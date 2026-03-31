from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys
from uuid import uuid4

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from software.api import get_rng_service
from software.api.rng_service import RNGServiceConfig, StateConfig
from software.pqc_drbg import DRBGPolicy


def pytest_configure(config: pytest.Config) -> None:
    # Force pytest and tempfile to use a project-local temp root instead of
    # a broken Windows/OneDrive global temp directory. Use a session-unique
    # basetemp so pytest never scans stale numbered directories.
    temp_root = PROJECT_ROOT / "tests_runtime" / "pytest_tmp_root"
    temp_root.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(temp_root)
    os.environ["TEMP"] = str(temp_root)
    os.environ["TMPDIR"] = str(temp_root)
    tempfile.tempdir = str(temp_root)
    config.option.basetemp = str(temp_root / f"basetemp_{uuid4().hex}")


def build_test_config(
    root_dir: Path,
    *,
    name: str = "test",
    policy: DRBGPolicy | None = None,
) -> RNGServiceConfig:
    config = RNGServiceConfig(
        state=StateConfig(
            root_dir=root_dir,
            device_id=f"{name}-device",
            namespace=f"{name}-namespace",
            blob_id=f"{name}-blob",
            checkpoint_metadata={"purpose": f"{name}-checkpoint"},
        )
    )
    if policy is not None:
        config.drbg.policy = policy
    return config


@pytest.fixture
def configure_rng_service():
    def _configure(
        name: str,
        *,
        policy: DRBGPolicy | None = None,
    ):
        root_dir = PROJECT_ROOT / "tests_runtime" / "stage5" / f"{name}_{uuid4().hex[:8]}"
        root_dir.mkdir(parents=True, exist_ok=True)
        config = build_test_config(root_dir, name=name, policy=policy)
        return get_rng_service(reset=True, config=config)

    return _configure


@pytest.fixture(autouse=True)
def isolate_global_rng_service():
    root = PROJECT_ROOT / "tests_runtime" / "stage5" / f"autouse_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=True)
    service = get_rng_service(reset=True, config=build_test_config(root, name="autouse"))
    yield service
    service.zeroize()
    cleanup_root = PROJECT_ROOT / "tests_runtime" / "stage5" / f"cleanup_{uuid4().hex[:8]}"
    cleanup_root.mkdir(parents=True, exist_ok=True)
    get_rng_service(reset=True, config=build_test_config(cleanup_root, name="cleanup"))
