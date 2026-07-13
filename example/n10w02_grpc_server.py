#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC server launcher.

N10W02Ctrl is exposed directly through grpc_frame.  No EventBus, no streaming,
and no image-control reimplementation are used.

Image transfer is a normal unary RPC:
    client.capture_bmp_bytes() -> N10W02Ctrl.capture_bmp_bytes() -> bytes
"""

from typing import Any, Optional

from x_logger import XLogger
from n10w02.grpc_server import n10w02_grpc_server


if __name__ == "__main__":
    CAMERA_IP = "10.170.10.42" # cobotta2
    # CAMERA_IP = "10.170.10.43"  # cobotta3
    # GRPC_HOST = "127.0.0.1"
    GRPC_HOST = "10.170.10.38"  # server2
    # GRPC_HOST = "10.170.10.41"  # server3
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

    n10w02_grpc_server(
        camera_ip=CAMERA_IP,
        grpc_host=GRPC_HOST,
        grpc_port=GRPC_PORT,
        max_message_mb=MAX_MESSAGE_MB,
        logger=logger_,
        log_level=LOG_LEVEL,
    )
