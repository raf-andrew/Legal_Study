# Legal Study Project Overview

## Project Structure
The Legal Study project is a comprehensive system for self-directed legal education, organized into several key directories:

### Core Directories
1. `.research/` - Primary research and documentation
   - Core legal knowledge
   - State requirements
   - Bar examination materials
   - Practice areas
   - Legal skills
   - Assessments

2. `.jobs/` - Task tracking and execution
   - Active jobs
   - Completed jobs
   - Templates
   - Phase-specific jobs
   - Management

3. `.qa/` - Quality assurance
   - Templates
   - Active reviews
   - Metrics
   - Checklists
   - Reports
   - Management

4. `.prompts/` - AI prompt management
   - Templates
   - Research prompts
   - Analysis prompts
   - QA prompts
   - Study prompts
   - Practice prompts
   - Assessment prompts
   - Management
   - Job-specific prompts

5. `.errors/` - Error tracking
   - Active errors
   - Resolved errors
   - Analysis
   - Prevention

6. `.experiments/` - Research experiments
   - Active experiments
   - Completed experiments
   - Results
   - Methodologies

7. `.tests/` - Practice tests
   - Criminal law
   - Civil law
   - Constitutional law
   - Results
   - Feedback

8. `.completed/` - Completed work
   - Jobs
   - Assessments
   - Certifications
   - Milestones

## File Conventions

### Markdown Files
- Use consistent heading levels
- Line length: 80 characters
- Wrap text: true
- Use proper markdown formatting
- Include metadata where required

### JSON Files
- Indent: 2 spaces
- Use consistent key naming
- Include comments where necessary
- Follow schema validation

### YAML Files
- Indent: 2 spaces
- Use consistent key naming
- Follow schema validation

## Workflow Rules

### Job Management
1. All jobs must have:
   - Unique ID
   - Clear type
   - Status tracking
   - Priority level
   - Associated prompts
   - QA checklist

2. Job Status Flow:
   - Not Started → In Progress → Under Review → Completed
   - Can be set to On Hold or Cancelled

### Prompt Management
1. All prompts must:
   - Follow ID format: [TYPE]-[NUMBER]
   - Include all required sections
   - Have associated QA checklist
   - Be properly categorized

2. Prompt Types:
   - System Management (SM)
   - Job Management (JM)
   - Quality Assurance (QA)
   - Research (RS)
   - Analysis (AN)
   - Study (ST)
   - Practice (PR)
   - Assessment (AS)

### Quality Assurance
1. QA Process:
   - Initial review
   - Technical review
   - Content review
   - Final assessment
   - Sign-off

2. Quality Metrics:
   - Completeness (0-10)
   - Accuracy (0-10)
   - Clarity (0-10)
   - Professionalism (0-10)

## Integration Rules

### File Associations
- `.md` → markdown
- `.json` → json
- `.yaml` → yaml
- `.pdf` → pdf
- `.docx` → word

### Search Rules
- Include: `*.md`, `*.json`, `*.yaml`, `*.pdf`, `*.docx`
- Exclude: `.git`, `node_modules`, `.backup`

### Version Control
- All files must maintain version history
- Version format: `MAJOR.MINOR.PATCH`
- Document changes in version history

## Best Practices

### Documentation
- Keep documentation up to date
- Use clear and concise language
- Include examples where helpful
- Maintain version history

### Organization
- Follow directory structure
- Use appropriate file types
- Maintain consistent naming
- Keep related files together

### Quality Control
- Regular reviews
- Consistent formatting
- Complete documentation
- Proper versioning

## Error Handling

### Error Categories
1. Critical - System-breaking
2. Major - Significant impact
3. Minor - Limited impact
4. Enhancement - Improvement suggestion

### Error Process
1. Document in `.errors/active/`
2. Analyze in `.errors/analysis/`
3. Resolve and move to `.errors/resolved/`
4. Document prevention in `.errors/prevention/`

## Maintenance

### Regular Tasks
- Review active jobs
- Update documentation
- Check for errors
- Verify quality metrics
- Update version history

### Backup
- Daily automatic backup
- Manual backup before major changes
- Verify backup integrity

## Security

### Access Control
- Restrict sensitive information
- Use appropriate file permissions
- Maintain audit trail

### Data Protection
- Secure storage of personal data
- Regular security reviews
- Update security measures 