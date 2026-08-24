from unittest.mock import patch

from ebook_mcp.tools.docker_cli import run_compose


@patch("sys.argv", ["poe", "up"])
@patch("subprocess.run")
def test_run_compose_up(mock_run):
    run_compose()
    mock_run.assert_called_once_with(["docker", "compose", "up", "-d", "--build"], check=True)


@patch("sys.argv", ["poe", "inspector"])
@patch("subprocess.run")
def test_run_compose_inspector(mock_run):
    run_compose()
    mock_run.assert_called_once_with(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "-f",
            "docker-compose.inspector.yml",
            "up",
            "--build",
        ],
        check=True,
    )
