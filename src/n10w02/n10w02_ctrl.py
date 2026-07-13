#!/usr/bin/env python
# coding: utf-8

from __future__ import annotations

import gc
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import pythoncom
    import win32com.client
except Exception:
    pythoncom = None
    win32com = None


class N10W02Ctrl:
    """
    Canon N10-W02 を ORiN2 / CAO 経由で制御する独立クラスである。

    画像取得は N10-W02 プロバイダの IMAGE 変数から行う。
    取得されるデータは BMP バイナリとして保存できる。
    """

    Provider = "CaoProv.Canon.N10-W02"

    def __init__(
        self,
        camera_ip: str = "10.170.10.42",  # cobotta2
        user: str = "admin",
        password: str = "password",  # デフォルトパスワード
        timeout_ms: int = 5000,
        instance_name: str = "N10-W02",
        logger: Optional[Any] = None,
        init_com: bool = True,
    ) -> None:
        self._camera_ip = camera_ip
        self._user = user
        self._password = password
        self._timeout_ms = timeout_ms
        self._instance_name = instance_name
        self._logger = logger

        self._init_com = bool(init_com)
        self._com_initialized = False

        self._cao_eng = None
        self._cao_ctrl = None
        self._var_image = None

        self.connect()

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)

    def _log_error(self, message: str) -> None:
        if self._logger is not None:
            self._logger.error(message)
        else:
            print(message, file=sys.stderr)

    def connect(self) -> bool:
        connect_started = time.perf_counter()
        self._log_info(
            f"[N10W02Ctrl.connect] start: camera_ip={self._camera_ip}, "
            f"timeout_ms={self._timeout_ms}, "
            f"instance_name={self._instance_name}, "
            f"init_com={self._init_com}"
        )

        if pythoncom is None:
            raise RuntimeError("pythoncom が import できない。Windows + pywin32 + ORiN2 SDK 環境で実行する必要がある。")

        if win32com is None:
            raise RuntimeError("win32com.client が import できない。pywin32 を確認する必要がある。")

        try:
            if self._init_com:
                self._log_info("[N10W02Ctrl.connect] CoInitialize start")
                pythoncom.CoInitialize()
                self._com_initialized = True
                self._log_info("[N10W02Ctrl.connect] CoInitialize complete")
            else:
                self._log_info(
                    "[N10W02Ctrl.connect] CoInitialize skipped "
                    "(initialized by COM runner)"
                )

            step_started = time.perf_counter()
            self._log_info(
                "[N10W02Ctrl.connect] Dispatch start: CAO.CaoEngine"
            )
            self._cao_eng = win32com.client.Dispatch("CAO.CaoEngine")
            self._log_info(
                f"[N10W02Ctrl.connect] Dispatch complete: "
                f"elapsed={time.perf_counter() - step_started:.3f}s"
            )

            option = (
                "Server={0},User={1},Password={2},Timeout={3}".format(
                    self._camera_ip,
                    self._user,
                    self._password,
                    self._timeout_ms,
                )
            )

            step_started = time.perf_counter()
            self._log_info(
                f"[N10W02Ctrl.connect] AddController start: "
                f"instance_name={self._instance_name}, "
                f"provider={self.Provider}, camera_ip={self._camera_ip}"
            )
            self._cao_ctrl = self._cao_eng.Workspaces(0).AddController(
                self._instance_name,
                self.Provider,
                "",
                option,
            )
            self._log_info(
                f"[N10W02Ctrl.connect] AddController complete: "
                f"elapsed={time.perf_counter() - step_started:.3f}s"
            )

            step_started = time.perf_counter()
            self._log_info(
                "[N10W02Ctrl.connect] AddVariable start: IMAGE"
            )
            self._var_image = self._cao_ctrl.AddVariable("IMAGE")
            self._log_info(
                f"[N10W02Ctrl.connect] AddVariable complete: "
                f"elapsed={time.perf_counter() - step_started:.3f}s"
            )

            self._log_info(
                f"[N10W02Ctrl.connect] complete: "
                f"camera_ip={self._camera_ip}, "
                f"total_elapsed={time.perf_counter() - connect_started:.3f}s"
            )
            return True

        except Exception as e:
            self._log_error(
                f"[N10W02Ctrl.connect] failed: "
                f"camera_ip={self._camera_ip}, "
                f"elapsed={time.perf_counter() - connect_started:.3f}s, "
                f"error={e}"
            )
            self.disconnect()
            raise RuntimeError(f"N10-W02 接続に失敗した: {e}")

    def disconnect(self) -> bool:
        try:
            if self._cao_ctrl is not None:
                del self._cao_ctrl
            if self._cao_eng is not None:
                del self._cao_eng
        except Exception:
            pass

        self._cao_ctrl = None
        self._cao_eng = None
        self._var_image = None

        if self._com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            self._com_initialized = False

        gc.collect()
        return True

    def __del__(self) -> None:
        try:
            self.disconnect()
        except Exception:
            pass

    @staticmethod
    def _variant_to_bytes(value: Any) -> bytes:
        if isinstance(value, bytes):
            return value

        if isinstance(value, bytearray):
            return bytes(value)

        if isinstance(value, memoryview):
            return value.tobytes()

        try:
            return bytes(value)
        except Exception as e:
            raise RuntimeError("IMAGE の戻り値を bytes に変換できない: {0}".format(e))

    def one_shot_focus(self, timeout_ms: int = 5000) -> bool:
        if self._cao_ctrl is None:
            raise RuntimeError("N10-W02 が未接続である。")

        self._cao_ctrl.Execute("OneShotFocus", timeout_ms)
        return True

    def one_shot_white_balance(self, timeout_ms: int = 5000) -> bool:
        if self._cao_ctrl is None:
            raise RuntimeError("N10-W02 が未接続である。")

        self._cao_ctrl.Execute("OneShotWhiteBalance", timeout_ms)
        return True

    def save_white_balance(self) -> bool:
        if self._cao_ctrl is None:
            raise RuntimeError("N10-W02 が未接続である。")

        self._cao_ctrl.Execute("SaveWhiteBalance")
        return True

    def get_variable(self, name: str) -> Any:
        if self._cao_ctrl is None:
            raise RuntimeError("N10-W02 が未接続である。")

        var = self._cao_ctrl.AddVariable(name)
        return var.Value

    def set_variable(self, name: str, value: Any) -> bool:
        if self._cao_ctrl is None:
            raise RuntimeError("N10-W02 が未接続である。")

        var = self._cao_ctrl.AddVariable(name)
        var.Value = value
        return True

    def capture_bmp_bytes(self, focus: bool = False) -> bytes:
        if self._var_image is None:
            raise RuntimeError("IMAGE 変数が未初期化である。")

        if focus:
            self.one_shot_focus()

        value = self._var_image.Value
        return self._variant_to_bytes(value)

    def save_bmp(
        self,
        output_path: Union[str, Path],
        focus: bool = False,
    ) -> Path:
        path = Path(output_path)
        data = self.capture_bmp_bytes(focus=focus)

        with open(str(path), "wb") as f:
            f.write(data)

        return path

    def capture_opencv(self, focus: bool = False) -> Any:
        """
        OpenCV の画像配列として取得する。
        cv2 と numpy が必要である。
        """
        import cv2
        import numpy as np

        data = self.capture_bmp_bytes(focus=focus)
        buf = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError("OpenCV で画像を decode できない。保存された BMP を確認する必要がある。")

        return image

    def save_png_by_opencv(
        self,
        output_path: Union[str, Path],
        focus: bool = False,
    ) -> Path:
        import cv2

        path = Path(output_path)
        image = self.capture_opencv(focus=focus)

        ok = cv2.imwrite(str(path), image)
        if not ok:
            raise RuntimeError("OpenCV による画像保存に失敗した: {0}".format(path))

        return path

    def get_status(self) -> Dict[str, Any]:
        names = [
            "@ORIGIN",
            "@HARDWARE",
            "@FIRMWARE",
            "@COUNT",
            "@TIMEOUT",
            "STATUS",
            "TYPE",
            "CAMERA_ID",
            "TIMESTAMP",
        ]

        result = {}
        for name in names:
            try:
                result[name] = self.get_variable(name)
            except Exception as e:
                result[name] = "ERROR: {0}".format(e)

        return result


if __name__ == "__main__":
    cam = N10W02Ctrl(
        camera_ip="10.170.10.42",
        user="admin",
        password="password",
    )

    try:
        print(cam.get_status())

        cam.save_bmp("n10w02_capture.bmp", focus=True)
        cam.save_png_by_opencv("n10w02_capture.png", focus=False)

    finally:
        cam.disconnect()