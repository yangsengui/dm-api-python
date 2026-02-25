"""Configuration constants for dm_api."""

ENV_DM_PIPE = "DM_PIPE"
ENV_DM_API_PATH = "DM_API_PATH"
ENV_DM_APP_ID = "DM_APP_ID"
ENV_DM_PUBLIC_KEY = "DM_PUBLIC_KEY"

DEFAULT_DLL_NAME = "dm_api.dll"
DEFAULT_TIMEOUT_MS = 5000

DEV_LICENSE_ERROR = (
    "Development license is missing or corrupted. "
    "Run `distromate sdk renew` to regenerate the dev certificate."
)
