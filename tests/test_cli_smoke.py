from typer.testing import CliRunner

from garmin_analytics import __version__
from garmin_analytics.cli import app


def test_package_imports() -> None:
    assert __version__


def test_cli_help_lists_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = result.output
    for cmd in ["discover", "ingest-uds", "ingest-sleep", "build-daily"]:
        assert cmd in output
