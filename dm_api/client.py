"""High-level Python client for DM API."""

import ctypes
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .constants import (
    ACTIVATION_ERROR_NAMES,
    DEV_LICENSE_ERROR,
    ENV_DM_APP_ID,
    ENV_DM_LAUNCHER_ENDPOINT,
    ENV_DM_LAUNCHER_TOKEN,
    ENV_DM_PUBLIC_KEY,
)
from .ffi import DmApiFFI

JsonDict = Dict[str, Any]


class DmApi:
    def __init__(
        self,
        public_key: Optional[str] = None,
        app_id: Optional[str] = None,
        dll_path: Optional[str] = None,
    ) -> None:
        self.app_id = app_id or os.environ.get(ENV_DM_APP_ID)
        self.public_key = public_key or os.environ.get(ENV_DM_PUBLIC_KEY)
        self._ffi = DmApiFFI(dll_path=dll_path)
        self._license_callback_ref: Optional[Any] = None

    @staticmethod
    def should_skip_check(
        app_id: Optional[str] = None,
        public_key: Optional[str] = None,
    ) -> bool:
        if os.environ.get(ENV_DM_LAUNCHER_ENDPOINT) and os.environ.get(ENV_DM_LAUNCHER_TOKEN):
            return False

        resolved_app_id = app_id or os.environ.get(ENV_DM_APP_ID)
        resolved_public_key = public_key or os.environ.get(ENV_DM_PUBLIC_KEY)
        if not resolved_app_id or not resolved_public_key:
            raise RuntimeError(
                "App identity is required for dev-license checks. "
                "Provide app_id/public_key or set DM_APP_ID and DM_PUBLIC_KEY."
            )

        pubkey_path = (
            Path.home() / ".distromate-cli" / "dev_licenses" / str(resolved_app_id) / "pubkey"
        )
        try:
            dev_pub_key = pubkey_path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            raise RuntimeError(DEV_LICENSE_ERROR) from exc

        if not dev_pub_key or dev_pub_key != str(resolved_public_key).strip():
            raise RuntimeError(DEV_LICENSE_ERROR)

        return True

    def get_last_error(self) -> Optional[str]:
        return self._ffi.ptr_to_string(self._ffi.lib.DM_GetLastError())

    def get_activation_error_name(self, code: Optional[int]) -> Optional[str]:
        if code is None:
            return None
        return ACTIVATION_ERROR_NAMES.get(code, f"UNKNOWN({code})")

    def _call_bool(self, func: Any, *args: Any) -> bool:
        return func(*args) == 0

    def _call_u32(self, func: Any) -> Optional[int]:
        value = ctypes.c_uint32(0)
        if func(ctypes.byref(value)) != 0:
            return None
        return int(value.value)

    def _call_out_string(self, func: Any, size: int = 512) -> Optional[str]:
        safe_size = max(8, int(size))
        buf = ctypes.create_string_buffer(safe_size)
        if func(buf, safe_size) != 0:
            return None
        return buf.value.decode("utf-8")

    def _call_json(self, func: Any, *args: Any) -> Optional[JsonDict]:
        return self._ffi.ptr_to_json(func(*args))

    @staticmethod
    def _encode_options(options: Optional[JsonDict]) -> Optional[bytes]:
        if options is None:
            return None
        return json.dumps(options, separators=(",", ":")).encode("utf-8")

    def set_product_data(self, product_data: str) -> bool:
        return self._call_bool(self._ffi.lib.SetProductData, product_data.encode("utf-8"))

    def set_product_id(self, product_id: str) -> bool:
        return self._call_bool(self._ffi.lib.SetProductId, product_id.encode("utf-8"))

    def set_data_directory(self, directory_path: str) -> bool:
        return self._call_bool(self._ffi.lib.SetDataDirectory, directory_path.encode("utf-8"))

    def set_debug_mode(self, enable: bool) -> bool:
        return self._call_bool(self._ffi.lib.SetDebugMode, 1 if enable else 0)

    def set_custom_device_fingerprint(self, fingerprint: str) -> bool:
        return self._call_bool(
            self._ffi.lib.SetCustomDeviceFingerprint,
            fingerprint.encode("utf-8"),
        )

    def set_license_key(self, license_key: str) -> bool:
        return self._call_bool(self._ffi.lib.SetLicenseKey, license_key.encode("utf-8"))

    def set_license_callback(self, callback: Callable[[], None]) -> bool:
        if not callable(callback):
            raise TypeError("callback must be callable")

        c_callback = DmApiFFI.LICENSE_CALLBACK_TYPE(callback)
        if self._ffi.lib.SetLicenseCallback(c_callback) != 0:
            return False

        self._license_callback_ref = c_callback
        return True

    def activate_license(self) -> bool:
        return self._call_bool(self._ffi.lib.ActivateLicense)

    def get_last_activation_error(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetLastActivationError)

    def is_license_genuine(self) -> bool:
        return self._call_bool(self._ffi.lib.IsLicenseGenuine)

    def is_license_valid(self) -> bool:
        return self._call_bool(self._ffi.lib.IsLicenseValid)

    def get_server_sync_grace_period_expiry_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetServerSyncGracePeriodExpiryDate)

    def get_activation_mode(self, buffer_size: int = 64) -> Optional[Dict[str, str]]:
        safe_size = max(8, int(buffer_size))
        initial = ctypes.create_string_buffer(safe_size)
        current = ctypes.create_string_buffer(safe_size)
        code = self._ffi.lib.GetActivationMode(initial, safe_size, current, safe_size)
        if code != 0:
            return None
        return {
            "initial_mode": initial.value.decode("utf-8"),
            "current_mode": current.value.decode("utf-8"),
        }

    def get_license_key(self, buffer_size: int = 256) -> Optional[str]:
        return self._call_out_string(self._ffi.lib.GetLicenseKey, size=buffer_size)

    def get_license_expiry_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetLicenseExpiryDate)

    def get_license_creation_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetLicenseCreationDate)

    def get_license_activation_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetLicenseActivationDate)

    def get_activation_creation_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetActivationCreationDate)

    def get_activation_last_synced_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetActivationLastSyncedDate)

    def get_activation_id(self, buffer_size: int = 256) -> Optional[str]:
        return self._call_out_string(self._ffi.lib.GetActivationId, size=buffer_size)

    def reset(self) -> bool:
        return self._call_bool(self._ffi.lib.Reset)

    def check_for_updates(self, options: Optional[JsonDict] = None) -> Optional[JsonDict]:
        return self._call_json(self._ffi.lib.DM_CheckForUpdates, self._encode_options(options))

    def download_update(self, options: Optional[JsonDict] = None) -> Optional[JsonDict]:
        return self._call_json(self._ffi.lib.DM_DownloadUpdate, self._encode_options(options))

    def cancel_update_download(self, options: Optional[JsonDict] = None) -> Optional[JsonDict]:
        return self._call_json(
            self._ffi.lib.DM_CancelUpdateDownload,
            self._encode_options(options),
        )

    def get_update_state(self) -> Optional[JsonDict]:
        return self._call_json(self._ffi.lib.DM_GetUpdateState)

    def get_post_update_info(self) -> Optional[JsonDict]:
        return self._call_json(self._ffi.lib.DM_GetPostUpdateInfo)

    def ack_post_update_info(self, options: Optional[JsonDict] = None) -> Optional[JsonDict]:
        return self._call_json(self._ffi.lib.DM_AckPostUpdateInfo, self._encode_options(options))

    def wait_for_update_state_change(
        self,
        last_sequence: int,
        timeout_ms: int = 30000,
    ) -> Optional[JsonDict]:
        sequence = max(0, int(last_sequence))
        timeout = max(0, int(timeout_ms))
        return self._call_json(self._ffi.lib.DM_WaitForUpdateStateChange, sequence, timeout)

    def quit_and_install(self, options: Optional[JsonDict] = None) -> int:
        return int(self._ffi.lib.DM_QuitAndInstall(self._encode_options(options)))

    def get_library_version(self) -> str:
        raw = self._ffi.lib.GetLibraryVersion()
        return raw.decode("utf-8") if raw else ""

    def json_to_canonical(self, json_str: str) -> Optional[str]:
        return self._ffi.json_to_canonical(json_str)
