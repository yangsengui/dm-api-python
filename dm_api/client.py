"""High-level Python client for DM API."""

import json
import os
import ctypes
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import (
    DEFAULT_TIMEOUT_MS,
    DEV_LICENSE_ERROR,
    ENV_DM_API_PATH,
    ENV_DM_APP_ID,
    ENV_DM_PIPE,
    ENV_DM_PUBLIC_KEY,
)
from .ffi import DmApiFFI


class DmApi:
    def __init__(
        self,
        public_key: Optional[str] = None,
        app_id: Optional[str] = None,
        dll_path: Optional[str] = None,
        pipe_timeout: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        self.app_id = app_id or os.environ.get(ENV_DM_APP_ID)
        self.public_key = public_key or os.environ.get(ENV_DM_PUBLIC_KEY)
        self.pipe_timeout = max(0, int(pipe_timeout))

        self._ffi = DmApiFFI(dll_path=dll_path)

    @staticmethod
    def should_skip_check(
        app_id: Optional[str] = None,
        public_key: Optional[str] = None,
    ) -> bool:
        if os.environ.get(ENV_DM_PIPE) and os.environ.get(ENV_DM_API_PATH):
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
        except Exception:
            raise RuntimeError(DEV_LICENSE_ERROR)

        if not dev_pub_key or dev_pub_key != str(resolved_public_key).strip():
            raise RuntimeError(DEV_LICENSE_ERROR)

        return True

    def get_version(self) -> str:
        raw = self._ffi.lib.DM_GetVersion()
        return raw.decode("utf-8") if raw else ""

    def get_last_error(self) -> Optional[str]:
        return self._ffi.ptr_to_string(self._ffi.lib.DM_GetLastError())

    def _call_bool(self, func: Any, *args: Any) -> bool:
        return func(*args) == 0

    def _resolve_pipe(self) -> Optional[str]:
        return os.environ.get(ENV_DM_PIPE)

    def _call_pipe_json(self, func: Any, *args: Any) -> Optional[Dict[str, Any]]:
        pipe = self._resolve_pipe()
        if not pipe:
            return None
        if self._ffi.lib.DM_Connect(pipe.encode("utf-8"), self.pipe_timeout) != 0:
            return None
        try:
            resp = self._ffi.ptr_to_json(func(*args))
            return resp.get("data") if isinstance(resp, dict) else None
        finally:
            self._ffi.lib.DM_Close()

    def _call_pipe_bool(self, func: Any, *args: Any) -> bool:
        pipe = self._resolve_pipe()
        if not pipe:
            return False
        if self._ffi.lib.DM_Connect(pipe.encode("utf-8"), self.pipe_timeout) != 0:
            return False
        try:
            return func(*args) == 1
        finally:
            self._ffi.lib.DM_Close()

    def _call_u32(self, func: Any) -> Optional[int]:
        value = ctypes.c_uint32(0)
        if func(ctypes.byref(value)) != 0:
            return None
        return int(value.value)

    def _call_string(self, func: Any, size: int = 512) -> Optional[str]:
        buf = ctypes.create_string_buffer(size)
        if func(buf, size) != 0:
            return None
        return buf.value.decode("utf-8")

    def restart_app_if_necessary(self) -> bool:
        return self._ffi.lib.DM_RestartAppIfNecessary() != 0

    def set_product_data(self, product_data: str) -> bool:
        return self._call_bool(self._ffi.lib.SetProductData, product_data.encode("utf-8"))

    def set_product_id(self, product_id: str, flags: int = 0) -> bool:
        return self._call_bool(
            self._ffi.lib.SetProductId,
            product_id.encode("utf-8"),
            int(flags),
        )

    def set_data_directory(self, directory_path: str) -> bool:
        return self._call_bool(
            self._ffi.lib.SetDataDirectory,
            directory_path.encode("utf-8"),
        )

    def set_debug_mode(self, enable: bool) -> bool:
        return self._call_bool(self._ffi.lib.SetDebugMode, 1 if enable else 0)

    def set_custom_device_fingerprint(self, fingerprint: str) -> bool:
        return self._call_bool(
            self._ffi.lib.SetCustomDeviceFingerprint,
            fingerprint.encode("utf-8"),
        )

    def set_license_key(self, license_key: str) -> bool:
        return self._call_bool(self._ffi.lib.SetLicenseKey, license_key.encode("utf-8"))

    def set_activation_metadata(self, key: str, value: str) -> bool:
        return self._call_bool(
            self._ffi.lib.SetActivationMetadata,
            key.encode("utf-8"),
            value.encode("utf-8"),
        )

    def activate_license(self) -> bool:
        return self._call_bool(self._ffi.lib.ActivateLicense)

    def activate_license_offline(self, file_path: str) -> bool:
        return self._call_bool(
            self._ffi.lib.ActivateLicenseOffline,
            file_path.encode("utf-8"),
        )

    def generate_offline_deactivation_request(self, file_path: str) -> bool:
        return self._call_bool(
            self._ffi.lib.GenerateOfflineDeactivationRequest,
            file_path.encode("utf-8"),
        )

    def get_last_activation_error(self) -> Optional[int]:
        value = ctypes.c_uint32(0)
        ok = self._ffi.lib.GetLastActivationError(ctypes.byref(value)) == 0
        return int(value.value) if ok else None

    def is_license_genuine(self) -> bool:
        return self._call_bool(self._ffi.lib.IsLicenseGenuine)

    def is_license_valid(self) -> bool:
        return self._call_bool(self._ffi.lib.IsLicenseValid)

    def get_server_sync_grace_period_expiry_date(self) -> Optional[int]:
        return self._call_u32(self._ffi.lib.GetServerSyncGracePeriodExpiryDate)

    def get_activation_mode(self, buffer_size: int = 64) -> Optional[Dict[str, str]]:
        initial = ctypes.create_string_buffer(buffer_size)
        current = ctypes.create_string_buffer(buffer_size)
        code = self._ffi.lib.GetActivationMode(initial, buffer_size, current, buffer_size)
        if code != 0:
            return None
        return {
            "initial_mode": initial.value.decode("utf-8"),
            "current_mode": current.value.decode("utf-8"),
        }

    def get_license_key(self, buffer_size: int = 256) -> Optional[str]:
        return self._call_string(self._ffi.lib.GetLicenseKey, size=buffer_size)

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
        return self._call_string(self._ffi.lib.GetActivationId, size=buffer_size)

    def get_library_version(self, buffer_size: int = 32) -> Optional[str]:
        return self._call_string(self._ffi.lib.GetLibraryVersion, size=buffer_size)

    def reset(self) -> bool:
        return self._call_bool(self._ffi.lib.Reset)

    def check_for_updates(self, options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        req = json.dumps(options or {}).encode("utf-8")
        return self._call_pipe_json(self._ffi.lib.DM_CheckForUpdates, req)

    def download_update(self, options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        req = json.dumps(options or {}).encode("utf-8")
        return self._call_pipe_json(self._ffi.lib.DM_DownloadUpdate, req)

    def get_update_state(self) -> Optional[Dict[str, Any]]:
        return self._call_pipe_json(self._ffi.lib.DM_GetUpdateState)

    def wait_for_update_state_change(
        self,
        last_sequence: int,
        timeout_ms: int = 30000,
    ) -> Optional[Dict[str, Any]]:
        sequence = max(0, int(last_sequence))
        timeout = max(0, int(timeout_ms))
        return self._call_pipe_json(
            self._ffi.lib.DM_WaitForUpdateStateChange,
            sequence,
            timeout,
        )

    def quit_and_install(self, options: Optional[Dict[str, Any]] = None) -> bool:
        req = json.dumps(options or {}).encode("utf-8")
        return self._call_pipe_bool(self._ffi.lib.DM_QuitAndInstall, req)

    def json_to_canonical(self, json_str: str) -> str:
        canonical = self._ffi.json_to_canonical(json_str)
        return canonical or ""
