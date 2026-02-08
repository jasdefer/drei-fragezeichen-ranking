# AGENTS.md

Guidance for coding agents working in this repository.

## Scope

- This file applies to the entire repo rooted at `drei-fragezeichen-ranking`.
- Follow repository conventions over generic preferences.
- Keep changes minimal, targeted, and easy to review.

## Rule Files

- Cursor rules: none found (`.cursor/rules/` missing, `.cursorrules` missing).
- Copilot rules: none found (`.github/copilot-instructions.md` missing).
- If these files are added later, treat them as higher-priority instructions.

## Project Layout

- `bot/`: core Python modules (API wrapper, rating model, validation, TSV I/O, CLI).
- `tests/`: automated tests (`unittest` style, runnable via `pytest` too).
- `data/`: TSV storage (`polls.tsv`, `ratings.tsv`) with strict header schemas.
- `docs/`: methodology and data-schema documentation.

## Environment Setup

- Create venv: `python -m venv .venv`
- Activate (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`
- Install test runner (optional but recommended): `pip install pytest`

Windows fallback if `python` alias is unavailable:

- Use `py -3 -m venv .venv`
- Use `py -3 -m pip install -r requirements.txt`
- Use `py -3 -m pytest ...`

## Build / Lint / Test Commands

There is no dedicated build system (no `pyproject.toml`, `tox`, `nox`, or Makefile).

Primary quality commands:

- Run all tests (pytest): `python -m pytest tests/`
- Run all tests verbose: `python -m pytest -v tests/`
- Run one test file: `python -m pytest tests/test_bradley_terry.py`
- Run one test case: `python -m pytest tests/test_bradley_terry.py::TestBradleyTerry`
- Run one single test: `python -m pytest tests/test_bradley_terry.py::TestBradleyTerry::test_happy_path_simple_preference`
- Alternative test runner: `python -m unittest discover tests/`

Validation / runtime commands:

- Run bot default entrypoint: `python -m bot`
- Run data validation command: `python -m bot validate-data`

Linting / formatting / typing status:

- No repo-configured linter (ruff/flake8/pylint) found.
- No repo-configured formatter (black/isort) found.
- No repo-configured static type checker (mypy/pyright) found.
- If you add such tooling, keep config explicit and scoped.

Useful ad-hoc checks:

- Syntax check: `python -m compileall bot tests`

## Testing Notes

- `tests/test_dreimetadaten_api.py` performs real network calls to Dreimetadaten API.
- Expect network-dependent failures/timeouts in restricted CI or offline environments.
- Prefer adding unit tests that avoid network and filesystem side effects when possible.
- For model logic, follow pattern used in `compute_ratings_from_polls()` tests.

## Code Style Guidelines

### General Python Style

- Use Pythonic, readable code; prioritize clarity over cleverness.
- Keep functions focused; extract helpers when logic becomes multi-step.
- Preserve existing docstring style (triple double quotes, descriptive, often German text).
- Add type hints on function signatures (args and return values).

### Imports

- Group imports in this order: standard library, third-party, local (`bot.*`).
- Use absolute local imports (`from bot.module import ...`), not relative imports.
- Avoid unused imports; remove dead imports during touched-file edits.

### Naming

- Functions and variables: `snake_case`.
- Classes and exceptions: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Keep domain terms consistent (`episode_id`, `polls`, `ratings`, `calculated_at`).

### Types and Data Shapes

- Follow existing typed container style: `List[Dict[str, Any]]`, `Dict[int, Set[int]]`, etc.
- Prefer explicit schemas for TSV row dictionaries.
- Validate critical inputs at boundaries (file rows, API payloads, timestamps).
- Datetime values used in ranking must be timezone-aware UTC.

### Formatting

- Match existing style (PEP 8-ish, readable line breaks, trailing commas in multiline calls).
- Keep log messages concise and actionable.
- Avoid introducing non-ASCII unless the target file already relies on it.

### Error Handling

- Use domain exceptions already present:
  - `APIError`, `APITimeoutError`, `APIResponseError`
  - `TSVError` (alias `TSVLoadError`)
  - `ValidationError`
  - `BradleyTerryError`
- Wrap lower-level exceptions with contextual messages.
- Re-raise when caller should handle; do not silently swallow failures.
- Fail fast on schema mismatch or invalid critical fields.

### Logging

- Use `logger = get_logger(__name__)` in modules.
- Initialize logging centrally (`setup_logging()`) at entrypoints.
- Use levels intentionally:
  - `debug` for diagnostics
  - `info` for lifecycle/status
  - `warning` for recoverable issues
  - `error` for terminal failures

### I/O and Data Rules

- `polls.tsv` and `ratings.tsv` use tab delimiter and UTF-8.
- Header order is strict and validated; do not reorder columns.
- `ratings.tsv` is append-only by design.
- `calculated_at` format: ISO-8601 UTC with `Z` suffix (`YYYY-MM-DDTHH:MM:SSZ`).
- Keep utility formatting consistent with repository behavior (6 decimals on write).

### Model and Domain Rules

- Bradley-Terry model centers on connectivity to episode `1`.
- Episodes not connected to episode `1` are intentionally excluded from ranking.
- Keep compute logic I/O-free where possible (`compute_ratings_from_polls`).
- Maintain normalization invariant for utilities (mean approximately `1.0`).

## Known Repository Gotchas

- `bot/__main__.py` imports `bot.tsv_loader`, but current repo module is `bot.tsv_repository`.
- If you touch CLI validation flow, resolve this mismatch consistently.
- API tests assert concrete external data (for example episode 149 title), which may drift.

## Change Checklist for Agents

- Update or add tests for behavioral changes.
- Run the narrowest relevant test first, then broader suite if feasible.
- Keep docs in sync when changing schema, commands, or model assumptions.
- Avoid manual edits to generated/append-only historical rating data unless requested.
- Keep commits small and explain why a change is needed.
