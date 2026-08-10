#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC client example (unary RPC).

従来どおり、1回の API 呼び出しで画像を1枚取得する例である。
streaming 対応後も既存の capture_bmp_bytes() API は変更されていない。

連続画像を利用する場合は n10w02_client_stream.py を使用する。
"""

from n10w02.grpc_server.n10w02_grpc_client import N10W02GrpcClient


if __name__ == "__main__":
    from x_logger import XLogger

    log_level_ = "INFO"
    logger_ = XLogger(
        log_level=log_level_,
        logger_name="N10W02GrpcClient",
    )

    client = N10W02GrpcClient(
        # server_ip="127.0.0.1",
        # server_ip="10.170.10.38",  # cobotta2/server2
        # server_ip="10.170.10.55",  # cobotta3/server4
        # server_ip="10.170.10.41",  # cobotta4/server3
        server_ip="10.170.10.60",  # cobotta4/server5
        grpc_port=50051,
        logger=logger_,
        log_level=log_level_,
        max_message_mb=64,
    )

    logger_.info("status: {0}".format(client.get_status()))

    # 従来の unary API。
    # 1回の Call に対して BMP 画像1枚分の bytes が返る。
    image = client.capture_bmp_bytes(focus=False)

    with open("n10w02_capture.bmp", "wb") as f:
        f.write(image)

    logger_.info(
        "saved: n10w02_capture.bmp size={0}".format(len(image))
    )
