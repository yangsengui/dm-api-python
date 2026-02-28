"""Low-level ctypes wrapper around dm_api.dll."""

import ctypes
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import DEFAULT_DLL_NAME, ENV_DM_API_PATH


class DmApiFFI:
    LICENSE_CALLBACK_TYPE = ctypes.CFUNCTYPE(None)

    def __init__(self, dll_path: Optional[str] = None) -> None:
        path = dll_path or os.environ.get(ENV_DM_API_PATH, DEFAULT_DLL_NAME)
        resolved = Path(path)
        if not resolved.is_absolute():
            package_dir = Path(__file__).resolve().parent
            candidates = [package_dir / resolved, package_dir.parent / resolved]
            existing = next((candidate for candidate in candidates if candidate.exists()), None)
            resolved = existing or candidates[0]

        self.lib = ctypes.CDLL(str(resolved))
        self._init_signatures()

    def _init_signatures(self) -> None:
        self.lib.DM_FreeString.argtypes = [ctypes.c_void_p]
        self.lib.DM_FreeString.restype = None

        self.lib.DM_GetLastError.argtypes = []
        self.lib.DM_GetLastError.restype = ctypes.c_void_p

        self.lib.DM_CheckForUpdates.argtypes = [ctypes.c_char_p]
        self.lib.DM_CheckForUpdates.restype = ctypes.c_void_p
        self.lib.DM_DownloadUpdate.argtypes = [ctypes.c_char_p]
        self.lib.DM_DownloadUpdate.restype = ctypes.c_void_p
        self.lib.DM_CancelUpdateDownload.argtypes = [ctypes.c_char_p]
        self.lib.DM_CancelUpdateDownload.restype = ctypes.c_void_p
        self.lib.DM_GetUpdateState.argtypes = []
        self.lib.DM_GetUpdateState.restype = ctypes.c_void_p
        self.lib.DM_GetPostUpdateInfo.argtypes = []
        self.lib.DM_GetPostUpdateInfo.restype = ctypes.c_void_p
        self.lib.DM_AckPostUpdateInfo.argtypes = [ctypes.c_char_p]
        self.lib.DM_AckPostUpdateInfo.restype = ctypes.c_void_p
        self.lib.DM_WaitForUpdateStateChange.argtypes = [ctypes.c_uint64, ctypes.c_uint32]
        self.lib.DM_WaitForUpdateStateChange.restype = ctypes.c_void_p
        self.lib.DM_QuitAndInstall.argtypes = [ctypes.c_char_p]
        self.lib.DM_QuitAndInstall.restype = ctypes.c_int32

        self.lib.DM_JsonToCanonical.argtypes = [ctypes.c_char_p]
        self.lib.DM_JsonToCanonical.restype = ctypes.c_void_p

        self.lib.SetProductData.argtypes = [ctypes.c_char_p]
        self.lib.SetProductData.restype = ctypes.c_int32
        self.lib.SetProductId.argtypes = [ctypes.c_char_p]
        self.lib.SetProductId.restype = ctypes.c_int32
        self.lib.SetDataDirectory.argtypes = [ctypes.c_char_p]
        self.lib.SetDataDirectory.restype = ctypes.c_int32
        self.lib.SetDebugMode.argtypes = [ctypes.c_uint32]
        self.lib.SetDebugMode.restype = ctypes.c_int32
        self.lib.SetCustomDeviceFingerprint.argtypes = [ctypes.c_char_p]
        self.lib.SetCustomDeviceFingerprint.restype = ctypes.c_int32

        self.lib.SetLicenseKey.argtypes = [ctypes.c_char_p]
        self.lib.SetLicenseKey.restype = ctypes.c_int32
        self.lib.SetLicenseCallback.argtypes = [self.LICENSE_CALLBACK_TYPE]
        self.lib.SetLicenseCallback.restype = ctypes.c_int32
        self.lib.ActivateLicense.argtypes = []
        self.lib.ActivateLicense.restype = ctypes.c_int32
        self.lib.GetLastActivationError.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetLastActivationError.restype = ctypes.c_int32

        self.lib.IsLicenseGenuine.argtypes = []
        self.lib.IsLicenseGenuine.restype = ctypes.c_int32
        self.lib.IsLicenseValid.argtypes = []
        self.lib.IsLicenseValid.restype = ctypes.c_int32
        self.lib.GetServerSyncGracePeriodExpiryDate.argtypes = [
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self.lib.GetServerSyncGracePeriodExpiryDate.restype = ctypes.c_int32
        self.lib.GetActivationMode.argtypes = [
            ctypes.c_char_p,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.c_uint32,
        ]
        self.lib.GetActivationMode.restype = ctypes.c_int32

        self.lib.GetLicenseKey.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        self.lib.GetLicenseKey.restype = ctypes.c_int32
        self.lib.GetLicenseExpiryDate.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetLicenseExpiryDate.restype = ctypes.c_int32
        self.lib.GetLicenseCreationDate.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetLicenseCreationDate.restype = ctypes.c_int32
        self.lib.GetLicenseActivationDate.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetLicenseActivationDate.restype = ctypes.c_int32
        self.lib.GetActivationCreationDate.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetActivationCreationDate.restype = ctypes.c_int32
        self.lib.GetActivationLastSyncedDate.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        self.lib.GetActivationLastSyncedDate.restype = ctypes.c_int32
        self.lib.GetActivationId.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        self.lib.GetActivationId.restype = ctypes.c_int32

        self.lib.GetLibraryVersion.argtypes = []
        self.lib.GetLibraryVersion.restype = ctypes.c_char_p
        self.lib.Reset.argtypes = []
        self.lib.Reset.restype = ctypes.c_int32

    def ptr_to_json(self, ptr: int) -> Optional[Dict[str, Any]]:
        if not ptr:
            return None
        try:
            raw = ctypes.cast(ptr, ctypes.c_char_p).value
            if not raw:
                return None
            return json.loads(raw)
        finally:
            self.lib.DM_FreeString(ptr)

    def json_to_canonical(self, json_str: str) -> Optional[str]:
        ptr = self.lib.DM_JsonToCanonical(json_str.encode("utf-8"))
        if not ptr:
            return None
        try:
            raw = ctypes.cast(ptr, ctypes.c_char_p).value
            return raw.decode("utf-8") if raw else None
        finally:
            self.lib.DM_FreeString(ptr)

    def ptr_to_string(self, ptr: int) -> Optional[str]:
        if not ptr:
            return None
        try:
            raw = ctypes.cast(ptr, ctypes.c_char_p).value
            return raw.decode("utf-8") if raw else None
        finally:
            self.lib.DM_FreeString(ptr)
