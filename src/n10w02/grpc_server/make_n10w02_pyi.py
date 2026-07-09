#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate n10w02_grpc_client.pyi.

Do not maintain n10w02_grpc_client.pyi by hand.
"""

import pathlib

import grpc_frame
from grpc_frame.make_pyi import generate_client_pyi


def main() -> None:
    """Generate n10w02_grpc_client.pyi."""
    base = pathlib.Path(__file__).resolve().parent
    grpc_base = pathlib.Path(grpc_frame.__file__).resolve().parent

    generate_client_pyi(
        client_py=base / "n10w02_grpc_client.py",
        client_class="N10W02GrpcClient",
        ctrl_py=base / "../n10w02_ctrl.py",
        ctrl_class="N10W02Ctrl",
        base_py=grpc_base / "grpc_client.py",
        base_class="GrpcClient",
        out_path=base / "n10w02_grpc_client.pyi",
        ctrl_async=True,
    )


if __name__ == "__main__":
    main()
