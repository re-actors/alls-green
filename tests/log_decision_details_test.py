"""Unit tests for ``log_decision_details``'s status-display formatting."""

import io

import pytest

from job_outcome import JobRequirement, JobResult, JobVerdict
from normalize_needed_jobs_status import (
    ActionSummaryOutput,
    log_decision_details,
)


@pytest.fixture
def summary_file() -> io.StringIO:
    """Make a fresh in-memory summary-file stream."""
    return io.StringIO()


@pytest.fixture
def console_file() -> io.StringIO:
    """Make a fresh in-memory console-file stream."""
    return io.StringIO()


@pytest.fixture
def no_color(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> bool:
    """Indirect fixture: toggle NO_COLOR based on the parametrized value.

    :raises: TypeError
    """  # noqa: DOC501
    enabled = request.param
    if not isinstance(enabled, bool):  # pragma: no cover
        exc_msg = 'Type narrowing the param for MyPy'
        raise TypeError(exc_msg)

    if enabled:
        monkeypatch.setenv('NO_COLOR', '1')
    else:
        monkeypatch.delenv('NO_COLOR', raising=False)
    return enabled


def _invoke(
    *,
    verdicts: list[JobVerdict],
    summary_file: io.StringIO,
    console_file: io.StringIO,
    action_summary_output: ActionSummaryOutput = ActionSummaryOutput.ALL,
) -> None:
    log_decision_details(
        job_matrix_succeeded=all(verdict.acceptable for verdict in verdicts),
        jobs_allowed_to_fail=frozenset(),
        jobs_allowed_to_be_skipped=frozenset(),
        verdicts=verdicts,
        action_summary_output=action_summary_output,
        summary_file=summary_file,
        console_file=console_file,
    )


@pytest.mark.parametrize(
    ('verdicts', 'expected_symbol'),
    (
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='success',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=True,
                ),
            ],
            '🟢',
            id='success',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='failure',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=False,
                ),
            ],
            '🔴',
            id='failure',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='skipped',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=False,
                ),
            ],
            '⬜',
            id='skipped',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='cancelled',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=False,
                ),
            ],
            '⚫',
            id='cancelled',
        ),
    ),
)
def test_result_symbol_appears_in_summary(
    verdicts: list[JobVerdict],
    expected_symbol: str,
    summary_file: io.StringIO,
    console_file: io.StringIO,
) -> None:
    """Every JobResult maps to its expected status symbol."""
    _invoke(
        verdicts=verdicts,
        summary_file=summary_file,
        console_file=console_file,
    )
    assert expected_symbol in summary_file.getvalue()


@pytest.mark.parametrize(
    ('verdicts', 'expected_mark', 'unexpected_mark'),
    (
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='skipped',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=False,
                ),
            ],
            '❌',
            '✓',
            id='unacceptable-skip',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='skipped',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=True,
                ),
            ],
            '✓',
            '❌',
            id='acceptable-skip',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='failure',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=True,
                ),
            ],
            '✓',
            '❌',
            id='acceptable-failure',
        ),
        pytest.param(
            [
                JobVerdict(
                    name='job',
                    result='failure',
                    requirement=JobRequirement.REQUIRED,
                    acceptable=False,
                ),
            ],
            '❌',
            '✓',
            id='unacceptable-failure',
        ),
    ),
)
def test_accept_mark_follows_acceptable_not_result(
    verdicts: list[JobVerdict],
    expected_mark: str,
    unexpected_mark: str,
    summary_file: io.StringIO,
    console_file: io.StringIO,
) -> None:
    """Ensure The leading mark tracks the acceptable status.

    And it's independent of the literal result.
    """
    _invoke(
        verdicts=verdicts,
        summary_file=summary_file,
        console_file=console_file,
    )
    summary_text = summary_file.getvalue()
    assert expected_mark in summary_text
    assert unexpected_mark not in summary_text


_SAMPLE_UNACCEPTABLE_VERDICTS = [
    JobVerdict(
        name='job',
        result='failure',
        requirement=JobRequirement.REQUIRED,
        acceptable=False,
    ),
]


@pytest.mark.parametrize(
    'no_color',
    (True, False),
    indirect=True,
    ids=('no-color', 'color'),
)
def test_summary_is_always_plain_regardless_of_no_color(
    no_color: bool,  # noqa: ARG001  # monkey-patches env vars under the hood
    summary_file: io.StringIO,
    console_file: io.StringIO,
) -> None:
    """The markdown summary never contains ANSI escapes, NO_COLOR or not."""
    _invoke(
        verdicts=_SAMPLE_UNACCEPTABLE_VERDICTS,
        summary_file=summary_file,
        console_file=console_file,
    )
    assert '\x1b[' not in summary_file.getvalue()


@pytest.mark.parametrize(
    'no_color',
    (True, False),
    indirect=True,
    ids=('no-color', 'color'),
)
def test_console_is_colorized_unless_no_color(
    no_color: bool,
    summary_file: io.StringIO,
    console_file: io.StringIO,
) -> None:
    """The console stream gets ANSI color unless NO_COLOR is set."""
    _invoke(
        verdicts=_SAMPLE_UNACCEPTABLE_VERDICTS,
        summary_file=summary_file,
        console_file=console_file,
    )
    console_text = console_file.getvalue()
    if no_color:
        assert '\x1b[' not in console_text
    else:
        assert (
            '\x1b[31m❌ job → 🔴 failure [required to succeed]\x1b[0m'
            in console_text
        )


@pytest.mark.parametrize(
    ('action_summary_output', 'result', 'expect_summary'),
    (
        pytest.param(
            ActionSummaryOutput.ALL,
            'success',
            True,
            id='all-success',
        ),
        pytest.param(
            ActionSummaryOutput.ALL,
            'failure',
            True,
            id='all-failure',
        ),
        pytest.param(
            ActionSummaryOutput.NONE,
            'success',
            False,
            id='none-success',
        ),
        pytest.param(
            ActionSummaryOutput.NONE,
            'failure',
            False,
            id='none-failure',
        ),
        pytest.param(
            ActionSummaryOutput.QUIET_ON_SUCCESS,
            'success',
            False,
            id='quiet-on-success-success',
        ),
        pytest.param(
            ActionSummaryOutput.QUIET_ON_SUCCESS,
            'failure',
            True,
            id='quiet-on-success-failure',
        ),
    ),
)
def test_action_summary_output_routes_to_summary(
    action_summary_output: ActionSummaryOutput,
    result: JobResult,
    expect_summary: bool,
    summary_file: io.StringIO,
    console_file: io.StringIO,
) -> None:
    """The summary stream only gets content per the routing option."""
    acceptable = result == 'success'
    _invoke(
        verdicts=[
            JobVerdict(
                name='job',
                result=result,
                requirement=JobRequirement.REQUIRED,
                acceptable=acceptable,
            ),
        ],
        summary_file=summary_file,
        console_file=console_file,
        action_summary_output=action_summary_output,
    )
    summary_text = summary_file.getvalue()
    if expect_summary:
        assert summary_text
    else:
        assert not summary_text
