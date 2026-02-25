# dm-api-python

Python SDK for DistroMate `dm_api.dll`.

## Install

```bash
pip install dm-api
```

## Integration Flow

This SDK follows the LexActivator-style integration flow:

1. `set_product_data()` and `set_product_id()`.
2. `set_license_key()` and `activate_license()`.
3. `is_license_genuine()` or `is_license_valid()` on every startup.
4. Optional version/update APIs: `get_version()`, `get_library_version()`, `check_for_updates()`.

## Quick Start

```python
from dm_api import DmApi

api = DmApi()
api.set_product_data("<product_data>")
api.set_product_id("your-product-id", flags=0)
api.set_license_key("XXXX-XXXX-XXXX")

if not api.activate_license():
    raise RuntimeError(api.get_last_error() or "activation failed")

if not api.is_license_genuine():
    raise RuntimeError(api.get_last_error() or "license not genuine")
```

## Version And Update APIs

- Runtime version: `get_version()`
- License library version: `get_library_version()`
- Update APIs: `check_for_updates()`, `download_update()`, `get_update_state()`, `wait_for_update_state_change()`, `quit_and_install()`

## Release

- CI workflow validates package build.
- Tag `v*` triggers publish workflow to PyPI.
- Required secret: `PYPI_API_TOKEN`.
