"""Initial test infra smoke tests."""

import json
import pathlib
import sys

import pytest

from normalize_needed_jobs_status import main as _invoke_helper_cli


@pytest.mark.parametrize(
    (
        'allowed_failures',
        'allowed_skips',
        'jobs',
        'expected_return_code',
        'expected_outputs',
        'expected_summary_entries',
    ),
    (
        pytest.param(
            json.dumps(['failing-job', 'skipped-job']),
            '',
            json.dumps(
                {
                    'failing-job': {
                        'result': 'failure',
                        'outputs': {},
                    },
                    'succeeding-job': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'skipped-job': {
                        'result': 'skipped',
                        'outputs': {},
                    },
                },
            ),
            0,
            {'failure=false', 'result=success', 'success=true'},
            {
                'All of the required dependency jobs succeeded',
                'Some of the allowed to fail jobs did not succeed',
                'Some of the allowed to be skipped jobs did not succeed',
                'failing-job → ❌ failure [allowed to fail]',
                'succeeding-job → ✓ success [required to succeed]',
                'skipped-job → ⬜ skipped [allowed to fail]',
            },
            id='success-despite-failure-and-skip',
        ),
        pytest.param(
            'check-links-markdown, nightly',
            json.dumps([]),
            json.dumps(
                {
                    'build-web': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'check-links-book': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'check-links-markdown': {
                        'result': 'failure',
                        'outputs': {},
                    },
                    'lint-megalinter': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'nightly': {
                        'result': 'failure',
                        'outputs': {},
                    },
                    'publish-web': {
                        'result': 'skipped',
                        'outputs': {},
                    },
                    'test-dotnet': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-elixir': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-java': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-js': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-lib': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-php': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-python': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-rust': {
                        'result': 'success',
                        'outputs': {},
                    },
                    'test-rust-main': {
                        'result': 'success',
                        'outputs': {},
                    },
                },
            ),
            1,
            {'failure=true', 'result=failure', 'success=false'},
            {
                'Some of the required to succeed jobs failed',
                'Some of the allowed to fail jobs did not succeed',
                'Some of the allowed to be skipped jobs did not succeed',
                'build-web → ✓ success [required to succeed]',
                'check-links-book → ✓ success [required to succeed]',
                'check-links-markdown → ❌ failure [allowed to fail]',
                'lint-megalinter → ✓ success [required to succeed]',
                'nightly → ❌ failure [allowed to fail]',
                'publish-web → ⬜ skipped [required to succeed]',
                'test-dotnet → ✓ success [required to succeed]',
                'test-elixir → ✓ success [required to succeed]',
                'test-java → ✓ success [required to succeed]',
                'test-js → ✓ success [required to succeed]',
                'test-lib → ✓ success [required to succeed]',
                'test-php → ✓ success [required to succeed]',
                'test-python → ✓ success [required to succeed]',
                'test-rust → ✓ success [required to succeed]',
                'test-rust-main → ✓ success [required to succeed]',
            },
            id='failure-due-to-skip',
        ),
        pytest.param(
            'succeeding-job',
            'succeeding-job',
            json.dumps(
                {
                    'succeeding-job': {
                        'result': 'success',
                        'outputs': {},
                    },
                },
            ),
            0,
            {'failure=false', 'result=success', 'success=true'},
            {
                'All of the required dependency jobs succeeded',
                'All of the allowed to fail dependency jobs succeeded',
                'All of the allowed to be skipped dependency jobs succeeded',
                'succeeding-job → ✓ success [allowed to fail]',
            },
            id='success-of-all-allowed-to-skip-or-fail',
        ),
        pytest.param(
            'failing-job',
            'failing-job',
            json.dumps(
                {
                    'failing-job': {
                        'result': 'failure',
                        'outputs': {},
                    },
                },
            ),
            1,
            {'failure=false', 'result=success', 'success=true'},
            {
                'All of the required dependency jobs succeeded',
                'Some of the allowed to fail jobs did not succeed',
                'Some of the allowed to be skipped jobs did not succeed',
                'failing-job → ❌ failure [allowed to fail]',
            },
            id='success-of-some-allowed-to-skip-or-fail',
            marks=pytest.mark.xfail(reason='This is a bug to fix'),
        ),
        pytest.param(
            '',
            '',
            json.dumps(
                {
                    'succeeding-job': {
                        'result': 'success',
                        'outputs': {},
                    },
                },
            ),
            0,
            {'failure=false', 'result=success', 'success=true'},
            {
                'All of the required dependency jobs succeeded',
                'succeeding-job → ✓ success [required to succeed]',
            },
            id='everything-required',
        ),
        pytest.param(
            '',
            '',
            '{}',
            1,
            set(),
            {'Invalid input jobs matrix'},
            id='failure-due-to-empty-jobs',
        ),
    ),
)
def test_smoke(
    allowed_failures: str,
    allowed_skips: str,
    jobs: str,
    expected_return_code: int,
    expected_outputs: set[str],
    expected_summary_entries: set[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """Validate all known scenarios."""
    gh_step_summary_path = tmp_path / 'gh_step_summary'
    gh_output_path = tmp_path / 'gh_output'

    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(gh_step_summary_path))
    monkeypatch.setenv('GITHUB_OUTPUT', str(gh_output_path))

    helper_return_code = _invoke_helper_cli(
        [
            sys.executable,
            allowed_failures,
            allowed_skips,
            jobs,
        ],
    )
    assert helper_return_code == expected_return_code

    gh_step_summary_txt = gh_step_summary_path.read_text(encoding='utf-8')

    assert all(
        line in gh_step_summary_txt for line in expected_summary_entries
    )

    if not expected_outputs:
        return

    gh_output_txt = gh_output_path.read_text(encoding='utf-8')
    assert all(line in gh_output_txt for line in expected_outputs)
