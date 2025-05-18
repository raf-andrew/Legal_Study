# File Organization Standards

## Overview
This document defines the standardized file naming conventions and directory structure for the state requirements research project.

## File Naming Conventions

### 1. General Rules
```yaml
Format Rules:
  Case:
    - Use lowercase letters
    - Separate words with underscores
    - No spaces in filenames
    - No special characters except - and _

  Structure:
    - category_subcategory_name
    - state_document_type_name
    - date_type_name (for dated documents)

  Extensions:
    - .md for documentation
    - .pdf for external documents
    - .xlsx for spreadsheets
    - .txt for plain text
```

### 2. Specific Patterns
```yaml
Research Documents:
  State Files:
    - state_name_research_notes.md
    - state_name_source_database.md
    - state_name_analysis.md
    - state_name_summary.md

  Templates:
    - template_name_template.md
    - template_name_example.md
    - template_name_guide.md

  Reports:
    - YYYYMMDD_report_name.md
    - YYYYMMDD_state_report.md
    - YYYYMMDD_progress_report.md
```

## Directory Structure

### 1. Root Organization
```yaml
.research/:
  state_requirements/:
    - README.md (master index)
    - templates/ (all templates)
    - analysis/ (comparative analysis)
    - [state_name]/ (state-specific folders)

.qa/:
  - templates/ (quality templates)
  - active/ (active assessments)
  - completed/ (finished reviews)

.errors/:
  - logs/ (error tracking)
  - templates/ (error templates)
  - resolutions/ (resolved issues)

.prompts/:
  - research/ (research prompts)
  - analysis/ (analysis prompts)
  - documentation/ (doc prompts)
```

### 2. State Directory Structure
```yaml
[state_name]/:
  - README.md (state index)
  
  analysis/:
    - requirements_analysis.md
    - program_analysis.md
    - comparison_analysis.md
  
  documentation/:
    - official_requirements.md
    - program_details.md
    - application_process.md
  
  sources/:
    - primary_sources.md
    - secondary_sources.md
    - contact_information.md
```

## Version Control

### 1. Version Naming
```yaml
File Versions:
  Format: filename_v[X.Y].md
  Example: alabama_analysis_v1.0.md
  
  Version Numbers:
    Major: X.0 (significant changes)
    Minor: 0.Y (small updates)
    Draft: v0.Y (pre-release)
```

### 2. Backup System
```yaml
Backup Structure:
  Daily:
    - Location: .backup/daily/
    - Format: YYYYMMDD_filename.md
    - Retention: 7 days

  Weekly:
    - Location: .backup/weekly/
    - Format: YYYYWW_filename.md
    - Retention: 4 weeks

  Monthly:
    - Location: .backup/monthly/
    - Format: YYYYMM_filename.md
    - Retention: 12 months
```

## File Management

### 1. Organization Rules
```yaml
File Placement:
  Research Files:
    - Place in appropriate state folder
    - Use correct subfolder
    - Follow naming convention
    - Include required metadata

  Templates:
    - Store in templates folder
    - Version appropriately
    - Include usage examples
    - Document changes
```

### 2. Maintenance
```yaml
Regular Tasks:
  Daily:
    - Update working files
    - Check naming compliance
    - Verify organization
    - Create backups

  Weekly:
    - Review file structure
    - Clean up temporary files
    - Verify backups
    - Update indexes
```

## Quality Standards

### 1. File Requirements
```yaml
Mandatory Elements:
  All Files:
    - Clear title
    - Creation date
    - Last updated date
    - Version number
    - Author/owner

  Documentation:
    - Purpose statement
    - Related documents
    - Quality status
    - Review history
```

### 2. Organization Quality
```yaml
Quality Metrics:
  Structure:
    - Correct placement
    - Proper naming
    - Clear organization
    - Easy navigation

  Maintenance:
    - Regular updates
    - Proper versioning
    - Complete backups
    - Current documentation
```

## Related Documents
- [Quality Standards](../../../.qa/templates/quality_standards.md)
- [Update Procedures](update_procedures.md)
- [Research Template](state_research_template.md)

## Notes
- Follow conventions strictly
- Maintain organization
- Regular backups required
- Update documentation
- Review regularly 