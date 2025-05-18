# Job Management System

## Metadata
- **Prompt ID**: `JM-001`
- **Job Type**: `System Management`
- **Created**: `2024-03-20`
- **Last Updated**: `2024-03-20`
- **Version**: `1.0.0`

## Purpose
This prompt guides the creation, tracking, and management of all jobs within the Legal Study system, ensuring proper organization, execution, and quality assurance.

## Context
All jobs must be properly categorized, tracked, and associated with appropriate prompts and QA checklists. Each job should have clear requirements, deliverables, and quality standards.

## Input Requirements
- Required fields:
  - Job ID (following format: [TYPE]-[NUMBER])
  - Job Type
  - Creation Date
  - Status
  - Priority
  - Required Prompts
  - Required QA Checklists
  - Deliverables
  - Dependencies
- Optional fields:
  - Estimated Duration
  - Assigned To
  - Notes
  - Version History

## Output Specifications
- Format: Markdown
- Required sections:
  - Job Information
  - Requirements
  - Deliverables
  - Dependencies
  - Status Tracking
  - Quality Assurance
  - Notes
  - Version History
- Quality criteria:
  - Clear job description
  - Comprehensive requirements
  - Defined deliverables
  - Proper tracking
  - Quality standards met

## Quality Assurance
- [ ] Job ID follows format
- [ ] All required fields present
- [ ] Requirements clear
- [ ] Deliverables defined
- [ ] Dependencies identified
- [ ] Status tracking implemented
- [ ] Associated prompts identified
- [ ] QA checklists assigned

## Notes
- All jobs must be stored in appropriate subdirectories
- Each job must have associated prompts and QA checklists
- Status must be regularly updated
- Dependencies must be tracked
- Regular review and updates required

## Version History
- 1.0.0: Initial version 