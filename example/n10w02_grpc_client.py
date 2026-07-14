#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC dynamic client.

The client is intentionally thin.  Remote methods are dynamically bound by
grpc_frame.  N10W02Ctrl is not reimplemented on the client side.
"""

from typing import Any, Optional
from n10w02.grpc_server import N10W02GrpcClient


if __name__ == "__main__":
    from x_logger import XLogger

    log_level_ = "INFO"
    logger_ = XLogger(
        log_level=log_level_,
        logger_name="N10W02GrpcClient",
    )

    client = N10W02GrpcClient(
        # server_ip="127.0.0.1",
        server_ip="10.170.10.38", # cobotta2/server2 (gRPC 1.54.3)
        # server_ip="10.170.10.41", # cobotta4/server3
        grpc_port=50051,
        logger=logger_,
        log_level=log_level_,
        max_message_mb=64,
    )

    logger_.info("status: {0}".format(client.get_status()))

    image = client.capture_bmp_bytes(focus=False)
    with open("n10w02_capture.bmp", "wb") as f:
        f.write(image)

    logger_.info("saved: n10w02_capture.bmp size={0}".format(len(image)))
