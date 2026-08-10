#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

N10-W02 gRPC server launcher.

このサーバーでは、N10-W02 の制御 API を grpc_frame を介して公開する。
通信経路は以下の2種類に分かれる。

------------------------------------------------------------
1. 通常の API 呼び出し（unary RPC）

   従来から存在する API。

       client.capture_bmp_bytes()
           ↓
       grpc_frame Control/Call
           ↓
       N10W02Ctrl.capture_bmp_bytes()
           ↓
       bytes

   1回のメソッド呼び出しに対して1つの結果を返す。
   capture_bmp_bytes() を含む既存 API はすべてこの経路を使用する。
   今回の streaming 対応によって、この既存 API の動作は変更しない。

------------------------------------------------------------
2. 連続データ取得（server-streaming RPC）

   grpc_frame の Control/StreamCall を利用する追加経路。

       client.stream_bmp_bytes()
           ↓
       grpc_frame Control/StreamCall
           ↓
       _N10W02Stream.stream_bmp_bytes()
           ↓
       capture_bmp_bytes()
       capture_bmp_bytes()
       capture_bmp_bytes()
           ↓
       bytes
       bytes
       bytes
       ...

   1回の RPC 接続を維持したまま、複数の結果を順次クライアントへ返す。

------------------------------------------------------------
責務分離
------------------------------------------------------------

grpc_frame は、

    Call       : 1 request -> 1 response
    StreamCall : 1 request -> N responses

という gRPC の通信形態だけを提供する。
grpc_frame は画像、カメラ、BMP、fps、focus などを一切知らない。

一方、このファイルの _N10W02Stream は N10-W02 固有の処理として、
    ・どのメソッドを繰り返し呼ぶか
    ・画像をどの周期で取得するか
    ・focus をいつ実行するか
を決定する。

つまり、
    grpc_frame
        = ストリームを「運ぶ」責務
    _N10W02Stream
        = 画像ストリームを「生成する」責務

である。

------------------------------------------------------------
COM との関係
------------------------------------------------------------

N10W02Ctrl は COM を使用するため、COM オブジェクトへのアクセスは
ComExecutionRunner の専用スレッド上で実行する必要がある。
そのため N10W02Ctrl 自身に generator を持たせて、その generator を
gRPC worker thread から直接反復する構造にはしていない。

_N10W02Stream は ThreadSafeCtrlProxy を経由して、

    self._ctrl.capture_bmp_bytes()

を繰り返し呼ぶ。
各 capture_bmp_bytes() は従来どおり ComExecutionRunner を経由して
COM thread 上で実行される。

したがって streaming を追加しても、N10W02Ctrl の COM 実行モデルは変更しない。
クライアント側での利用

------------------------------------------------------------

サーバーは画像を取得して転送するところまでを担当する。
受信した画像に対する、

    ・OpenCV での表示
    ・画像加工
    ・物体認識
    ・対象物の中心座標計算
    ・ロボット等へのフィードバック

などはクライアント側の責務とする。
これにより、画像サーバーを特定の画像処理用途に依存させず、
連続画像データを汎用的に利用できる。

