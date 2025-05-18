#!/usr/bin/env python3

import sys
import time
from pathlib import Path
import argparse
import logging

def setup_logging():
    """Setup logging for the tail script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def tail_log(log_file: Path, follow: bool = True, lines: int = 10):
    """Tail a log file."""
    logger = setup_logging()

    if not log_file.exists():
        logger.error(f"Log file not found: {log_file}")
        return

    try:
        with log_file.open() as f:
            # Read last N lines
            lines_list = f.readlines()
            for line in lines_list[-lines:]:
                print(line, end='')

            if follow:
                # Go to end of file
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    print(line, end='')
    except KeyboardInterrupt:
        logger.info("Stopping log tail...")
    except Exception as e:
        logger.error(f"Error tailing log: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Tail service logs')
    parser.add_argument('--service', type=str, choices=['mysql', 'redis', 'all'],
                      help='Service to tail logs for')
    parser.add_argument('--lines', type=int, default=10,
                      help='Number of lines to show initially')
    parser.add_argument('--no-follow', action='store_true',
                      help='Do not follow log updates')
    args = parser.parse_args()

    base_dir = Path('.')
    logs_dir = base_dir / '.setup' / 'logs'

    if args.service == 'all':
        # Tail all service logs
        for service in ['mysql', 'redis']:
            log_file = logs_dir / f'{service}_service.log'
            if log_file.exists():
                print(f"\n=== {service.upper()} Service Log ===")
                tail_log(log_file, not args.no_follow, args.lines)
    else:
        # Tail specific service log
        log_file = logs_dir / f'{args.service}_service.log'
        tail_log(log_file, not args.no_follow, args.lines)

if __name__ == '__main__':
    main()
