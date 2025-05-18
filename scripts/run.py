"""
Main run script for sniffing infrastructure.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run")

def main() -> int:
    """Main entry point for running sniffing infrastructure."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Run infrastructure
        asyncio.run(run_infrastructure(config))

        return 0

    except Exception as e:
        logger.error(f"Error running infrastructure: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

async def run_infrastructure(config: Dict[str, Any]) -> None:
    """Run sniffing infrastructure."""
    try:
        # Start MCP server
        mcp_server = MCPServer(config.get("mcp", {}))
        await mcp_server.start()

        # Start API server
        await start_api_server(config)

        # Start monitoring
        await start_monitoring(config)

        # Start background tasks
        await start_background_tasks(config)

        # Wait for shutdown
        await wait_for_shutdown()

    except Exception as e:
        logger.error(f"Error running infrastructure: {e}")
        raise

async def start_api_server(config: Dict[str, Any]) -> None:
    """Start API server."""
    try:
        from fastapi import FastAPI
        from uvicorn import Config, Server

        # Create FastAPI application
        app = FastAPI(
            title="Sniffing API",
            description="API for sniffing infrastructure",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Add routes
        from sniffing.api.routes import (
            health_routes,
            sniffing_routes,
            monitoring_routes,
            analysis_routes
        )

        app.include_router(health_routes.router, prefix="/health", tags=["health"])
        app.include_router(sniffing_routes.router, prefix="/sniffing", tags=["sniffing"])
        app.include_router(monitoring_routes.router, prefix="/monitoring", tags=["monitoring"])
        app.include_router(analysis_routes.router, prefix="/analysis", tags=["analysis"])

        # Start server
        server_config = Config(
            app=app,
            host=config.get("host", "localhost"),
            port=config.get("port", 8000),
            workers=config.get("workers", 4),
            timeout_keep_alive=config.get("timeout", 300),
            log_level=config.get("log_level", "info")
        )
        server = Server(server_config)

        # Run server in background
        asyncio.create_task(server.serve())
        logger.info("API server started")

    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        raise

async def start_monitoring(config: Dict[str, Any]) -> None:
    """Start monitoring system."""
    try:
        from prometheus_client import start_http_server

        # Start Prometheus server
        port = config.get("monitoring", {}).get("prometheus_port", 9090)
        start_http_server(port)
        logger.info("Monitoring system started")

    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise

async def start_background_tasks(config: Dict[str, Any]) -> None:
    """Start background tasks."""
    try:
        tasks = []

        # Add metric collection task
        if config.get("monitoring", {}).get("enabled", False):
            tasks.append(collect_metrics(config))

        # Add health check task
        if config.get("monitoring", {}).get("health_checks", {}).get("enabled", False):
            tasks.append(run_health_checks(config))

        # Add cleanup task
        tasks.append(run_cleanup(config))

        # Start all tasks
        for task in tasks:
            asyncio.create_task(task)

        logger.info("Background tasks started")

    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")
        raise

async def collect_metrics(config: Dict[str, Any]) -> None:
    """Collect system metrics."""
    try:
        interval = config.get("monitoring", {}).get("metrics", {}).get("collection_interval", 60)

        while True:
            try:
                # Collect system metrics
                import psutil
                metrics = {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent
                }

                # Save metrics
                metrics_path = Path(config.get("storage", {}).get("metrics_path", "metrics"))
                metrics_file = metrics_path / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                with open(metrics_file, "w") as f:
                    json.dump(metrics, f)

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(interval)

    except Exception as e:
        logger.error(f"Error in metric collection task: {e}")
        raise

async def run_health_checks(config: Dict[str, Any]) -> None:
    """Run system health checks."""
    try:
        interval = config.get("monitoring", {}).get("health_checks", {}).get("interval", 300)

        while True:
            try:
                # Check system health
                health_status = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "healthy",
                    "checks": {
                        "api": await check_api_health(),
                        "database": await check_database_health(),
                        "monitoring": await check_monitoring_health()
                    }
                }

                # Update status
                if any(not check["status"] for check in health_status["checks"].values()):
                    health_status["status"] = "unhealthy"

                # Save health status
                health_path = Path(config.get("storage", {}).get("health_path", "health"))
                health_file = health_path / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                with open(health_file, "w") as f:
                    json.dump(health_status, f)

                # Send alerts if unhealthy
                if health_status["status"] == "unhealthy":
                    await send_alerts(health_status)

            except Exception as e:
                logger.error(f"Error running health checks: {e}")

            await asyncio.sleep(interval)

    except Exception as e:
        logger.error(f"Error in health check task: {e}")
        raise

async def run_cleanup(config: Dict[str, Any]) -> None:
    """Run cleanup tasks."""
    try:
        retention_days = config.get("storage", {}).get("retention_days", 30)
        cutoff = datetime.now() - timedelta(days=retention_days)

        while True:
            try:
                # Clean up old files
                for directory in ["metrics", "alerts", "health", "reports"]:
                    path = Path(config.get("storage", {}).get(f"{directory}_path", directory))
                    for file in path.glob("*.json"):
                        if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                            file.unlink()
                            logger.info(f"Removed old file: {file}")

            except Exception as e:
                logger.error(f"Error running cleanup: {e}")

            await asyncio.sleep(86400)  # Run daily

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise

async def check_api_health() -> Dict[str, Any]:
    """Check API health."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                return {
                    "status": response.status == 200,
                    "response_time": response.elapsed.total_seconds()
                }

    except Exception as e:
        logger.error(f"Error checking API health: {e}")
        return {
            "status": False,
            "error": str(e)
        }

async def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine("sqlite:///dev/database/sniffing.db")

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return {
                "status": True,
                "connected": True
            }

    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return {
            "status": False,
            "error": str(e)
        }

async def check_monitoring_health() -> Dict[str, Any]:
    """Check monitoring health."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9090/-/healthy") as response:
                return {
                    "status": response.status == 200,
                    "response_time": response.elapsed.total_seconds()
                }

    except Exception as e:
        logger.error(f"Error checking monitoring health: {e}")
        return {
            "status": False,
            "error": str(e)
        }

