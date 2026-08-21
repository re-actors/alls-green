"""Pure helpers mapping a job's voting policy to acceptable outcomes."""

import dataclasses
import enum
import typing as _t


JobResult = _t.Literal['success', 'failure', 'cancelled', 'skipped']


class JobRequirement(enum.Enum):
    """A job's voting policy, derived from the allow-lists.

    (README > Options).
    """

    REQUIRED = enum.auto()
    ALLOWED_TO_FAIL = enum.auto()
    ALLOWED_TO_BE_SKIPPED = enum.auto()
    ALLOWED_EITHER = enum.auto()


ACCEPTABLE_RESULTS: dict[JobRequirement, frozenset[JobResult]] = {
    JobRequirement.REQUIRED: frozenset({'success'}),
    JobRequirement.ALLOWED_TO_BE_SKIPPED: frozenset({'success', 'skipped'}),
    JobRequirement.ALLOWED_TO_FAIL: frozenset(
        {'success', 'failure', 'cancelled', 'skipped'},
    ),
    JobRequirement.ALLOWED_EITHER: frozenset(
        {'success', 'failure', 'cancelled', 'skipped'},
    ),
}


def classify_job_requirement(
    *,
    job_name: str,
    jobs_allowed_to_fail: _t.AbstractSet[str],
    jobs_allowed_to_be_skipped: _t.AbstractSet[str],
) -> JobRequirement:
    """Classify one job's voting policy from the two allow-lists."""
    allowed_to_fail = job_name in jobs_allowed_to_fail
    allowed_to_be_skipped = job_name in jobs_allowed_to_be_skipped
    if allowed_to_fail and allowed_to_be_skipped:
        return JobRequirement.ALLOWED_EITHER
    if allowed_to_fail:
        return JobRequirement.ALLOWED_TO_FAIL
    if allowed_to_be_skipped:
        return JobRequirement.ALLOWED_TO_BE_SKIPPED
    return JobRequirement.REQUIRED


def job_outcome_is_acceptable(
    *,
    result: JobResult,
    requirement: JobRequirement,
) -> bool:
    """Decide whether one job's actual result satisfies its policy."""
    return result in ACCEPTABLE_RESULTS[requirement]


@dataclasses.dataclass(frozen=True)
class JobVerdict:
    """The classified policy and acceptance decision for one job."""

    name: str
    result: JobResult
    requirement: JobRequirement
    acceptable: bool


def evaluate_jobs(
    *,
    jobs: _t.Mapping[str, JobResult],
    jobs_allowed_to_fail: _t.AbstractSet[str],
    jobs_allowed_to_be_skipped: _t.AbstractSet[str],
) -> list[JobVerdict]:
    """Classify and judge every job in the matrix."""
    verdicts = []
    for name, result in jobs.items():
        requirement = classify_job_requirement(
            job_name=name,
            jobs_allowed_to_fail=jobs_allowed_to_fail,
            jobs_allowed_to_be_skipped=jobs_allowed_to_be_skipped,
        )
        verdicts.append(
            JobVerdict(
                name=name,
                result=result,
                requirement=requirement,
                acceptable=job_outcome_is_acceptable(
                    result=result,
                    requirement=requirement,
                ),
            ),
        )
    return verdicts
