# Naming the Ducks

Canonical names for this project, and how to refer to it in
prose. Other files in `.agents-ctx/` (and any generated content)
should say "the project" rather than hardcoding one of these --
reach for a specific name only when the distinction actually
matters (e.g. citing a package, an import, or a repository URL).

## Action reference: `re-actors/alls-green`

This is a GitHub Action, not a Python distribution -- nothing is
published to PyPI. Workflows refer to it as
`re-actors/alls-green@<ref>`, usually `release/v1` or an exact
commit SHA. In prose, "alls-green".

## GitHub repository slug: `re-actors/alls-green`

The same as the action reference. Use it verbatim when it's
actually the repository being referenced (URLs, `gh` invocations,
PR/issue citations).

## Branches

`unstable/v1` is the development branch PRs target; `release/v1`
is what users pin to, with `release/v1.N` branches for minor
lines. Say which one is meant.
