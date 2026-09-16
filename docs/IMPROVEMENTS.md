# Improvement audit — 16 September 2026

## Correctness checkpoint

Reused identifiers could discard different dates, ASCII normalisation collapsed non-English events, and merging dropped shorter notes and distinct source URLs.

Implemented: preserve conflicting accounts and unicode event text during merging. Regression tests exercise the failure cases and
the original suite remains required. GitHub Actions runs tests, lint and package builds.

## Requested next release

The user requested the ranked product improvements, including optional local browser
workspaces. This extends the earlier CLI-only scope in CLAUDE.md. Existing command-line
interfaces and deterministic libraries remain supported. Browser workspaces must preserve
source evidence and explicit human review; they must not infer legal conclusions.

Workspace implementation, integration tests and release validation are in progress.
