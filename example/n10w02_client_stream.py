#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N10-W02 gRPC client example (server-streaming RPC).

N10W02GrpcClient.stream_bmp_bytes() を使用して、
サーバーから連続して送られる BMP フレームを受信・表示する。

サーバー側は画像を取得して転送するところまでを担当する。
OpenCV での decode、表示、画像処理、物体検出、座標抽出などは
このクライアント側で自由に実装する。

ESC または q キーで終了する。
"""

import cv2
import numpy as np

from n10w02.grpc_client import N10W02GrpcClient


if __name__ == "__main__":
    from x_logger import XLogger

    log_level_ = "INFO"
    logger_ = XLogger(
        log_level=log_level_,
        logger_name="N10W02GrpcStreamClient",
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
    logger_.info("start image stream")

    try:
        # fps=None なら、カメラ取得と通信が可能な速度で連続取得する。
        # 必要なら fps=10.0 などを指定して取得周期の上限を設定できる。
        # focus=True の場合、サーバー側では最初のフレームだけ focus を行う。
        for bmp_bytes in client.stream_bmp_bytes(
            fps=None,
            focus=False,
        ):
            # gRPC から受信した BMP bytes を OpenCV の画像へ decode する。
            encoded = np.frombuffer(bmp_bytes, dtype=np.uint8)
            image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

            if image is None:
                logger_.warning("failed to decode BMP frame")
                continue

            # ------------------------------------------------------------
            # 画像処理はここに記述する。
            #
            # 例:
            #   - 物体検出
            #   - 対象物の中心座標計算
            #   - センタリング量の算出
            #   - ロボット制御へのフィードバック
            #   - 画像保存
            #
            # サーバー側はこれらの処理には関与しない。
            # ------------------------------------------------------------

            cv2.imshow("N10-W02 stream", image)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

    finally:
        cv2.destroyAllWindows()
        logger_.info("image stream stopped")
