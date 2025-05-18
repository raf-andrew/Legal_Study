#!/usr/bin/env python3

import argparse
import json
import os
import shutil
from datetime import datetime

def load_verification_report(verification_file):
    """Load and validate verification report."""
    with open(verification_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    required_fields = ['verification_status', 'requirements_met', 'test_results', 'coverage_data']
    if not all(field in report for field in required_fields):
        raise ValueError("Invalid verification report format")

    return report

def load_checklist_items(checklist_dir, test_suite):
    """Load checklist items for the specified test suite."""
    checklist_file = os.path.join(checklist_dir, f"{test_suite}_checklist.json")

    if not os.path.exists(checklist_file):
        return []

    with open(checklist_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_checklist_item(item, verification_report):
    """Verify if a checklist item meets all requirements."""
    requirements = item.get('requirements', {})

    # Check test coverage requirement
    if requirements.get('min_coverage'):
        if verification_report['coverage_data']['line_coverage'] < requirements['min_coverage']:
            return False

    # Check test pass rate requirement
    if requirements.get('min_pass_rate'):
        if verification_report['test_results']['pass_rate'] < requirements['min_pass_rate']:
            return False

    # Check for any failed tests
    if verification_report['test_results']['failed'] > 0:
        return False

    # Check for skipped tests
    if requirements.get('no_skipped_tests', True):
        if verification_report['test_results']['skipped'] > 0:
            return False

    return True

def move_to_complete(item, complete_dir, verification_report):
    """Move verified item to .complete directory with proof."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    item_id = item['id']

    # Create completion record
    completion_record = {
        'item_id': item_id,
        'timestamp': timestamp,
        'verification_report': verification_report,
        'status': 'completed'
    }

    # Create completion directory if it doesn't exist
    os.makedirs(complete_dir, exist_ok=True)

    # Write completion record
    completion_file = os.path.join(complete_dir, f"{item_id}_complete_{timestamp}.json")
    with open(completion_file, 'w', encoding='utf-8') as f:
        json.dump(completion_record, f, indent=2)

    return completion_file

def main():
    parser = argparse.ArgumentParser(description='Verify checklist items against test results')
    parser.add_argument('--verification-file', required=True, help='Path to verification report')
    parser.add_argument('--checklist-dir', required=True, help='Directory containing checklist files')
    parser.add_argument('--complete-dir', required=True, help='Directory for completed items')
    parser.add_argument('--test-suite', required=True, help='Test suite being verified')

    args = parser.parse_args()

    try:
        # Load verification report
        verification_report = load_verification_report(args.verification_file)

        # Load checklist items
        checklist_items = load_checklist_items(args.checklist_dir, args.test_suite)

        if not checklist_items:
            print(f"No checklist items found for {args.test_suite}")
            return

        # Verify each checklist item
        verified_items = []
        for item in checklist_items:
            if verify_checklist_item(item, verification_report):
                completion_file = move_to_complete(item, args.complete_dir, verification_report)
                verified_items.append({
                    'item_id': item['id'],
                    'completion_file': completion_file
                })

        # Print summary
        print(f"\nChecklist Verification Summary for {args.test_suite}:")
        print(f"Total items: {len(checklist_items)}")
        print(f"Verified items: {len(verified_items)}")

        if verified_items:
            print("\nVerified items:")
            for item in verified_items:
                print(f"- {item['item_id']} -> {item['completion_file']}")

    except Exception as e:
        print(f"Error verifying checklist: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