async def send_alerts(health_status: Dict[str, Any]) -> None:
    """Send alerts for unhealthy status."""
    try:
        # Create alert
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": "high",
            "message": f"System health is {health_status['status']}",
            "details": health_status
        }

        # Save alert
        alerts_path = Path("alerts")
        alert_file = alerts_path / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(alert_file, "w") as f:
            json.dump(alert, f)

        # Send through configured channels
        await send_slack_alert(alert)
        await send_email_alert(alert)

    except Exception as e:
        logger.error(f"Error sending alerts: {e}")

async def send_slack_alert(alert: Dict[str, Any]) -> None:
    """Send alert through Slack."""
    try:
        import aiohttp
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={
                "text": f"Alert: {alert['message']}\nSeverity: {alert['severity']}"
            })

    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")

async def send_email_alert(alert: Dict[str, Any]) -> None:
    """Send alert through email."""
    try:
        import aiosmtplib
        from email.message import EmailMessage

        smtp_config = {
            "hostname": os.getenv("SMTP_SERVER"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD")
        }

        if not all(smtp_config.values()):
            return

        # Create message
        msg = EmailMessage()
        msg.set_content(f"Alert: {alert['message']}\nSeverity: {alert['severity']}")
        msg["Subject"] = f"Sniffing Alert: {alert['severity'].upper()}"
        msg["From"] = os.getenv("ALERT_FROM_EMAIL")
        msg["To"] = os.getenv("ALERT_TO_EMAIL")

        # Send email
        await aiosmtplib.send(msg, **smtp_config)

    except Exception as e:
        logger.error(f"Error sending email alert: {e}")

async def wait_for_shutdown() -> None:
    """Wait for shutdown signal."""
    try:
        # Wait for shutdown signal
        shutdown_event = asyncio.Event()
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Error waiting for shutdown: {e}")
        raise

def cleanup() -> None:
    """Clean up resources."""
    try:
        logger.info("Cleaning up resources...")

    except Exception as e:
        logger.error(f"Error cleaning up: {e}")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        cleanup()
        sys.exit(0)
