# dm-api-python

Python SDK for DistroMate `dm_api` native library.

## Install

```bash
pip install dm-api
```

## Quick Start (License)

```python
from dm_api import DmApi

api = DmApi()

api.set_product_data("<product-data>")
api.set_product_id("your-product-id")
api.set_license_key("XXXX-XXXX-XXXX")

if not api.activate_license():
    raise RuntimeError(api.get_last_error() or "activation failed")

if not api.is_license_genuine():
    code = api.get_last_activation_error()
    name = api.get_activation_error_name(code)
    raise RuntimeError(f"license check failed: {name}, err={api.get_last_error()}")
```

## API Groups

- License setup: `set_product_data`, `set_product_id`, `set_data_directory`, `set_debug_mode`, `set_custom_device_fingerprint`
- License activation: `set_license_key`, `set_license_callback`, `activate_license`, `get_last_activation_error`
- License state: `is_license_genuine`, `is_license_valid`, `get_server_sync_grace_period_expiry_date`, `get_activation_mode`
- License details: `get_license_key`, `get_license_expiry_date`, `get_license_creation_date`, `get_license_activation_date`, `get_activation_creation_date`, `get_activation_last_synced_date`, `get_activation_id`
- Update: `check_for_updates`, `download_update`, `cancel_update_download`, `get_update_state`, `get_post_update_info`, `ack_post_update_info`, `wait_for_update_state_change`, `quit_and_install`
- General: `get_library_version`, `json_to_canonical`, `get_last_error`, `reset`

## Update API Notes

- Update APIs return parsed JSON envelope (`dict`) when transport succeeds.
- If native API returns `NULL`, Python SDK returns `None`; check `get_last_error()`.
- `quit_and_install()` returns native `int` status code directly:
  - `1`: accepted, process should exit soon
  - `-1`: business-level rejection (check `get_last_error()`)
  - `-2`: transport/parse error

## Environment Variables

- `DM_API_PATH`: optional path to native library
- `DM_APP_ID`, `DM_PUBLIC_KEY`: optional defaults for app identity
- `DM_LAUNCHER_ENDPOINT`, `DM_LAUNCHER_TOKEN`: launcher IPC variables used by update APIs

## Release

- CI workflow validates package build.
- Tag `v*` triggers publish workflow to PyPI.
- Required secret: `PYPI_API_TOKEN`.
