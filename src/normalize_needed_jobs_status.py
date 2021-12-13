#! /usr/bin/env python

import functools
import json
import sys


print_to_stderr = functools.partial(print, file=sys.stderr)


allowed_failures_raw_input = sys.argv[1]
try:
    allowed_failures_input = json.loads(allowed_failures_raw_input)
except json.decoder.JSONDecodeError:
    allowed_failures_input = list(
        map(str.strip, allowed_failures_raw_input.split(',')),
    )


inputs = {
    'allowed_failures': allowed_failures_input,
    'jobs': json.loads(sys.argv[2]),
}


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


print_to_stderr(
    '::set-output name=failure::{failed}'.
    format(failed=not job_matrix_succeeded),
)
print_to_stderr(
    '::set-output name=result::{result}'.
    format(result='success' if job_matrix_succeeded else 'failure'),
)
print_to_stderr(
    '::set-output name=success::{succeeded}'.
    format(succeeded=job_matrix_succeeded),
)


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