"""

from typing import Any, Optional
import time

import traceback

import grpc
from grpc import channel_ready_future

from n10w02.n10w02_ctrl import N10W02Ctrl
from grpc_frame.grpc_com import ComExecutionRunner, ThreadSafeCtrlProxy
from grpc_frame.grpc_server import create_grpc_server
from x_logger import XLogger


def _make_self_check_addr(
    grpc_host: str,
    grpc_port: int,
) -> str:
    """Create a local client address for server self-check."""
    host = str(grpc_host)

    if host == "0.0.0.0":
        host = "127.0.0.1"

    if host == "::":
        host = "[::1]"

    return "{0}:{1}".format(host, int(grpc_port))


def _make_large_message_options(
    max_message_mb: int,
):
    """Create gRPC options for BMP-sized unary messages."""
    max_message_bytes = int(max_message_mb) * 1024 * 1024

    return (
        ("grpc.max_receive_message_length", max_message_bytes),
        ("grpc.max_send_message_length", max_message_bytes),
    )



class _N10W02Stream:
    """
    N10-W02 固有の server-streaming 用データ生成クラス。

    grpc_frame の StreamCall は、streaming RPC を転送するための
    汎用通信機能だけを提供する。

    「何を連続して取得するか」「どの周期で取得するか」といった
    デバイス固有の処理を grpc_frame に持ち込まないため、
    N10-W02 固有の streaming 処理をこのクラスに分離している。

    また、N10W02Ctrl は COM オブジェクトを扱うため、
    N10W02Ctrl 自身から generator を返す構造にはしない。

    このクラスから ThreadSafeCtrlProxy を経由して通常の
    capture_bmp_bytes() を繰り返し呼ぶことで、各画像取得処理は
    従来どおり ComExecutionRunner の COM thread 上で実行される。
    """

    def __init__(self, ctrl_proxy: Any) -> None:
        # N10W02Ctrl を直接保持するのではなく ThreadSafeCtrlProxy を保持する。
        #
        # streaming のループ自体は gRPC worker 側で動作するが、
        # 実際の N10W02Ctrl メソッド呼び出しは proxy を経由するため、
        # COM オブジェクトへのアクセスは ComExecutionRunner の
        # 専用 COM thread 上で実行される。
        self._ctrl = ctrl_proxy

    def stream_bmp_bytes(
        self,
        fps: Optional[float] = None,
        focus: bool = False,
    ):
        """
        N10-W02 から BMP 画像を連続取得する。

        このメソッド自身は画像処理を行わない。
        capture_bmp_bytes() が返した BMP bytes をそのまま yield し、
        grpc_frame の StreamCall が各 yield を順次クライアントへ転送する。

        Parameters
        ----------
        fps : float, optional
            画像取得周期の上限。

            None の場合は待ち時間を設けず、
            capture_bmp_bytes() と通信が可能な速度で連続取得する。

            値を指定した場合は、1フレームの開始時刻を基準として
            指定 fps になるよう残り時間だけ sleep する。

        focus : bool
            True の場合でも focus を実行するのは最初の1フレームだけ。

            毎フレーム autofocus を実行すると画像取得周期に大きく
            影響するため、stream 開始時だけ focus=True とし、
            2フレーム目以降は focus=False で取得する。

        Yields
        ------
        bytes
            capture_bmp_bytes() で取得した1フレーム分の BMP データ。

            OpenCV への変換、物体認識、座標抽出などは行わない。
            それらは受信したクライアント側で実施する。
        """
        period = None
        if fps is not None:
            fps_value = float(fps)
            if fps_value <= 0.0:
                raise ValueError("fps must be > 0")
            period = 1.0 / fps_value

        first = True
        while True:
            # フレーム周期は「sleep時間」ではなく、
            # capture処理を含む1ループ全体の時間で調整する。
            started = time.monotonic()

            # ThreadSafeCtrlProxy 経由で呼ぶため、
            # 実際の capture_bmp_bytes() は COM runner 上で実行される。
            #
            # focus=True が指定されていても最初の1回だけ実行する。
            yield self._ctrl.capture_bmp_bytes(
                focus=bool(focus and first),
            )
            first = False

            if period is not None:
                # capture に既に使用した時間を差し引き、
                # 指定されたフレーム周期に合わせる。
                remain = period - (time.monotonic() - started)
                if remain > 0.0:
                    time.sleep(remain)

def n10w02_grpc_server(
    grpc_host: str,
    grpc_port: int,
    camera_ip: str,
    user: str = "admin",
    password: str = "password",
    timeout_ms: int = 5000,
    instance_name: str = "N10-W02",
    max_message_mb: int = 64,
    logger: Optional[Any] = None,
    log_level: Optional[str] = None,
) -> None:
    """Start N10-W02 gRPC server."""
    if logger is None:
        import logging

        log_level = log_level or "INFO"
        logging.basicConfig(level=log_level.upper())
        logger = logging.getLogger(__name__)

    bind_addr = "{0}:{1}".format(grpc_host, int(grpc_port))
    self_check_addr = _make_self_check_addr(
        grpc_host=grpc_host,
        grpc_port=grpc_port,
    )
    grpc_options = _make_large_message_options(max_message_mb=max_message_mb)

    server = None
    runner = None

    logger.info(
        f"[n10w02_grpc_server] startup: bind_addr={bind_addr}, "
        f"self_check_addr={self_check_addr}, camera_ip={camera_ip}, "
        f"timeout_ms={timeout_ms}, max_message_mb={max_message_mb}"
    )

    try:
        logger.info(
            "[n10w02_grpc_server] create COM runner start"
        )
        runner = ComExecutionRunner(
            ctrl_factory=lambda: N10W02Ctrl(
                camera_ip=camera_ip,
                user=user,
                password=password,
                timeout_ms=timeout_ms,
                instance_name=instance_name,
                logger=logger,
                init_com=False,
            ),
            logger=logger,
            log_level=log_level,
        )
        if not runner.wait_ready(timeout=20.0):
            startup_error = runner.get_startup_error()
            if startup_error:
                raise RuntimeError(startup_error)
            raise TimeoutError("ComExecutionRunner initialization timed out")

        # N10W02Ctrl への通常のメソッド呼び出しは、従来どおり
        # ThreadSafeCtrlProxy を通して ComExecutionRunner へ送る。
        #
        # この proxy は unary API と streaming API の双方から共有する。
        proxy = ThreadSafeCtrlProxy(
            runner=runner,
            ready_timeout=20.0,
        )

        # N10-W02 固有の streaming 処理。
        #
        # grpc_frame 自身には capture_bmp_bytes() の反復処理を持たせない。
        # 「画像を連続取得する」という機器固有の意味はこのオブジェクト側に置き、
        # grpc_frame は yield された結果を運ぶだけとする。
        stream_obj = _N10W02Stream(proxy)

        # ctrl_obj:
        #     従来の Control/Call 用。
        #     capture_bmp_bytes() を含む既存 API はすべてこちら。
        #
        # stream_obj:
        #     新しい Control/StreamCall 用。
        #     server-streaming として明示的に公開するメソッドだけを持つ。
        #
        # 通常APIとstreaming APIを分離することで、既存の Describe / Call
        # による透過型ディスパッチの挙動を変更しない。
        server = create_grpc_server(
            ctrl_obj=proxy,
            stream_obj=stream_obj,
            max_workers=10,
            logger=logger,
            log_level=log_level,
            grpc_options=grpc_options,
        )
        logger.info(
            "[n10w02_grpc_server] create gRPC server complete"
        )

        logger.info(
            f"[n10w02_grpc_server] add_insecure_port start: {bind_addr}"
        )
        ret = server.add_insecure_port(bind_addr)
        if ret == 0:
            raise RuntimeError("bind failed: {0}".format(bind_addr))
        logger.info(
            f"[n10w02_grpc_server] add_insecure_port complete: "
            f"bound_port={ret}"
        )

        logger.info("[n10w02_grpc_server] server.start start")
        server.start()
        logger.info(f"[n10w02_grpc_server] server.start complete: {bind_addr}")

        logger.info(
            f"[n10w02_grpc_server] self-check start: {self_check_addr}"
        )
        ch = grpc.insecure_channel(
            self_check_addr,
            options=grpc_options,
        )
        channel_ready_future(ch).result(timeout=2.0)
        logger.info(
            f"[n10w02_grpc_server] self-check complete: "
            f"{self_check_addr}"
        )

        logger.info(
            "[n10w02_grpc_server] wait_for_termination start"
        )
        server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except Exception as e:
        logger.error(
            f"[n10w02_grpc_server] startup/runtime failed: {e}\n"
            f"{traceback.format_exc()}"
        )
        raise

    finally:
        logger.info("[n10w02_grpc_server] shutdown start")
        if runner is not None:
            try:
                logger.info(
                    "[n10w02_grpc_server] disconnect RPC start"
                )
                runner.call(
                    "disconnect",
                    tuple(),
                    {},
                    timeout=5.0,
                )
                logger.info(
                    "[n10w02_grpc_server] disconnect RPC complete"
                )
            except Exception as e:
                logger.error(
                    f"[n10w02_grpc_server] disconnect RPC failed: {e}"
                )

        if server is not None:
            logger.info("[n10w02_grpc_server] server.stop start")
            server.stop(grace=None)
            logger.info("[n10w02_grpc_server] server.stop complete")

        if runner is not None:
            logger.info("[n10w02_grpc_server] runner.stop start")
            runner.stop()
            logger.info("[n10w02_grpc_server] runner.stop complete")

        logger.info("gRPC server stopped")


if __name__ == "__main__":
    CAMERA_IP = "10.170.10.42"
    GRPC_HOST = "0.0.0.0"
    GRPC_PORT = 50051
    LOG_LEVEL = "INFO"
    MAX_MESSAGE_MB = 64

    logger_ = XLogger(
        log_level=LOG_LEVEL,
        logger_name="N10W02GrpcServerCom",
    )

    n10w02_grpc_server(
        camera_ip=CAMERA_IP,
        grpc_host=GRPC_HOST,
        grpc_port=GRPC_PORT,
        max_message_mb=MAX_MESSAGE_MB,
        logger=logger_,
        log_level=LOG_LEVEL,
    )
