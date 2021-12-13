#! /usr/bin/env python

import functools
import json
import sys


print_to_stderr = functools.partial(print, file=sys.stderr)


def set_gha_output(name, value):
    print_to_stderr('::set-output name={name}::{value}'.format(**locals()))


def parse_inputs(raw_allowed_failures, raw_jobs):
    try:
        allowed_failures_input = json.loads(raw_allowed_failures)
    except json.decoder.JSONDecodeError:
        allowed_failures_input = list(
            map(str.strip, raw_allowed_failures.split(',')),
        )


    return {
        'allowed_failures': allowed_failures_input,
        'jobs': json.loads(raw_jobs),
    }


inputs = parse_inputs(raw_allowed_failures=sys.argv[1], raw_jobs=sys.argv[2])


jobs = inputs['jobs'] or {}
jobs_allowed_to_fail = inputs['allowed_failures'] or []

if not jobs:
    sys.exit(
        '❌ Invalid input jobs matrix, '
        'please provide a non-empty `needs` context',
    )


job_matrix_succeeded = all(
    job['result'] == 'success' for name, job in jobs.items()
    if name not in jobs_allowed_to_fail
)


set_gha_output(name='failure', value=not job_matrix_succeeded)
set_gha_output(
    name='result',
    value='success' if job_matrix_succeeded else 'failure',
)
set_gha_output(name='success', value=job_matrix_succeeded)


allowed_to_fail_jobs_succeeded = all(
    job['result'] == 'success' for name, job in jobs.items()
    if name in jobs_allowed_to_fail
)


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


print_to_stderr('📝 Job statuses:')
for name, job in jobs.items():
    print_to_stderr(
        '📝 {name} → {emoji} {result} [{status}]'.
        format(
            emoji='✓' if job['result'] == 'success' else '❌',
            name=name,
            result=job['result'],
            status='allowed to fail' if name in jobs_allowed_to_fail
            else 'required to succeed',
        ),
    )


sys.exit(int(not job_matrix_succeeded))
