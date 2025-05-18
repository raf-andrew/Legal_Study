import shutil
from log import logger

class VersionTracker:
    def flush_reports(self):
        """Clear all version history and reports."""
        if self.base_dir.exists():
            # Remove all version directories
            for version_dir in self.base_dir.glob("v*"):
                if version_dir.is_dir():
                    shutil.rmtree(version_dir)

            # Remove all iteration directories
            for iteration_dir in self.base_dir.glob("iteration_*"):
                if iteration_dir.is_dir():
                    shutil.rmtree(iteration_dir)

            # Remove all report files
            for report_file in self.base_dir.glob("*.html"):
                if report_file.is_file():
                    report_file.unlink()

            # Remove all JSON files
            for json_file in self.base_dir.glob("*.json"):
                if json_file.is_file():
                    json_file.unlink()

            # Remove all screenshots
            if self.screenshots_dir.exists():
                shutil.rmtree(self.screenshots_dir)
                self.screenshots_dir.mkdir(parents=True)

            logger.info("All version history and reports cleared")
        else:
            logger.info("No version history to clear")
