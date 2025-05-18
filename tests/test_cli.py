import sys
import pytest
from unittest import mock
from pathlib import Path
import yaml
from sniffing import cli

@pytest.fixture
def mock_config():
    return {
        "monitoring": {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "domains": {
            "security": {"enabled": True},
            "functional": {"enabled": True}
        }
    }

@pytest.mark.unit
def test_parse_args_sniff(monkeypatch):
    test_args = ["prog", "sniff", "--files", "file1.py,file2.py", "--domains", "security,functional"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = cli.parse_args()
    assert args.command == "sniff"
    assert args.files == "file1.py,file2.py"
    assert args.domains == "security,functional"
    assert args.config == "sniffing/config/sniffing_config.yaml"
    assert args.report_dir == "reports"

@pytest.mark.unit
def test_parse_args_install(monkeypatch):
    test_args = ["prog", "install", "--config", "custom_config.yaml"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = cli.parse_args()
    assert args.command == "install"
    assert args.config == "custom_config.yaml"

@pytest.mark.unit
def test_parse_args_fix(monkeypatch):
    test_args = ["prog", "fix", "--files", "file1.py", "--domains", "security"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = cli.parse_args()
    assert args.command == "fix"
    assert args.files == "file1.py"
    assert args.domains == "security"
    assert args.config == "sniffing/config/sniffing_config.yaml"

@pytest.mark.unit
async def test_run_sniffing(mock_config, tmp_path):
    args = mock.Mock(
        config="config.yaml",
        files="test.py",
        domains="security",
        report_dir=str(tmp_path)
    )

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml.dump(mock_config))), \
         mock.patch("sniffing.cli.SniffingLoop") as mock_loop, \
         mock.patch("sniffing.cli.setup_logger") as mock_logger:

        mock_loop.return_value.sniff_file.return_value = {"status": "success"}
        await cli.run_sniffing(args)

        mock_logger.assert_called_once()
        mock_loop.return_value.sniff_file.assert_called_once_with("test.py", ["security"])

@pytest.mark.unit
async def test_install_hooks(mock_config):
    args = mock.Mock(config="config.yaml")

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml.dump(mock_config))), \
         mock.patch("sniffing.cli.GitWorkflow") as mock_workflow, \
         mock.patch("sniffing.cli.setup_logger") as mock_logger:

        await cli.install_hooks(args)

        mock_logger.assert_called_once()
        mock_workflow.return_value.install_hooks.assert_called_once()

@pytest.mark.unit
async def test_fix_issues(mock_config, tmp_path):
    args = mock.Mock(
        config="config.yaml",
        files="test.py",
        domains="security"
    )

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml.dump(mock_config))), \
         mock.patch("sniffing.cli.SniffingLoop") as mock_loop, \
         mock.patch("sniffing.cli.setup_logger") as mock_logger:

        mock_loop.return_value.fix_file.return_value = {"status": "success"}
        await cli.fix_issues(args)

        mock_logger.assert_called_once()
        mock_loop.return_value.fix_file.assert_called_once_with("test.py", ["security"])

@pytest.mark.unit
def test_main_dispatch_sniff(monkeypatch):
    args = mock.Mock(command="sniff")
    with mock.patch("sniffing.cli.parse_args", return_value=args), \
         mock.patch("sniffing.cli.run_sniffing") as mock_run, \
         mock.patch("asyncio.run") as mock_asyncio:
        cli.main()
        mock_asyncio.assert_called_once_with(mock_run.return_value)

@pytest.mark.unit
def test_main_dispatch_install(monkeypatch):
    args = mock.Mock(command="install")
    with mock.patch("sniffing.cli.parse_args", return_value=args), \
         mock.patch("sniffing.cli.install_hooks") as mock_install, \
         mock.patch("asyncio.run") as mock_asyncio:
        cli.main()
        mock_asyncio.assert_called_once_with(mock_install.return_value)

@pytest.mark.unit
def test_main_dispatch_fix(monkeypatch):
    args = mock.Mock(command="fix")
    with mock.patch("sniffing.cli.parse_args", return_value=args), \
         mock.patch("sniffing.cli.fix_issues") as mock_fix, \
         mock.patch("asyncio.run") as mock_asyncio:
        cli.main()
        mock_asyncio.assert_called_once_with(mock_fix.return_value)

@pytest.mark.unit
def test_main_invalid_command(monkeypatch):
    args = mock.Mock(command=None)
    with mock.patch("sniffing.cli.parse_args", return_value=args), \
         mock.patch("sniffing.cli.logger") as mock_logger, \
         pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 1
    mock_logger.error.assert_called()

@pytest.mark.unit
def test_main_exception(monkeypatch):
    with mock.patch("sniffing.cli.parse_args", side_effect=Exception("fail")), \
         mock.patch("sniffing.cli.logger") as mock_logger, \
         pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 1
    mock_logger.error.assert_called()
