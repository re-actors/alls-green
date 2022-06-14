#! /usr/bin/env python
"""A helper GitHub Action module that computes the outcome."""

import functools
import json
import sys


print_to_stderr = functools.partial(print, file=sys.stderr)


def set_gha_output(name, value):
    """Set an action output using a runner command.

    https://docs.github.com/en/actions/learn-github-actions/workflow-commands-for-github-actions#setting-an-output-parameter
    """
    print_to_stderr('::set-output name={name}::{value}'.format(**locals()))


def set_final_result_outputs(job_matrix_succeeded):
    """Set action outputs depending on the computed outcome."""
    set_gha_output(name='failure', value=str(not job_matrix_succeeded).lower())
    set_gha_output(
        name='result',
        value='success' if job_matrix_succeeded else 'failure',
    )
    set_gha_output(name='success', value=str(job_matrix_succeeded).lower())


def parse_as_list(input_text):
    """Parse given input as JSON or comma-separated list."""
    try:
        return json.loads(input_text)
    except json.decoder.JSONDecodeError:
        return [s.strip() for s in input_text.split(',')]


def parse_inputs(raw_allowed_failures, raw_allowed_skips, raw_jobs):
    """Normalize the action inputs by turning them into data."""
    allowed_failures_input = parse_as_list(raw_allowed_failures)
    allowed_skips_input = parse_as_list(raw_allowed_skips)

    return {
        'allowed_failures': allowed_failures_input,
        'allowed_skips': allowed_skips_input,
        'jobs': json.loads(raw_jobs),
    }


def log_decision_details(
        job_matrix_succeeded,
        jobs_allowed_to_fail,
        jobs_allowed_to_be_skipped,
        allowed_to_fail_jobs_succeeded,
        allowed_to_be_skipped_jobs_succeeded,
        jobs,
):
    """Record the decisions made into console output."""
    if job_matrix_succeeded:
        print_to_stderr(
            '🎉 All of the required dependency jobs succeeded.',
        )
    else:
        print_to_stderr(
            '😢 Some of the required to succeed jobs failed.',
        )


    if jobs_allowed_to_fail and allowed_to_fail_jobs_succeeded:
        print_to_stderr(
            '🛈 All of the allowed to fail dependency jobs succeeded.',
        )
    elif jobs_allowed_to_fail:
        print_to_stderr(
            '🛈 Some of the allowed to fail jobs did not succeed.',
        )


    if jobs_allowed_to_be_skipped and allowed_to_be_skipped_jobs_succeeded:
        print_to_stderr(
            '🛈 All of the allowed to be skipped dependency jobs succeeded.',
        )
    elif jobs_allowed_to_fail:
        print_to_stderr(
            '🛈 Some of the allowed to be skipped jobs did not succeed.',
        )


    print_to_stderr('📝 Job statuses:')
    for name, job in jobs.items():
        print_to_stderr(
            '📝 {name} → {emoji} {result} [{status}]'.
            format(
                emoji='✓' if job['result'] == 'success'
                else '❌' if job['result'] == 'failure'
                else '⬜',
                name=name,
                result=job['result'],
                status='allowed to fail' if name in jobs_allowed_to_fail
                else 'required to succeed'
                if name not in jobs_allowed_to_be_skipped
                else 'required to succeed or be skipped',
            ),
        )


def main(argv):
    """Decide whether the needed jobs got satisfactory results."""
    inputs = parse_inputs(
        raw_allowed_failures=argv[1],
        raw_allowed_skips=argv[2],
        raw_jobs=argv[3],
    )


    jobs = inputs['jobs'] or {}
    jobs_allowed_to_fail = set(inputs['allowed_failures'] or [])
    jobs_allowed_to_be_skipped = set(inputs['allowed_skips'] or [])

    if not jobs:
        sys.exit(
            '❌ Invalid input jobs matrix, '
            'please provide a non-empty `needs` context',
        )


    job_matrix_succeeded = all(
        job['result'] == 'success' for name, job in jobs.items()
        if name not in (jobs_allowed_to_fail | jobs_allowed_to_be_skipped)
    ) and all(
        job['result'] in {'skipped', 'cancelled', 'success'} for name, job in jobs.items()
        if name in jobs_allowed_to_be_skipped
    )
    set_final_result_outputs(job_matrix_succeeded)


    allowed_to_fail_jobs_succeeded = all(
        job['result'] == 'success' for name, job in jobs.items()
        if name in jobs_allowed_to_fail
    )


    allowed_to_be_skipped_jobs_succeeded = all(
        job['result'] == 'success' for name, job in jobs.items()
        if name in jobs_allowed_to_be_skipped
    )


    log_decision_details(
            job_matrix_succeeded,
            jobs_allowed_to_fail,
            jobs_allowed_to_be_skipped,
            allowed_to_fail_jobs_succeeded,
            allowed_to_be_skipped_jobs_succeeded,
            jobs,
    )


    return int(not job_matrix_succeeded)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
