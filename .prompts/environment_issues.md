# Environment Issue Resolution Prompt

## Context
I am working on a Python project and encountering environment setup issues. Here are the details:

## Issue Description
[Describe the specific issue you're encountering]
- Error message:
- Environment:
  - OS: [Windows/Linux/Mac]
  - Python version:
  - Virtual environment:
  - Dependencies:

## Steps Already Taken
1. [List steps already attempted]
2. [Include any error messages]
3. [Note any temporary solutions tried]

## Current State
- What works:
- What doesn't work:
- Impact on development:

## Questions
1. What could be causing this issue?
2. What are the recommended solutions?
3. How can we prevent this in the future?

## Additional Information
- Relevant configuration files:
- System information:
- Recent changes:
- Time constraints:

## Expected Outcome
[Describe what you want to achieve]

## Success Criteria
- [ ] Issue is resolved
- [ ] Solution is documented
- [ ] Prevention measures are in place
- [ ] Team is informed of the solution

## Example Usage
```markdown
# Environment Issue Resolution Prompt

## Context
I am working on a Python project and encountering environment setup issues. Here are the details:

## Issue Description
- Error message: "ModuleNotFoundError: No module named 'jwt'"
- Environment:
  - OS: Windows 10
  - Python version: 3.11.9
  - Virtual environment: venv
  - Dependencies: requirements.test.txt

## Steps Already Taken
1. Installed dependencies via pip
2. Recreated virtual environment
3. Checked Python PATH
4. Verified package installation

## Current State
- What works: Basic Python installation
- What doesn't work: Package imports
- Impact on development: Cannot run security tests

## Questions
1. Why are packages not found despite installation?
2. How can we fix the virtual environment?
3. What's the best way to verify the setup?

## Additional Information
- requirements.test.txt contains all dependencies
- Using PowerShell for commands
- Recently updated Python version
- Need solution within 24 hours

## Expected Outcome
Working virtual environment with all packages properly installed and accessible.

## Success Criteria
- [ ] All packages import successfully
- [ ] Virtual environment activates properly
- [ ] Tests run without import errors
- [ ] Solution documented in setup guide
```

## Response Template
```markdown
# Environment Issue Resolution

## Root Cause
[Explain what caused the issue]

## Solution
1. [Step-by-step solution]
2. [Commands to run]
3. [Configuration changes]

## Prevention
1. [How to prevent this issue]
2. [Best practices to follow]
3. [Monitoring suggestions]

## Documentation
1. [What to document]
2. [Where to document]
3. [Who to inform]

## Verification
1. [How to verify the solution]
2. [Tests to run]
3. [Success indicators]

## References
- [Relevant documentation]
- [Similar issues]
- [Best practices]
``` 