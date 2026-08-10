#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC server launcher.

N10W02Ctrl is exposed through grpc_frame for the existing unary API.
Image streaming is provided separately by _N10W02Stream and uses the generic
Control/StreamCall transport.

Existing image transfer remains unchanged:
    client.capture_bmp_bytes() -> N10W02Ctrl.capture_bmp_bytes() -> bytes

Additional stream API:
    client.stream_bmp_bytes() -> repeated capture_bmp_bytes() -> stream of bytes
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
    """N10-W02 固有の画像ストリーム生成部。通信方式は grpc_frame に委譲する。"""

    def __init__(self, ctrl_proxy: Any) -> None:
        self._ctrl = ctrl_proxy

    def stream_bmp_bytes(
        self,
        fps: Optional[float] = None,
        focus: bool = False,
    ):
        """BMP 画像を連続取得して yield する。画像処理は行わない。"""
        period = None
        if fps is not None:
            fps_value = float(fps)
            if fps_value <= 0.0:
                raise ValueError("fps must be > 0")
            period = 1.0 / fps_value

        first = True
        while True:
            started = time.monotonic()
            yield self._ctrl.capture_bmp_bytes(
                focus=bool(focus and first),
            )
            first = False

            if period is not None:
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

        proxy = ThreadSafeCtrlProxy(
            runner=runner,
            ready_timeout=20.0,
        )
        stream_obj = _N10W02Stream(proxy)

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
