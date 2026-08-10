#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC server launcher.

このファイルは N10-W02 gRPC サーバーの起動用スクリプトである。
実際の制御・gRPC 公開処理は n10w02.grpc_server.n10w02_grpc_server が担当する。

現在のサーバーは、grpc_frame の2種類の汎用ディスパッチを利用する。

1. 通常の Call（unary RPC）

    client.capture_bmp_bytes()
        -> Control/Call
        -> N10W02Ctrl.capture_bmp_bytes()
        -> 1枚の BMP bytes

   従来の N10-W02 API はこの経路を使用する。

2. StreamCall（server-streaming RPC）

    client.stream_bmp_bytes()
        -> Control/StreamCall
        -> N10-W02 側の stream_bmp_bytes()
        -> BMP bytes
        -> BMP bytes
        -> ...

   1本の RPC 接続を維持したまま、画像を連続してクライアントへ送る。

画像の表示、OpenCV による処理、物体検出、座標抽出などは
サーバーでは行わず、受信したクライアント側の責務とする。

既存の Call API はそのまま維持されており、streaming 対応によって
従来のクライアント API の呼び方は変更されない。
"""

from x_logger import XLogger
from n10w02.grpc_server.n10w02_grpc_server import n10w02_grpc_server


if __name__ == "__main__":
    # CAMERA_IP = "10.170.10.42"  # cobotta2
    CAMERA_IP = "10.170.10.52"  # cobotta3
    # CAMERA_IP = "10.170.10.43"  # cobotta4

    # GRPC_HOST = "127.0.0.1"
    # GRPC_HOST = "10.170.10.38"  # cobotta2/server2
    GRPC_HOST = "10.170.10.55"  # cobotta3/server4
    # GRPC_HOST = "10.170.10.41"  # cobotta4/server3
    # GRPC_HOST = "10.170.10.60"  # cobotta4/server5

    GRPC_PORT = 50051
    LOG_LEVEL = "INFO"
    MAX_MESSAGE_MB = 64

    logger_ = XLogger(
        log_level=LOG_LEVEL,
        logger_name="N10W02GrpcServerCom",
    )

    logger_.info(
        f"[launcher] start: camera_ip={CAMERA_IP}, "
        f"grpc_host={GRPC_HOST}, grpc_port={GRPC_PORT}, "
        f"max_message_mb={MAX_MESSAGE_MB}"
    )

    # n10w02_grpc_server() 内部で、
    #   ctrl_obj   : 通常の Call 用
    #   stream_obj : StreamCall 用
    # が grpc_frame に登録される。
    #
    # この launcher 側では、unary / streaming を個別に起動する必要はない。
    n10w02_grpc_server(
        camera_ip=CAMERA_IP,
        grpc_host=GRPC_HOST,
        grpc_port=GRPC_PORT,
        max_message_mb=MAX_MESSAGE_MB,
        logger=logger_,
        log_level=LOG_LEVEL,
    )
