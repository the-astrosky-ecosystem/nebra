# Agent Guidance for Nebra

This document provides guidance for AI agents working on the Nebra project.

## Project Overview

Nebra is a Python library for streaming or sending time-critical scientific data live and for free on the ATProtocol.

## Development Environment

This project uses `uv` for Python dependency management and task execution. All Python dependencies are managed through `uv`. The project configuration is in `pyproject.toml`

NEVER use `uv pip` commands, as they are bad practice. Instead, use `uv add`, `uv remove`, and `uv sync --all-extras` to (re)install all packages.

## Key Commands

### After Making Changes

1. **Run Ruff to check and fix code style issues:**
   ```bash
   ruff check --fix
   ```
   
   This will automatically fix many common code style issues. Ruff is configured in `pyproject.toml`.

2. **Run tests:**
   ```bash
   pytest
   ```
   
   This will run all tests in the project. Make sure all tests pass before completing a task.

3. **Build the docs:**
   ```bash
   zensical build
   ```
   
   This will check that the documentation site still builds after your changes.

### Other Useful Commands

- **Run a specific test file:**
  ```bash
  pytest tests/test_file.py
  ```

- **Run tests with verbose output:**
  ```bash
  pytest -v
  ```

- **Run Ruff in check-only mode (without fixing):**
  ```bash
  ruff check
  ```

## Testing Guidelines

1. When adding new functionality, create corresponding tests in the `tests/` directory.
2. Use the existing test utilities in `tests/utilities.py` when possible.
3. For testing components that interact with ATProto, use mock send functions instead of posting real data.
4. Make sure tests are deterministic and don't rely on external services.

## Code Style

- Follow PEP 8 guidelines for Python code.
- Use type hints for function parameters and return values.
- Keep functions focused and modular.
- Add docstrings to functions and classes, following numpy docstyle.

## Project Structure

- `src/nebra/`: Main library code
- `tests/`: Test files
- `docs/`: Documentation for the module, written in markdown
- `pyproject.toml`: Project configuration and dependencies
- `uv.lock`: Lock file for dependencies

## Agent Workflow

1. Understand the task requirements.
2. Review relevant code in the codebase.
3. Make changes to implement the task.
4. Run `ruff check --fix` to ensure code style compliance.
5. Add or update tests as needed.
6. Run `pytest` to verify all tests pass.
7. Add any new changes to the documentation for the module.
8. Run `zensical build` to check that the documentation still builds.
9. Document any changes or new functionality in the final message.