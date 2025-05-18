"""
File locking utility for safe concurrent file access.
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class FileLockError(Exception):
    """File lock error."""
    pass

class FileLock:
    """Asynchronous file lock implementation."""

    def __init__(
        self,
        file_path: str,
        timeout: int = 30,
        check_interval: float = 0.1
    ):
        """Initialize file lock.

        Args:
            file_path: Path to file
            timeout: Lock timeout in seconds
            check_interval: Lock check interval in seconds
        """
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.parent / f".{self.file_path.name}.lock"
        self.timeout = timeout
        self.check_interval = check_interval
        self._locked = False

    async def acquire(self) -> None:
        """Acquire file lock."""
        try:
            start_time = datetime.now()

            while True:
                try:
                    # Try to create lock file
                    self.lock_path.parent.mkdir(parents=True, exist_ok=True)

                    # Open with exclusive creation
                    fd = os.open(
                        str(self.lock_path),
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY
                    )

                    # Write process info
                    with os.fdopen(fd, 'w') as f:
                        f.write(f"{os.getpid()}\n{datetime.now().isoformat()}")

                    self._locked = True
                    logger.debug(f"Acquired lock for {self.file_path}")
                    return

                except FileExistsError:
                    # Check timeout
                    if (datetime.now() - start_time).total_seconds() > self.timeout:
                        raise FileLockError(
                            f"Timeout waiting for lock on {self.file_path}"
                        )

                    # Check if lock is stale
                    if await self._is_stale_lock():
                        await self._break_lock()
                        continue

                    # Wait and retry
                    await asyncio.sleep(self.check_interval)

        except Exception as e:
            logger.error(f"Error acquiring lock for {self.file_path}: {e}")
            raise

    async def release(self) -> None:
        """Release file lock."""
        try:
            if self._locked:
                try:
                    self.lock_path.unlink()
                    self._locked = False
                    logger.debug(f"Released lock for {self.file_path}")

                except FileNotFoundError:
                    # Lock file already gone
                    self._locked = False
                    logger.warning(
                        f"Lock file missing on release for {self.file_path}"
                    )

        except Exception as e:
            logger.error(f"Error releasing lock for {self.file_path}: {e}")
            raise

    async def _is_stale_lock(self) -> bool:
        """Check if lock file is stale.

        Returns:
            True if lock is stale
        """
        try:
            if not self.lock_path.exists():
                return False

            # Read lock info
            with open(self.lock_path) as f:
                try:
                    pid = int(f.readline().strip())
                    timestamp = datetime.fromisoformat(f.readline().strip())
                except (ValueError, TypeError):
                    # Invalid lock file
                    return True

            # Check process
            try:
                os.kill(pid, 0)
            except OSError:
                # Process not running
                return True

            # Check timeout
            if (datetime.now() - timestamp).total_seconds() > self.timeout:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking stale lock for {self.file_path}: {e}")
            return False

    async def _break_lock(self) -> None:
        """Break stale lock file."""
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
                logger.warning(f"Broke stale lock for {self.file_path}")

        except Exception as e:
            logger.error(f"Error breaking lock for {self.file_path}: {e}")
            raise

    async def __aenter__(self) -> 'FileLock':
        """Enter async context manager."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.release()

    def __del__(self) -> None:
        """Clean up lock file on deletion."""
        try:
            if self._locked and self.lock_path.exists():
                self.lock_path.unlink()
        except Exception:
            pass
