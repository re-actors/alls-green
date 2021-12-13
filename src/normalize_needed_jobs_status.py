#! /usr/bin/env python

import json
import sys


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


print(
    '::set-output name=failure::{failed}'.
    format(failed=not job_matrix_succeeded),
    file=sys.stderr,
)
print(
    '::set-output name=result::{result}'.
    format(result='success' if job_matrix_succeeded else 'failure'),
    file=sys.stderr,
)
print(
    '::set-output name=success::{succeeded}'.
    format(succeeded=job_matrix_succeeded),
    file=sys.stderr,
)


allowed_to_fail_jobs_succeeded = all(
    job['result'] == 'success' for name, job in jobs.items()
    if name in jobs_allowed_to_fail
)


if job_matrix_succeeded:
    print(
        '🎉 All of the required dependency jobs succeeded.',
        file=sys.stderr,
    )
else:
    print(
        '😢 Some of the required to succeed jobs failed.',
        file=sys.stderr,
    )


if jobs_allowed_to_fail and allowed_to_fail_jobs_succeeded:
    print(
        '🛈 All of the allowed to fail dependency jobs succeeded.',
        file=sys.stderr,
    )
elif jobs_allowed_to_fail:
    print(
        '🛈 Some of the allowed to fail jobs did not succeed.',
        file=sys.stderr,
    )


print('📝 Job statuses:', file=sys.stderr)
for name, job in jobs.items():
    print(
        '📝 {name} → {emoji} {result} [{status}]'.
        format(
            emoji='✓' if job['result'] == 'success' else '❌',
            name=name,
            result=job['result'],
            status='allowed to fail' if name in jobs_allowed_to_fail
            else 'required to succeed',
        ),
        file=sys.stderr,
    )


sys.exit(int(not job_matrix_succeeded))
