"""Unit tests for the job-outcome state-mapping abstraction."""

import pytest

from job_outcome import (
    JobRequirement,
    JobResult,
    JobVerdict,
    classify_job_requirement,
    evaluate_jobs,
    job_outcome_is_acceptable,
)


ALL_RESULTS = ('success', 'failure', 'cancelled', 'skipped')

# What the README (allowed-failures/allowed-skips semantics) and the
# pre-regression v1.2.2 behavior say should be acceptable for each policy:
_EXPECTED_ACCEPTABLE_RESULTS = {
    JobRequirement.REQUIRED: {'success'},
    JobRequirement.ALLOWED_TO_BE_SKIPPED: {'success', 'skipped'},
    JobRequirement.ALLOWED_TO_FAIL: {
        'success',
        'failure',
        'cancelled',
        'skipped',
    },
    JobRequirement.ALLOWED_EITHER: {
        'success',
        'failure',
        'cancelled',
        'skipped',
    },
}


@pytest.mark.parametrize('requirement', list(JobRequirement))
@pytest.mark.parametrize('result', ALL_RESULTS)
def test_job_outcome_is_acceptable_matches_contract(
    result: JobResult,
    requirement: JobRequirement,
) -> None:
    """Exhaustively check every (requirement, result) combination."""
    expected = result in _EXPECTED_ACCEPTABLE_RESULTS[requirement]
    assert (
        job_outcome_is_acceptable(
            result=result,
            requirement=requirement,
        )
        is expected
    )


@pytest.mark.parametrize(
    (
        'job_name',
        'jobs_allowed_to_fail',
        'jobs_allowed_to_be_skipped',
        'expected',
    ),
    (
        pytest.param(
            'job',
            frozenset(),
            frozenset(),
            JobRequirement.REQUIRED,
            id='neither-list',
        ),
        pytest.param(
            'job',
            frozenset({'job'}),
            frozenset(),
            JobRequirement.ALLOWED_TO_FAIL,
            id='allowed-to-fail-only',
        ),
        pytest.param(
            'job',
            frozenset(),
            frozenset({'job'}),
            JobRequirement.ALLOWED_TO_BE_SKIPPED,
            id='allowed-to-be-skipped-only',
        ),
        pytest.param(
            'job',
            frozenset({'job'}),
            frozenset({'job'}),
            JobRequirement.ALLOWED_EITHER,
            id='both-lists',
        ),
    ),
)
def test_classify_job_requirement(
    job_name: str,
    jobs_allowed_to_fail: frozenset[str],
    jobs_allowed_to_be_skipped: frozenset[str],
    expected: JobRequirement,
) -> None:
    """Check the 4 set-membership combinations map to the right policy."""
    assert (
        classify_job_requirement(
            job_name=job_name,
            jobs_allowed_to_fail=jobs_allowed_to_fail,
            jobs_allowed_to_be_skipped=jobs_allowed_to_be_skipped,
        )
        == expected
    )


def test_evaluate_jobs_produces_one_verdict_per_job() -> None:
    """Check the whole-matrix aggregate over a small mixed example."""
    jobs: dict[str, JobResult] = {
        'required-job': 'success',
        'failing-but-allowed': 'failure',
        'skipped-but-required': 'skipped',
    }

    verdicts = evaluate_jobs(
        jobs=jobs,
        jobs_allowed_to_fail=frozenset({'failing-but-allowed'}),
        jobs_allowed_to_be_skipped=frozenset(),
    )

    assert verdicts == [
        JobVerdict(
            name='required-job',
            result='success',
            requirement=JobRequirement.REQUIRED,
            acceptable=True,
        ),
        JobVerdict(
            name='failing-but-allowed',
            result='failure',
            requirement=JobRequirement.ALLOWED_TO_FAIL,
            acceptable=True,
        ),
        JobVerdict(
            name='skipped-but-required',
            result='skipped',
            requirement=JobRequirement.REQUIRED,
            acceptable=False,
        ),
    ]
