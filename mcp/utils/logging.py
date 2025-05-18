"""
MCP logging utilities.
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Any, Dict

def setup_logger(
    logger: logging.Logger,
    config: Dict[str, Any],
    name: str
) -> None:
    """Set up logger with configuration.

    Args:
        logger: Logger to configure
        config: Logging configuration
        name: Logger name

    Raises:
        ValueError: If configuration is invalid
    """
    try:
        # Get configuration
        log_level = config.get("level", "INFO")
        log_format = config.get("format")
        log_file = config.get("file")

        # Set log level
        logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Add file handler
        if log_file:
            # Create log directory
            log_path = Path(log_file).parent
            log_path.mkdir(parents=True, exist_ok=True)

            # Create handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file.format(name=name),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    except Exception as e:
        raise ValueError(f"Error setting up logger: {e}")

def log_error(
    logger: logging.Logger,
    error: Exception,
    message: str = None
) -> None:
    """Log error with traceback.

    Args:
        logger: Logger to use
        error: Error to log
        message: Optional message to include
    """
    try:
        if message:
            logger.error(f"{message}: {error}", exc_info=True)
        else:
            logger.error(str(error), exc_info=True)

    except Exception as e:
        logger.error(f"Error logging error: {e}")

def log_warning(
    logger: logging.Logger,
    warning: str,
    details: Dict[str, Any] = None
) -> None:
    """Log warning with details.

    Args:
        logger: Logger to use
        warning: Warning message
        details: Optional warning details
    """
    try:
        if details:
            logger.warning(f"{warning}: {details}")
        else:
            logger.warning(warning)

    except Exception as e:
        logger.error(f"Error logging warning: {e}")

def log_info(
    logger: logging.Logger,
    message: str,
    details: Dict[str, Any] = None
) -> None:
    """Log info message with details.

    Args:
        logger: Logger to use
        message: Info message
        details: Optional message details
    """
    try:
        if details:
            logger.info(f"{message}: {details}")
        else:
            logger.info(message)

    except Exception as e:
        logger.error(f"Error logging info: {e}")

def log_debug(
    logger: logging.Logger,
    message: str,
    details: Dict[str, Any] = None
) -> None:
    """Log debug message with details.

    Args:
        logger: Logger to use
        message: Debug message
        details: Optional message details
    """
    try:
        if details:
            logger.debug(f"{message}: {details}")
        else:
            logger.debug(message)

    except Exception as e:
        logger.error(f"Error logging debug: {e}")

def log_metrics(
    logger: logging.Logger,
    metrics: Dict[str, Any]
) -> None:
    """Log metrics.

    Args:
        logger: Logger to use
        metrics: Metrics to log
    """
    try:
        logger.info("Metrics:", extra={"metrics": metrics})

    except Exception as e:
        logger.error(f"Error logging metrics: {e}")

def log_health(
    logger: logging.Logger,
    health: Dict[str, Any]
) -> None:
    """Log health status.

    Args:
        logger: Logger to use
        health: Health status to log
    """
    try:
        logger.info("Health status:", extra={"health": health})

    except Exception as e:
        logger.error(f"Error logging health: {e}")

def log_report(
    logger: logging.Logger,
    report: Dict[str, Any]
) -> None:
    """Log report.

    Args:
        logger: Logger to use
        report: Report to log
    """
    try:
        logger.info("Report:", extra={"report": report})

    except Exception as e:
        logger.error(f"Error logging report: {e}")

def log_coverage(
    logger: logging.Logger,
    coverage: Dict[str, Any]
) -> None:
    """Log coverage.

    Args:
        logger: Logger to use
        coverage: Coverage to log
    """
    try:
        logger.info("Coverage:", extra={"coverage": coverage})

    except Exception as e:
        logger.error(f"Error logging coverage: {e}")

def log_issues(
    logger: logging.Logger,
    issues: Dict[str, Any]
) -> None:
    """Log issues.

    Args:
        logger: Logger to use
        issues: Issues to log
    """
    try:
        logger.info("Issues:", extra={"issues": issues})

    except Exception as e:
        logger.error(f"Error logging issues: {e}")

def log_fixes(
    logger: logging.Logger,
    fixes: Dict[str, Any]
) -> None:
    """Log fixes.

    Args:
        logger: Logger to use
        fixes: Fixes to log
    """
    try:
        logger.info("Fixes:", extra={"fixes": fixes})

    except Exception as e:
        logger.error(f"Error logging fixes: {e}")

def log_analysis(
    logger: logging.Logger,
    analysis: Dict[str, Any]
) -> None:
    """Log analysis.

    Args:
        logger: Logger to use
        analysis: Analysis to log
    """
    try:
        logger.info("Analysis:", extra={"analysis": analysis})

    except Exception as e:
        logger.error(f"Error logging analysis: {e}")

def log_test(
    logger: logging.Logger,
    test: Dict[str, Any]
) -> None:
    """Log test.

    Args:
        logger: Logger to use
        test: Test to log
    """
    try:
        logger.info("Test:", extra={"test": test})

    except Exception as e:
        logger.error(f"Error logging test: {e}")

def log_validation(
    logger: logging.Logger,
    validation: Dict[str, Any]
) -> None:
    """Log validation.

    Args:
        logger: Logger to use
        validation: Validation to log
    """
    try:
        logger.info("Validation:", extra={"validation": validation})

    except Exception as e:
        logger.error(f"Error logging validation: {e}")

def log_compliance(
    logger: logging.Logger,
    compliance: Dict[str, Any]
) -> None:
    """Log compliance.

    Args:
        logger: Logger to use
        compliance: Compliance to log
    """
    try:
        logger.info("Compliance:", extra={"compliance": compliance})

    except Exception as e:
        logger.error(f"Error logging compliance: {e}")

def log_security(
    logger: logging.Logger,
    security: Dict[str, Any]
) -> None:
    """Log security.

    Args:
        logger: Logger to use
        security: Security to log
    """
    try:
        logger.info("Security:", extra={"security": security})

    except Exception as e:
        logger.error(f"Error logging security: {e}")

def log_performance(
    logger: logging.Logger,
    performance: Dict[str, Any]
) -> None:
    """Log performance.

    Args:
        logger: Logger to use
        performance: Performance to log
    """
    try:
        logger.info("Performance:", extra={"performance": performance})

    except Exception as e:
        logger.error(f"Error logging performance: {e}")

def log_documentation(
    logger: logging.Logger,
    documentation: Dict[str, Any]
) -> None:
    """Log documentation.

    Args:
        logger: Logger to use
        documentation: Documentation to log
    """
    try:
        logger.info("Documentation:", extra={"documentation": documentation})

    except Exception as e:
        logger.error(f"Error logging documentation: {e}")

def log_browser(
    logger: logging.Logger,
    browser: Dict[str, Any]
) -> None:
    """Log browser.

    Args:
        logger: Logger to use
        browser: Browser to log
    """
    try:
        logger.info("Browser:", extra={"browser": browser})

    except Exception as e:
        logger.error(f"Error logging browser: {e}")

def log_functional(
    logger: logging.Logger,
    functional: Dict[str, Any]
) -> None:
    """Log functional.

    Args:
        logger: Logger to use
        functional: Functional to log
    """
    try:
        logger.info("Functional:", extra={"functional": functional})

    except Exception as e:
        logger.error(f"Error logging functional: {e}")

def log_unit(
    logger: logging.Logger,
    unit: Dict[str, Any]
) -> None:
    """Log unit.

    Args:
        logger: Logger to use
        unit: Unit to log
    """
    try:
        logger.info("Unit:", extra={"unit": unit})

    except Exception as e:
        logger.error(f"Error logging unit: {e}")

def log_integration(
    logger: logging.Logger,
    integration: Dict[str, Any]
) -> None:
    """Log integration.

    Args:
        logger: Logger to use
        integration: Integration to log
    """
    try:
        logger.info("Integration:", extra={"integration": integration})

    except Exception as e:
        logger.error(f"Error logging integration: {e}")

def log_api(
    logger: logging.Logger,
    api: Dict[str, Any]
) -> None:
    """Log API.

    Args:
        logger: Logger to use
        api: API to log
    """
    try:
        logger.info("API:", extra={"api": api})

    except Exception as e:
        logger.error(f"Error logging API: {e}")

def log_git(
    logger: logging.Logger,
    git: Dict[str, Any]
) -> None:
    """Log git.

    Args:
        logger: Logger to use
        git: Git to log
    """
    try:
        logger.info("Git:", extra={"git": git})

    except Exception as e:
        logger.error(f"Error logging git: {e}")

def log_ci(
    logger: logging.Logger,
    ci: Dict[str, Any]
) -> None:
    """Log CI.

    Args:
        logger: Logger to use
        ci: CI to log
    """
    try:
        logger.info("CI:", extra={"ci": ci})

    except Exception as e:
        logger.error(f"Error logging CI: {e}")

def log_cd(
    logger: logging.Logger,
    cd: Dict[str, Any]
) -> None:
    """Log CD.

    Args:
        logger: Logger to use
        cd: CD to log
    """
    try:
        logger.info("CD:", extra={"cd": cd})

    except Exception as e:
        logger.error(f"Error logging CD: {e}")

def log_deployment(
    logger: logging.Logger,
    deployment: Dict[str, Any]
) -> None:
    """Log deployment.

    Args:
        logger: Logger to use
        deployment: Deployment to log
    """
    try:
        logger.info("Deployment:", extra={"deployment": deployment})

    except Exception as e:
        logger.error(f"Error logging deployment: {e}")

def log_monitoring(
    logger: logging.Logger,
    monitoring: Dict[str, Any]
) -> None:
    """Log monitoring.

    Args:
        logger: Logger to use
        monitoring: Monitoring to log
    """
    try:
        logger.info("Monitoring:", extra={"monitoring": monitoring})

    except Exception as e:
        logger.error(f"Error logging monitoring: {e}")

def log_alerting(
    logger: logging.Logger,
    alerting: Dict[str, Any]
) -> None:
    """Log alerting.

    Args:
        logger: Logger to use
        alerting: Alerting to log
    """
    try:
        logger.info("Alerting:", extra={"alerting": alerting})

    except Exception as e:
        logger.error(f"Error logging alerting: {e}")

def log_dashboard(
    logger: logging.Logger,
    dashboard: Dict[str, Any]
) -> None:
    """Log dashboard.

    Args:
        logger: Logger to use
        dashboard: Dashboard to log
    """
    try:
        logger.info("Dashboard:", extra={"dashboard": dashboard})

    except Exception as e:
        logger.error(f"Error logging dashboard: {e}")

def log_report_generation(
    logger: logging.Logger,
    report_generation: Dict[str, Any]
) -> None:
    """Log report generation.

    Args:
        logger: Logger to use
        report_generation: Report generation to log
    """
    try:
        logger.info("Report generation:", extra={"report_generation": report_generation})

    except Exception as e:
        logger.error(f"Error logging report generation: {e}")

def log_report_analysis(
    logger: logging.Logger,
    report_analysis: Dict[str, Any]
) -> None:
    """Log report analysis.

    Args:
        logger: Logger to use
        report_analysis: Report analysis to log
    """
    try:
        logger.info("Report analysis:", extra={"report_analysis": report_analysis})

    except Exception as e:
        logger.error(f"Error logging report analysis: {e}")

def log_report_validation(
    logger: logging.Logger,
    report_validation: Dict[str, Any]
) -> None:
    """Log report validation.

    Args:
        logger: Logger to use
        report_validation: Report validation to log
    """
    try:
        logger.info("Report validation:", extra={"report_validation": report_validation})

    except Exception as e:
        logger.error(f"Error logging report validation: {e}")

def log_report_compliance(
    logger: logging.Logger,
    report_compliance: Dict[str, Any]
) -> None:
    """Log report compliance.

    Args:
        logger: Logger to use
        report_compliance: Report compliance to log
    """
    try:
        logger.info("Report compliance:", extra={"report_compliance": report_compliance})

    except Exception as e:
        logger.error(f"Error logging report compliance: {e}")

def log_report_security(
    logger: logging.Logger,
    report_security: Dict[str, Any]
) -> None:
    """Log report security.

    Args:
        logger: Logger to use
        report_security: Report security to log
    """
    try:
        logger.info("Report security:", extra={"report_security": report_security})

    except Exception as e:
        logger.error(f"Error logging report security: {e}")

def log_report_performance(
    logger: logging.Logger,
    report_performance: Dict[str, Any]
) -> None:
    """Log report performance.

    Args:
        logger: Logger to use
        report_performance: Report performance to log
    """
    try:
        logger.info("Report performance:", extra={"report_performance": report_performance})

    except Exception as e:
        logger.error(f"Error logging report performance: {e}")

def log_report_documentation(
    logger: logging.Logger,
    report_documentation: Dict[str, Any]
) -> None:
    """Log report documentation.

    Args:
        logger: Logger to use
        report_documentation: Report documentation to log
    """
    try:
        logger.info("Report documentation:", extra={"report_documentation": report_documentation})

    except Exception as e:
        logger.error(f"Error logging report documentation: {e}")

def log_report_browser(
    logger: logging.Logger,
    report_browser: Dict[str, Any]
) -> None:
    """Log report browser.

    Args:
        logger: Logger to use
        report_browser: Report browser to log
    """
    try:
        logger.info("Report browser:", extra={"report_browser": report_browser})

    except Exception as e:
        logger.error(f"Error logging report browser: {e}")

def log_report_functional(
    logger: logging.Logger,
    report_functional: Dict[str, Any]
) -> None:
    """Log report functional.

    Args:
        logger: Logger to use
        report_functional: Report functional to log
    """
    try:
        logger.info("Report functional:", extra={"report_functional": report_functional})

    except Exception as e:
        logger.error(f"Error logging report functional: {e}")

def log_report_unit(
    logger: logging.Logger,
    report_unit: Dict[str, Any]
) -> None:
    """Log report unit.

    Args:
        logger: Logger to use
        report_unit: Report unit to log
    """
    try:
        logger.info("Report unit:", extra={"report_unit": report_unit})

    except Exception as e:
        logger.error(f"Error logging report unit: {e}")

def log_report_integration(
    logger: logging.Logger,
    report_integration: Dict[str, Any]
) -> None:
    """Log report integration.

    Args:
        logger: Logger to use
        report_integration: Report integration to log
    """
    try:
        logger.info("Report integration:", extra={"report_integration": report_integration})

    except Exception as e:
        logger.error(f"Error logging report integration: {e}")

def log_report_api(
    logger: logging.Logger,
    report_api: Dict[str, Any]
) -> None:
    """Log report API.

    Args:
        logger: Logger to use
        report_api: Report API to log
    """
    try:
        logger.info("Report API:", extra={"report_api": report_api})

    except Exception as e:
        logger.error(f"Error logging report API: {e}")

def log_report_git(
    logger: logging.Logger,
    report_git: Dict[str, Any]
) -> None:
    """Log report git.

    Args:
        logger: Logger to use
        report_git: Report git to log
    """
    try:
        logger.info("Report git:", extra={"report_git": report_git})

    except Exception as e:
        logger.error(f"Error logging report git: {e}")

def log_report_ci(
    logger: logging.Logger,
    report_ci: Dict[str, Any]
) -> None:
    """Log report CI.

    Args:
        logger: Logger to use
        report_ci: Report CI to log
    """
    try:
        logger.info("Report CI:", extra={"report_ci": report_ci})

    except Exception as e:
        logger.error(f"Error logging report CI: {e}")

def log_report_cd(
    logger: logging.Logger,
    report_cd: Dict[str, Any]
) -> None:
    """Log report CD.

    Args:
        logger: Logger to use
        report_cd: Report CD to log
    """
    try:
        logger.info("Report CD:", extra={"report_cd": report_cd})

    except Exception as e:
        logger.error(f"Error logging report CD: {e}")

def log_report_deployment(
    logger: logging.Logger,
    report_deployment: Dict[str, Any]
) -> None:
    """Log report deployment.

    Args:
        logger: Logger to use
        report_deployment: Report deployment to log
    """
    try:
        logger.info("Report deployment:", extra={"report_deployment": report_deployment})

    except Exception as e:
        logger.error(f"Error logging report deployment: {e}")

def log_report_monitoring(
    logger: logging.Logger,
    report_monitoring: Dict[str, Any]
) -> None:
    """Log report monitoring.

    Args:
        logger: Logger to use
        report_monitoring: Report monitoring to log
    """
    try:
        logger.info("Report monitoring:", extra={"report_monitoring": report_monitoring})

    except Exception as e:
        logger.error(f"Error logging report monitoring: {e}")

def log_report_alerting(
    logger: logging.Logger,
    report_alerting: Dict[str, Any]
) -> None:
    """Log report alerting.

    Args:
        logger: Logger to use
        report_alerting: Report alerting to log
    """
    try:
        logger.info("Report alerting:", extra={"report_alerting": report_alerting})

    except Exception as e:
        logger.error(f"Error logging report alerting: {e}")

def log_report_dashboard(
    logger: logging.Logger,
    report_dashboard: Dict[str, Any]
) -> None:
    """Log report dashboard.

    Args:
        logger: Logger to use
        report_dashboard: Report dashboard to log
    """
    try:
        logger.info("Report dashboard:", extra={"report_dashboard": report_dashboard})

    except Exception as e:
        logger.error(f"Error logging report dashboard: {e}")
