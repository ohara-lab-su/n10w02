#!/usr/bin/env python
# coding: utf-8

from __future__ import annotations

import gc
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
        log_level: Optional[str] = None,
        init_com: bool = True,
    ) -> None:
        # XLogger が存在しない時に仕方がないのでデフォルトの logging を使う
        if logger is None:
            import logging

            log_level = log_level or "INFO"
            logging.basicConfig(level=log_level.upper())
            logger = logging.getLogger(__name__)

        self._logger = logger

        self._camera_ip = camera_ip
        self._user = user
        self._password = password
        self._timeout_ms = timeout_ms
        self._instance_name = instance_name

        self._init_com = bool(init_com)
        self._com_initialized = False

        self._cao_eng = None
        self._cao_ctrl = None
        self._var_image = None

        # 起動時の接続失敗は例外を送出し、サーバー起動を停止させる。
        self.connect()

    def connect(self) -> bool:
        connect_started = time.perf_counter()

        self._logger.info(
            f"[N10W02Ctrl.connect] start: camera_ip={self._camera_ip}, "
            f"timeout_ms={self._timeout_ms}, "
            f"instance_name={self._instance_name}, "
            f"init_com={self._init_com}"
        )

        if pythoncom is None:
            message = (
                "pythoncom が import できない。"
                "Windows + pywin32 + ORiN2 SDK 環境で実行する必要がある。"
            )
            self._logger.error(message)
            raise RuntimeError(message)

        if win32com is None:
            message = (
                "win32com.client が import できない。"
                "pywin32 を確認する必要がある。"
            )
            self._logger.error(message)
            raise RuntimeError(message)

        try:
            if self._init_com:
                self._logger.info("[N10W02Ctrl.connect] CoInitialize start")
                pythoncom.CoInitialize()
                self._com_initialized = True
                self._logger.info("[N10W02Ctrl.connect] CoInitialize complete")
            else:
                self._logger.info(
                    "[N10W02Ctrl.connect] CoInitialize skipped "
                    "(initialized by COM runner)"
                )

            self._logger.info(
                "[N10W02Ctrl.connect] Dispatch start: CAO.CaoEngine"
            )
            self._cao_eng = win32com.client.Dispatch("CAO.CaoEngine")
            self._logger.info(
                "[N10W02Ctrl.connect] Dispatch complete"
            )

            option = "Server={0},User={1},Password={2},Timeout={3}".format(
                self._camera_ip,
                self._user,
                self._password,
                self._timeout_ms,
            )

            self._logger.info(
                "[N10W02Ctrl.connect] AddController start: "
                f"instance_name={self._instance_name}, "
                f"provider={self.Provider}, "
                f"camera_ip={self._camera_ip}"
            )
            self._cao_ctrl = self._cao_eng.Workspaces(0).AddController(
                self._instance_name,
                self.Provider,
                "",
                option,
            )
            self._logger.info(
                "[N10W02Ctrl.connect] AddController complete"
            )

            self._logger.info(
                "[N10W02Ctrl.connect] AddVariable start: IMAGE"
            )
            self._var_image = self._cao_ctrl.AddVariable("IMAGE")
            self._logger.info(
                "[N10W02Ctrl.connect] AddVariable complete: IMAGE"
            )

            elapsed = time.perf_counter() - connect_started
            self._logger.info(
                f"[N10W02Ctrl.connect] complete: elapsed={elapsed:.3f}s"
            )
            return True

        except Exception as e:
            elapsed = time.perf_counter() - connect_started
            self._logger.exception(
                "[N10W02Ctrl.connect] failed: "
                f"camera_ip={self._camera_ip}, "
                f"elapsed={elapsed:.3f}s, error={e}"
            )
            self.disconnect()
            raise RuntimeError(f"N10-W02 接続に失敗した: {e}") from e

    def disconnect(self) -> bool:
        self._logger.info("[N10W02Ctrl.disconnect] start")
        result = True

        try:
            if self._cao_ctrl is not None:
                del self._cao_ctrl
        except Exception as e:
            result = False
            self._logger.exception(
                f"[N10W02Ctrl.disconnect] controller release failed: {e}"
            )

        try:
            if self._cao_eng is not None:
                del self._cao_eng
        except Exception as e:
            result = False
            self._logger.exception(
                f"[N10W02Ctrl.disconnect] engine release failed: {e}"
            )

        self._cao_ctrl = None
        self._cao_eng = None
        self._var_image = None

        if self._com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception as e:
                result = False
                self._logger.exception(
                    f"[N10W02Ctrl.disconnect] CoUninitialize failed: {e}"
                )
            self._com_initialized = False

        try:
            gc.collect()
        except Exception as e:
            result = False
            self._logger.exception(
                f"[N10W02Ctrl.disconnect] gc.collect failed: {e}"
            )

        if result:
            self._logger.info("[N10W02Ctrl.disconnect] complete")
        else:
            self._logger.error(
                "[N10W02Ctrl.disconnect] completed with errors"
            )

        return result

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
            raise RuntimeError(
                "IMAGE の戻り値を bytes に変換できない: {0}".format(e)
            ) from e

    def one_shot_focus(self, timeout_ms: int = 5000) -> bool:
        self._logger.info(
            f"[N10W02Ctrl.one_shot_focus] timeout_ms={timeout_ms}"
        )

        try:
            if self._cao_ctrl is None:
                raise RuntimeError("N10-W02 が未接続である。")

            self._cao_ctrl.Execute("OneShotFocus", timeout_ms)
            return True
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.one_shot_focus] failed: {e}"
            )
            return False

    def one_shot_white_balance(self, timeout_ms: int = 5000) -> bool:
        self._logger.info(
            "[N10W02Ctrl.one_shot_white_balance] "
            f"timeout_ms={timeout_ms}"
        )

        try:
            if self._cao_ctrl is None:
                raise RuntimeError("N10-W02 が未接続である。")

            self._cao_ctrl.Execute("OneShotWhiteBalance", timeout_ms)
            return True
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.one_shot_white_balance] failed: {e}"
            )
            return False

    def save_white_balance(self) -> bool:
        self._logger.info("[N10W02Ctrl.save_white_balance]")

        try:
            if self._cao_ctrl is None:
                raise RuntimeError("N10-W02 が未接続である。")

            self._cao_ctrl.Execute("SaveWhiteBalance")
            return True
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.save_white_balance] failed: {e}"
            )
            return False

    def get_variable(self, name: str) -> Any:
        self._logger.info(
            f"[N10W02Ctrl.get_variable] name={name}"
        )

        try:
            if self._cao_ctrl is None:
                raise RuntimeError("N10-W02 が未接続である。")

            var = self._cao_ctrl.AddVariable(name)
            return var.Value
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.get_variable] failed: name={name}, error={e}"
            )
            return False

    def set_variable(self, name: str, value: Any) -> bool:
        self._logger.info(
            f"[N10W02Ctrl.set_variable] name={name}, value={value}"
        )

        try:
            if self._cao_ctrl is None:
                raise RuntimeError("N10-W02 が未接続である。")

            var = self._cao_ctrl.AddVariable(name)
            var.Value = value
            return True
        except Exception as e:
            self._logger.exception(
                "[N10W02Ctrl.set_variable] failed: "
                f"name={name}, value={value}, error={e}"
            )
            return False

    def capture_bmp_bytes(self, focus: bool = False) -> Union[bytes, bool]:
        self._logger.info(
            f"[N10W02Ctrl.capture_bmp_bytes] focus={focus}"
        )

        try:
            if self._var_image is None:
                raise RuntimeError("IMAGE 変数が未初期化である。")

            if focus:
                focus_result = self.one_shot_focus()
                if focus_result is False:
                    return False

            value = self._var_image.Value
            data = self._variant_to_bytes(value)
            self._logger.info(
                f"[N10W02Ctrl.capture_bmp_bytes] size={len(data)} bytes"
            )
            return data
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.capture_bmp_bytes] failed: {e}"
            )
            return False

    def save_bmp(
        self,
        output_path: Union[str, Path],
        focus: bool = False,
    ) -> Union[Path, bool]:
        path = Path(output_path)
        self._logger.info(
            f"[N10W02Ctrl.save_bmp] path={path}, focus={focus}"
        )

        try:
            data = self.capture_bmp_bytes(focus=focus)
            if data is False:
                return False

            with open(str(path), "wb") as f:
                f.write(data)

            return path
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.save_bmp] failed: path={path}, error={e}"
            )
            return False

    def capture_opencv(self, focus: bool = False) -> Any:
        """
        OpenCV の画像配列として取得する。
        cv2 と numpy が必要である。
        """
        self._logger.info(
            f"[N10W02Ctrl.capture_opencv] focus={focus}"
        )

        try:
            import cv2
            import numpy as np

            data = self.capture_bmp_bytes(focus=focus)
            if data is False:
                return False

            buf = np.frombuffer(data, dtype=np.uint8)
            image = cv2.imdecode(buf, cv2.IMREAD_COLOR)

            if image is None:
                raise RuntimeError(
                    "OpenCV で画像を decode できない。"
                    "保存された BMP を確認する必要がある。"
                )

            return image
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.capture_opencv] failed: {e}"
            )
            return False

    def save_png_by_opencv(
        self,
        output_path: Union[str, Path],
        focus: bool = False,
    ) -> Union[Path, bool]:
        path = Path(output_path)
        self._logger.info(
            "[N10W02Ctrl.save_png_by_opencv] "
            f"path={path}, focus={focus}"
        )

        try:
            import cv2

            image = self.capture_opencv(focus=focus)
            if image is False:
                return False

            ok = cv2.imwrite(str(path), image)
            if not ok:
                raise RuntimeError(
                    "OpenCV による画像保存に失敗した: {0}".format(path)
                )

            return path
        except Exception as e:
            self._logger.exception(
                "[N10W02Ctrl.save_png_by_opencv] failed: "
                f"path={path}, error={e}"
            )
            return False

    def get_status(self) -> Union[Dict[str, Any], bool]:
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

        self._logger.info("[N10W02Ctrl.get_status]")

        try:
            result = {}
            for name in names:
                result[name] = self.get_variable(name)

            return result
        except Exception as e:
            self._logger.exception(
                f"[N10W02Ctrl.get_status] failed: {e}"
            )
            return False


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
