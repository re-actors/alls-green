"""Initial test infra smoke tests."""

import normalize_needed_jobs_status  # pth via editable install in tox


def test_smoke() -> None:
    """Check that the imported module is truthy."""
    assert normalize_needed_jobs_status
