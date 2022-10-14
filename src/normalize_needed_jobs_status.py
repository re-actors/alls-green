#! /usr/bin/env python
"""A helper GitHub Action module that computes the outcome."""

import json
import os
import pathlib
import sys


FILE_APPEND_MODE = 'a'


def write_lines_to_streams(lines, streams):
    eoled_lines = [line + os.linesep for line in lines]
    for stream in streams:
        stream.writelines(eoled_lines)
        stream.flush()


def set_gha_output(name, value):
    """Set an action output using an environment file.

    Refs:
    * https://hynek.me/til/set-output-deprecation-github-actions/
    * https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter
    """
    outputs_file_path = pathlib.Path(os.environ['GITHUB_OUTPUT'])
    with outputs_file_path.open(mode=FILE_APPEND_MODE) as outputs_file:
        write_lines_to_streams((f'{name}::{value}',), (outputs_file,))


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


def drop_empty_from_list(a_list):
    return [list_element for list_element in a_list if list_element]


def parse_inputs(raw_allowed_failures, raw_allowed_skips, raw_jobs):
    """Normalize the action inputs by turning them into data."""
    allowed_failures_input = drop_empty_from_list(
        parse_as_list(raw_allowed_failures),
    )
    allowed_skips_input = drop_empty_from_list(
        parse_as_list(raw_allowed_skips),
    )

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
        summary_file_streams,
):
    """Record the decisions made into console output."""
    markdown_summary_lines = []

    markdown_summary_lines += {
        '# ✓ All of the required dependency jobs succeeded 🎉🎉🎉'
        if job_matrix_succeeded else
        '# ❌ Some of the required to succeed jobs failed 😢😢😢'
    }
    markdown_summary_lines += {''}

    if jobs_allowed_to_fail and allowed_to_fail_jobs_succeeded:
        markdown_summary_lines += {
            '🛈 All of the allowed to fail dependency jobs succeeded.',
        }
    elif jobs_allowed_to_fail:
        markdown_summary_lines += {
            '🛈 Some of the allowed to fail jobs did not succeed.',
        }


    if jobs_allowed_to_be_skipped and allowed_to_be_skipped_jobs_succeeded:
        markdown_summary_lines += {
            '🛈 All of the allowed to be skipped dependency jobs succeeded.',
        }
    elif jobs_allowed_to_fail:
        markdown_summary_lines += {
            '🛈 Some of the allowed to be skipped jobs did not succeed.',
        }


    markdown_summary_lines += {
        '📝 Job statuses:',
    }
    for name, job in jobs.items():
        markdown_summary_lines += {
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
        }

    write_lines_to_streams(markdown_summary_lines, summary_file_streams)


def main(argv):
    """Decide whether the needed jobs got satisfactory results."""
    inputs = parse_inputs(
        raw_allowed_failures=argv[1],
        raw_allowed_skips=argv[2],
        raw_jobs=argv[3],
    )
    summary_file_path = pathlib.Path(os.environ['GITHUB_STEP_SUMMARY'])


    jobs = inputs['jobs'] or {}
    jobs_allowed_to_fail = set(inputs['allowed_failures'] or [])
    jobs_allowed_to_be_skipped = set(inputs['allowed_skips'] or [])

    if not jobs:
        with summary_file_path.open(mode=FILE_APPEND_MODE) as summary_file:
            write_lines_to_streams(
                (
                    '# ❌ Invalid input jobs matrix, '
                    'please provide a non-empty `needs` context',
                ),
                (sys.stderr, summary_file),
            )
        return 1


    job_matrix_succeeded = all(
        job['result'] == 'success' for name, job in jobs.items()
        if name not in (jobs_allowed_to_fail | jobs_allowed_to_be_skipped)
    ) and all(
        job['result'] in {'skipped', 'success'} for name, job in jobs.items()
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


    with summary_file_path.open(mode=FILE_APPEND_MODE) as summary_file:
        log_decision_details(
            job_matrix_succeeded,
            jobs_allowed_to_fail,
            jobs_allowed_to_be_skipped,
            allowed_to_fail_jobs_succeeded,
            allowed_to_be_skipped_jobs_succeeded,
            jobs,
            summary_file_streams=(sys.stderr, summary_file),
        )


    return int(not job_matrix_succeeded)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
