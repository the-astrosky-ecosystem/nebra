"""Tests for the Nebra CLI."""

import pytest
from click.testing import CliRunner

from nebra import cli


@pytest.fixture
def runner():
    """Fixture to provide a Click test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that the CLI shows help text."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output
    assert "stream" in result.output


def test_stream_help(runner):
    """Test that the `stream` command shows help text."""
    result = runner.invoke(cli, ["stream", "--help"])
    assert result.exit_code == 0
    assert "Usage: cli stream [OPTIONS]" in result.output


def test_stream_command(runner):
    """Test that the `stream` command runs without errors."""
    # Mock the `run_stream` function to avoid making real API calls during tests
    from nebra.jetstream import run_stream
    original_run_stream = run_stream

    def mock_run_stream(*args, **kwargs):
        print("Mock stream called")

    import nebra.jetstream
    nebra.jetstream.run_stream = mock_run_stream

    try:
        result = runner.invoke(cli, ["stream"])
        assert result.exit_code == 0
        assert "Mock stream called" in result.output
    finally:
        # Restore the original function
        nebra.jetstream.run_stream = original_run_stream


def test_stream_command_with_invalid_args(runner):
    """Test that the `stream` command handles invalid arguments gracefully."""
    result = runner.invoke(cli, ["stream", "--invalid-arg"])
    assert result.exit_code != 0
    assert "Error: No such option: --invalid-arg" in result.output


def test_stream_command_with_default_kinds(runner):
    """Test that the `stream` command defaults to 'commit' kind."""
    from nebra.jetstream import run_stream
    original_run_stream = run_stream

    def mock_run_stream(*args, **kwargs):
        assert kwargs.get("kinds", ("commit",)) == ("commit",)
        print("Mock stream called with kinds=['commit']")

    import nebra.jetstream
    nebra.jetstream.run_stream = mock_run_stream

    try:
        result = runner.invoke(cli, ["stream"])
        assert result.exit_code == 0
        assert "Mock stream called with kinds=['commit']" in result.output
    finally:
        nebra.jetstream.run_stream = original_run_stream


def test_stream_command_with_custom_kinds(runner):
    """Test that the `stream` command can accept custom kinds."""
    from nebra.jetstream import run_stream
    original_run_stream = run_stream

    def mock_run_stream(*args, **kwargs):
        assert kwargs.get("kinds", ()) == ("commit", "identity")
        print("Mock stream called with kinds=['commit', 'identity']")

    import nebra.jetstream
    nebra.jetstream.run_stream = mock_run_stream

    try:
        result = runner.invoke(cli, ["stream", "--kinds", "commit", "--kinds", "identity"])
        assert result.exit_code == 0
        assert "Mock stream called with kinds=['commit', 'identity']" in result.output
    finally:
        nebra.jetstream.run_stream = original_run_stream