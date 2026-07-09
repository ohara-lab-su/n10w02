#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC dynamic client.

The client is intentionally thin.  Remote methods are dynamically bound by
grpc_frame.  N10W02Ctrl is not reimplemented on the client side.
"""

from typing import Any, Optional

from grpc_frame import GrpcClient


class N10W02GrpcClient(GrpcClient):
    """N10-W02 gRPC dynamic client."""

    def __init__(
        self,
        server_ip: str,
        grpc_port: int,
        logger: Optional[Any] = None,
        log_level: Optional[str] = None,
        timeout_sec: Optional[float] = None,
        max_message_mb: int = 64,
    ) -> None:
        max_message_bytes = int(max_message_mb) * 1024 * 1024
        grpc_options = (
            ("grpc.max_receive_message_length", max_message_bytes),
            ("grpc.max_send_message_length", max_message_bytes),
        )

        super().__init__(
            server_ip=server_ip,
            server_port=grpc_port,
            logger=logger,
            log_level=log_level,
            timeout_sec=timeout_sec,
            grpc_options=grpc_options,
        )


if __name__ == "__main__":
    from x_logger import XLogger

    log_level_ = "INFO"
    logger_ = XLogger(
        log_level=log_level_,
        logger_name="N10W02GrpcClient",
    )

    client = N10W02GrpcClient(
        server_ip="127.0.0.1",
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
