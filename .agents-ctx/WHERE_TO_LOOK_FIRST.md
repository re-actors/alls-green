# Where to Look First

When picking up a task, get oriented before proposing anything.
Read, in this order:

1. The packaging metadata -- what the project is, what it depends
   on, what it exposes.
2. The source of the module the task is about.
3. The shared test fixtures, then the tests for that module --
   they are the behavioral contract.
4. `tox.ini` and `.pre-commit-config.yaml` -- how things get run
   locally and in CI.
5. The main CI/CD workflow.

Here:

1. `action.yml` -- the composite action's inputs and the step
   running the helper. `pyproject.toml` only holds the testing
   dependency group; there's no packaging metadata.
2. `src/normalize_needed_jobs_status.py`, the helper the action
   runs, and `src/job_outcome.py`.
3. There's no `tests/conftest.py`; go straight to
   `tests/<topic>_test.py`.
4. As above -- `tox.ini` only has the `py` env, and the linters run
   through `pre-commit` directly.
5. `.github/workflows/self-smoke-test-action.yml`, which runs the
   action on itself.

Other places worth knowing:

- `README.md` -- the user-facing documentation.
