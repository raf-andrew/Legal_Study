"""
Script to run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file and specific log format and specific log rotation and specific log compression and specific log encoding and specific log mode and specific log delay and specific log buffering and specific log filters and specific log handlers and specific log formatters.
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import signal
import sys
import yaml
from datetime import datetime
from logging.handlers import RotatingFileHandler, SysLogHandler, SMTPHandler, HTTPHandler
from pathlib import Path
from typing import Dict, List, Optional

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_domains_files_options_output_format_log_file_format_rotation_compression_encoding_mode_delay_buffering_filters_handlers_formatters")

class LogFilter(logging.Filter):
    """Class for filtering log records."""

    def __init__(self, name: str = "", filters: List[str] = None):
        """Initialize filter.

        Args:
            name: Name of the filter
            filters: List of filters to apply
        """
        super().__init__(name)
        self.filters = filters or []

    def filter(self, record):
        """Filter log record.

        Args:
            record: Log record to filter

        Returns:
            bool: Whether to include the record
        """
        if not self.filters:
            return True

        return any(f in record.getMessage() for f in self.filters)

class LogFormatter(logging.Formatter):
    """Class for formatting log records."""

    def __init__(self, fmt: str = None, datefmt: str = None, style: str = "%"):
        """Initialize formatter.

        Args:
            fmt: Format string
            datefmt: Date format string
            style: Style of format string
        """
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        """Format log record.

        Args:
            record: Log record to format

        Returns:
            str: Formatted log record
        """
        # Add custom fields
        record.timestamp = datetime.fromtimestamp(record.created).isoformat()
        record.hostname = os.uname().nodename
        record.pid = os.getpid()

        return super().format(record)

class CompressedRotatingFileHandler(RotatingFileHandler):
    """Class for handling compressed rotating log files."""

    def __init__(self, filename: str, mode: str = "a", maxBytes: int = 0, backupCount: int = 0, encoding: Optional[str] = None, delay: bool = False, compress: bool = False, buffering: int = -1, filters: List[str] = None):
        """Initialize handler.

        Args:
            filename: Path to log file
            mode: Mode to open file in
            maxBytes: Maximum number of bytes per log file
            backupCount: Number of backup log files to keep
            encoding: Encoding to use
            delay: Whether to delay opening the file
            compress: Whether to compress backup files
            buffering: Buffering policy (-1 for system default, 0 for unbuffered, >0 for buffer size)
            filters: List of filters to apply
        """
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress = compress
        self.buffering = buffering
        if filters:
            self.addFilter(LogFilter(filters=filters))

    def _open(self):
        """Open the current base file with the (original) mode and encoding."""
        return open(self.baseFilename, self.mode, buffering=self.buffering, encoding=self.encoding)

    def doRollover(self):
        """Do rollover."""
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

            if self.compress:
                import gzip
                with open(dfn, "rb") as f_in:
                    with gzip.open(f"{dfn}.gz", "wb") as f_out:
                        f_out.writelines(f_in)
                os.remove(dfn)

        if not self.delay:
            self.stream = self._open()

def get_log_handlers(
    args: argparse.Namespace,
    log_filters: List[str],
    log_formatter: logging.Formatter
) -> List[logging.Handler]:
    """Get log handlers.

    Args:
        args: Command line arguments
        log_filters: List of filters to apply
        log_formatter: Formatter to use

    Returns:
        List[logging.Handler]: List of log handlers
    """
    handlers = []

    # Add file handler
    if args.log_file:
        handler = CompressedRotatingFileHandler(
            args.log_file,
            mode=args.log_mode,
            maxBytes=args.log_max_bytes,
            backupCount=args.log_backup_count,
            compress=args.log_compress,
            encoding=args.log_encoding,
            delay=args.log_delay,
            buffering=args.log_buffering,
            filters=log_filters
        )
        handler.setFormatter(log_formatter)
        handlers.append(handler)

    # Add syslog handler
    if args.syslog_host:
        handler = SysLogHandler(
            address=(args.syslog_host, args.syslog_port),
            facility=args.syslog_facility
        )
        handler.setFormatter(log_formatter)
        handlers.append(handler)

    # Add SMTP handler
    if args.smtp_host:
        handler = SMTPHandler(
            mailhost=(args.smtp_host, args.smtp_port),
            fromaddr=args.smtp_from,
            toaddrs=args.smtp_to.split(","),
            subject=args.smtp_subject,
            credentials=(args.smtp_user, args.smtp_password) if args.smtp_user else None,
            secure=() if args.smtp_secure else None
        )
        handler.setFormatter(log_formatter)
        handlers.append(handler)

    # Add HTTP handler
    if args.http_host:
        handler = HTTPHandler(
            host=args.http_host,
            url=args.http_url,
            method=args.http_method,
            secure=args.http_secure
        )
        handler.setFormatter(log_formatter)
        handlers.append(handler)

    # Add stdout handler
    if args.stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(log_formatter)
        handlers.append(handler)

    return handlers

class DomainFileOptionOutputFormatLogFileFormatRotationCompressionEncodingModeDelayBufferingFiltersHandlersFormattersRunner:
    """Class for running sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file and specific log format and specific log rotation and specific log compression and specific log encoding and specific log mode and specific log delay and specific log buffering and specific log filters and specific log handlers and specific log formatters."""

    def __init__(
        self,
        mode: str,
        config_path: str,
        domains: List[str],
        files: List[str],
        options: Dict[str, any],
        output_path: str,
        output_format: str,
        log_level: str,
        log_file: str,
        log_format: str,
        log_max_bytes: int,
        log_backup_count: int,
        log_compress: bool,
        log_encoding: str,
        log_mode: str,
        log_delay: bool,
        log_buffering: int,
        log_filters: List[str],
        log_handlers: List[logging.Handler],
        log_formatter: logging.Formatter
    ):
        """Initialize runner.

        Args:
            mode: Mode to run in
            config_path: Path to configuration file
            domains: List of domains to run
            files: List of files to run
            options: Dictionary of options to use
            output_path: Path to output file
            output_format: Format of output file
            log_level: Level of logging
            log_file: Path to log file
            log_format: Format of log file
            log_max_bytes: Maximum number of bytes per log file
            log_backup_count: Number of backup log files to keep
            log_compress: Whether to compress backup log files
            log_encoding: Encoding to use for log files
            log_mode: Mode to open log files in
            log_delay: Whether to delay opening log files
            log_buffering: Buffering policy (-1 for system default, 0 for unbuffered, >0 for buffer size)
            log_filters: List of filters to apply
            log_handlers: List of log handlers
            log_formatter: Formatter to use
        """
        self.mode = mode
        self.config_path = Path(config_path)
        self.domains = domains
        self.files = files
        self.options = options
        self.output_path = Path(output_path)
        self.output_format = output_format
        self.log_level = log_level
        self.log_file = Path(log_file)
        self.log_format = log_format
        self.log_max_bytes = log_max_bytes
        self.log_backup_count = log_backup_count
        self.log_compress = log_compress
        self.log_encoding = log_encoding
        self.log_mode = log_mode
        self.log_delay = log_delay
        self.log_buffering = log_buffering
        self.log_filters = log_filters
        self.log_handlers = log_handlers
        self.log_formatter = log_formatter
        self.server: Optional[MCPServer] = None
        self.running = True

    async def run(
        self,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run in specific mode with specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file and specific log format and specific log rotation and specific log compression and specific log encoding and specific log mode and specific log delay and specific log buffering and specific log filters and specific log handlers and specific log formatters.

        Args:
            verbose: Whether to enable verbose logging
            trace: Whether to enable trace logging
        """
        try:
            # Load config
            if not self.config_path.exists():
                logger.error("Config file not found")
                return

            # Create MCP server
            self.server = MCPServer(str(self.config_path))

            # Start server
            server_task = asyncio.create_task(self.server.start())

            try:
                # Run sniffing
                await self._run_sniffing(verbose, trace)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running in {self.mode} mode with config {self.config_path}, domains {self.domains}, files {self.files}, options {self.options}, output {self.output_path}, format {self.output_format}, log level {self.log_level}, log file {self.log_file}, log format {self.log_format}, log max bytes {self.log_max_bytes}, log backup count {self.log_backup_count}, log compress {self.log_compress}, log encoding {self.log_encoding}, log mode {self.log_mode}, log delay {self.log_delay}, log buffering {self.log_buffering}, log filters {self.log_filters}, log handlers {self.log_handlers}, and log formatter {self.log_formatter}: {e}")
            raise

    async def _run_sniffing(
        self,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run sniffing.

        Args:
            verbose: Whether to enable verbose logging
            trace: Whether to enable trace logging
        """
        try:
            if not self.server:
                return

            logger.info(f"Running sniffing in {self.mode} mode with config {self.config_path}, domains {self.domains}, files {self.files}, options {self.options}, output {self.output_path}, format {self.output_format}, log level {self.log_level}, log file {self.log_file}, log format {self.log_format}, log max bytes {self.log_max_bytes}, log backup count {self.log_backup_count}, log compress {self.log_compress}, log encoding {self.log_encoding}, log mode {self.log_mode}, log delay {self.log_delay}, log buffering {self.log_buffering}, log filters {self.log_filters}, log handlers {self.log_handlers}, and log formatter {self.log_formatter}...")

            # Get priority based on mode
            priority = {
                "debug": 5,
                "profile": 6,
                "test": 7,
                "prod": 8,
                "ci": 9,
                "all": 10
            }.get(self.mode, 0)

            # Run sniffing
            result = await self.server.sniff({
                "files": self.files,
                "domains": self.domains,
                "verbose": verbose,
                "trace": trace,
                "priority": priority,
                **self.options
            })

            # Check result
            if result.get("status") != "completed":
                logger.error("Sniffing failed")
                return

            # Log issues
            results = result.get("results", {})
            for file_path, file_results in results.items():
                for domain, domain_result in file_results.items():
                    issues = domain_result.get("issues", [])
                    if issues:
                        logger.info(
                            f"{file_path} ({domain}): "
                            f"{len(issues)} issues found"
                        )

                        # Log issue details
                        for issue in issues:
                            logger.info(
                                f"  - {issue.get('title')} "
                                f"({issue.get('severity')}): "
                                f"{issue.get('description')}"
                            )

                            if issue.get("fix"):
                                logger.info(f"    Fix: {issue.get('fix')}")

                            if issue.get("trace"):
                                logger.info("    Trace:")
                                for line in issue.get("trace", []):
                                    logger.info(f"      {line}")

            # Write output
            if self.output_format == "json":
                with open(self.output_path, self.log_mode, encoding=self.log_encoding, buffering=self.log_buffering) as f:
                    json.dump(result, f, indent=2)
            elif self.output_format == "yaml":
                with open(self.output_path, self.log_mode, encoding=self.log_encoding, buffering=self.log_buffering) as f:
                    yaml.dump(result, f, indent=2)
            elif self.output_format == "csv":
                with open(self.output_path, self.log_mode, newline="", encoding=self.log_encoding, buffering=self.log_buffering) as f:
                    writer = csv.writer(f)
                    writer.writerow(["file", "domain", "title", "severity", "description", "fix", "trace"])
                    for file_path, file_results in results.items():
                        for domain, domain_result in file_results.items():
                            for issue in domain_result.get("issues", []):
                                writer.writerow([
                                    file_path,
                                    domain,
                                    issue.get("title"),
                                    issue.get("severity"),
                                    issue.get("description"),
                                    issue.get("fix"),
                                    "\n".join(issue.get("trace", []))
                                ])
            else:
                logger.error(f"Unsupported output format: {self.output_format}")
                return

            logger.info("Sniffing completed")

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            raise

    def stop(self) -> None:
        """Stop runner."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping runner...")
    if runner:
        runner.stop()

