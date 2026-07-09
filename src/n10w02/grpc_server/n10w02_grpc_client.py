#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC dynamic client.

This client is intentionally thin.

The client side:
- does not know N10W02Ctrl implementation details
- does not import stub / pb2 directly
- uses only grpc_frame.GrpcClient public I/F
- receives remote methods dynamically through Describe RPC

Remote methods such as capture_bmp_bytes(), save_bmp(), one_shot_focus(),
get_status(), connect(), and disconnect() are provided by N10W02Ctrl on the
server side.
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
    ) -> None:
        super().__init__(
            server_ip=server_ip,
            server_port=grpc_port,
            logger=logger,
            log_level=log_level,
            timeout_sec=timeout_sec,
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
    )

    logger_.info("status: {0}".format(client.get_status()))

    image = client.capture_bmp_bytes(focus=False)
    with open("n10w02_capture.bmp", "wb") as f:
        f.write(image)

    logger_.info("saved: n10w02_capture.bmp size={0}".format(len(image)))
