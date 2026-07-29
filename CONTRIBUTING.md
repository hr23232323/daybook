# Contributing to Daybook

Thanks for helping make private personal-finance software better.

Daybook is intentionally small: one Python process, one SQLite file, and a browser
interface with no build step. Contributions should preserve that ease of inspection
unless a larger architectural change has been discussed first.

## Before you start

- Search existing issues before opening a new one.
- For a bug, include the smallest reproducible example you can safely share. Never
  attach a real bank export, setup token, API key, or `finance.db`.
- For a substantial feature or dependency, open an issue before writing the full
  implementation.
- Keep pull requests focused. Small commits with clear messages are easier to review.

## Local setup

You need Python 3.10 or newer.

```bash
make setup
make seed
make dev
```

Open <http://127.0.0.1:8888>. `make seed` creates fictional data and resets the local
database, so do not run it against data you want to keep.

The dashboard, imports, charts, and deterministic discoveries do not need an LLM key.
Most contributions can be developed without sending data to any external service.

## Project map

- `app/api.py` — FastAPI routes and the static application entry point
- `app/db.py` — schema, settings, and deduplicated writes
- `app/queries.py` — read-only financial queries
- `app/analysis.py` and `app/discover.py` — deterministic analysis
- `app/connectors/` — bank file and SimpleFIN ingestion
- `app/web/` — dependency-free HTML, CSS, and JavaScript interface
- `scripts/seed_fake_data.py` — realistic fictional development data

## Checks

There is not yet a full automated test suite. Before opening a pull request, run:

```bash
make check
```

The check target compiles the Python sources, validates the JavaScript when Node is
available, and checks the diff for whitespace errors.

Then exercise the affected flow with seeded data. For interface changes, check a wide
desktop and a narrow mobile viewport, keyboard focus, empty states, and long merchant
names.

## Product boundaries

These constraints are part of the product, not incidental implementation details:

- The app binds to `127.0.0.1` by default.
- Core features work without an LLM or remote account.
- Manual imports remain fully local.
- Financial claims must be traceable to stored transactions or computed aggregates.
- No telemetry, remote fonts, or CDN dependencies.
- Secrets and financial data never belong in logs, fixtures, screenshots, or commits.

If a contribution changes where data travels, what is persisted, or what an external
provider receives, update the privacy table in the README in the same pull request.

## Interface principles

Daybook should feel like a trustworthy instrument, not a generic analytics template.
Prefer legibility, exact figures, plain language, and inspectable evidence. Avoid
decorative metrics, unexplained scores, unnecessary animation, and UI that obscures
the source of a number.

The current frontend is deliberately framework-free and offline-capable. A dependency
is welcome when it solves a concrete problem that cannot be handled cleanly with the
existing stack; explain that tradeoff in the pull request.

## Pull requests

Describe:

1. What changed and why.
2. How you verified it.
3. Any privacy, migration, or compatibility impact.

By contributing, you agree that your contribution will be licensed under the
repository's MIT license.