def main() -> None:
    """Main entry point."""
    try:
        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file and specific log format and specific log rotation and specific log compression and specific log encoding and specific log mode and specific log delay and specific log buffering and specific log filters and specific log handlers and specific log formatters"
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["debug", "profile", "test", "prod", "ci", "all"],
            required=True,
            help="Mode to run in"
        )
        parser.add_argument(
            "--config",
            type=str,
            required=True,
            help="Path to configuration file"
        )
        parser.add_argument(
            "--domains",
            type=str,
            required=True,
            help="Comma-separated list of domains to run"
        )
        parser.add_argument(
            "--files",
            type=str,
            required=True,
            help="Comma-separated list of files to run"
        )
        parser.add_argument(
            "--options",
            type=str,
            required=True,
            help="Comma-separated list of options to use in key=value format"
        )
        parser.add_argument(
            "--output",
            type=str,
            required=True,
            help="Path to output file"
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["json", "yaml", "csv"],
            required=True,
            help="Format of output file"
        )
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["debug", "info", "warning", "error", "critical"],
            required=True,
            help="Level of logging"
        )
        parser.add_argument(
            "--log-file",
            type=str,
            required=True,
            help="Path to log file"
        )
        parser.add_argument(
            "--log-format",
            type=str,
            required=True,
            help="Format of log file"
        )
        parser.add_argument(
            "--log-max-bytes",
            type=int,
            required=True,
            help="Maximum number of bytes per log file"
        )
        parser.add_argument(
            "--log-backup-count",
            type=int,
            required=True,
            help="Number of backup log files to keep"
        )
        parser.add_argument(
            "--log-compress",
            action="store_true",
            help="Whether to compress backup log files"
        )
        parser.add_argument(
            "--log-encoding",
            type=str,
            required=True,
            help="Encoding to use for log files"
        )
        parser.add_argument(
            "--log-mode",
            type=str,
            choices=["w", "a"],
            required=True,
            help="Mode to open log files in"
        )
        parser.add_argument(
            "--log-delay",
            action="store_true",
            help="Whether to delay opening log files"
        )
        parser.add_argument(
            "--log-buffering",
            type=int,
            default=-1,
            help="Buffering policy (-1 for system default, 0 for unbuffered, >0 for buffer size)"
        )
        parser.add_argument(
            "--log-filters",
            type=str,
            help="Comma-separated list of filters to apply"
        )
        parser.add_argument(
            "--syslog-host",
            type=str,
            help="Syslog host"
        )
        parser.add_argument(
            "--syslog-port",
            type=int,
            default=514,
            help="Syslog port"
        )
        parser.add_argument(
            "--syslog-facility",
            type=str,
            default="user",
            help="Syslog facility"
        )
        parser.add_argument(
            "--smtp-host",
            type=str,
            help="SMTP host"
        )
        parser.add_argument(
            "--smtp-port",
            type=int,
            default=25,
            help="SMTP port"
        )
        parser.add_argument(
            "--smtp-from",
            type=str,
            help="SMTP from address"
        )
        parser.add_argument(
            "--smtp-to",
            type=str,
            help="Comma-separated list of SMTP to addresses"
        )
        parser.add_argument(
            "--smtp-subject",
            type=str,
            help="SMTP subject"
        )
        parser.add_argument(
            "--smtp-user",
            type=str,
            help="SMTP user"
        )
        parser.add_argument(
            "--smtp-password",
            type=str,
            help="SMTP password"
        )
        parser.add_argument(
            "--smtp-secure",
            action="store_true",
            help="Whether to use secure SMTP"
        )
        parser.add_argument(
            "--http-host",
            type=str,
            help="HTTP host"
        )
        parser.add_argument(
            "--http-url",
            type=str,
            help="HTTP URL"
        )
        parser.add_argument(
            "--http-method",
            type=str,
            choices=["GET", "POST"],
            default="POST",
            help="HTTP method"
        )
        parser.add_argument(
            "--http-secure",
            action="store_true",
            help="Whether to use secure HTTP"
        )
        parser.add_argument(
            "--stdout",
            action="store_true",
            help="Whether to log to stdout"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging"
        )
        parser.add_argument(
            "--trace",
            action="store_true",
            help="Enable trace logging"
        )
        args = parser.parse_args()

        # Get log filters
        log_filters = args.log_filters.split(",") if args.log_filters else None

        # Get log formatter
        log_formatter = LogFormatter(args.log_format)

        # Get log handlers
        log_handlers = get_log_handlers(args, log_filters, log_formatter)

        # Set up logging
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper()),
            handlers=log_handlers
        )

        # Get domains and files
        domains = args.domains.split(",")
        files = args.files.split(",")

        # Get options
        options = {}
        for option in args.options.split(","):
            key, value = option.split("=")
            options[key] = value

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run in specific mode with specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file and specific log format and specific log rotation and specific log compression and specific log encoding and specific log mode and specific log delay and specific log buffering and specific log filters and specific log handlers and specific log formatters
        global runner
        runner = DomainFileOptionOutputFormatLogFileFormatRotationCompressionEncodingModeDelayBufferingFiltersHandlersFormattersRunner(args.mode, args.config, domains, files, options, args.output, args.format, args.log_level, args.log_file, args.log_format, args.log_max_bytes, args.log_backup_count, args.log_compress, args.log_encoding, args.log_mode, args.log_delay, args.log_buffering, log_filters, log_handlers, log_formatter)
        asyncio.run(runner.run(
            verbose=args.verbose,
            trace=args.trace
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()
