# InitializationStateManager Circular Dependency Error

## Error Details
- Test: `testGetInitializationOrder`
- Location: `InitializationStateManagerTest.php:169`
- Error: `RuntimeException: Circular dependency detected`
- Stack Trace:
  - InitializationStateManager.php:90
  - InitializationStateManager.php:104
  - InitializationStateManager.php:80

## Action Items
1. [ ] Review dependency registration in test setup
2. [ ] Verify dependency order is correct
3. [ ] Check circular dependency detection logic
4. [ ] Update test to properly handle dependencies
5. [ ] Run tests to verify fix

## Notes
- The error occurs during initialization order calculation
- Need to ensure test dependencies are properly structured
- May need to modify test setup to avoid circular dependencies 