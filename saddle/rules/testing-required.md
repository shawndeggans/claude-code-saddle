# Testing Required Policy

All code changes MUST have corresponding tests. Test-Driven Development (TDD) is enforced via the TDD Guard hook.

## TDD Workflow

### The Red-Green-Refactor Cycle
1. **Red**: Write a failing test first
2. **Green**: Write minimum code to pass the test
3. **Refactor**: Improve code while keeping tests green

### Enforcement
- TDD Guard hook blocks writing implementation files without corresponding test files
- Hook checks that test file exists before allowing edits to source files
- Warnings issued if tests exist but don't cover the function being modified

## Test Requirements by Type

### Unit Tests
- Required for all business logic functions
- Should be fast (<100ms per test)
- Mock external dependencies
- Location: `project/tests/unit/` or `project/tests/test_*.py`

### Integration Tests
- Required for API endpoints
- Required for database operations
- May use test databases or containers
- Location: `project/tests/integration/`

### End-to-End Tests
- Required for critical user flows
- Optional for minor features
- Location: `project/tests/e2e/`

## What Doesn't Require Tests

The TDD Guard excludes these patterns by default:

- `**/migrations/**` - Database migrations
- `**/config/**` - Configuration files
- `**/__init__.py` - Package init files
- `**/conftest.py` - Pytest fixtures
- `**/settings.py` - Django/Flask settings
- `**/manage.py` - Django management

## Test File Naming

### Python
- Source: `src/module.py`
- Test: `tests/test_module.py`

### JavaScript/TypeScript
- Source: `src/module.js`
- Test: `tests/module.test.js` or `__tests__/module.test.js`

## Coverage Expectations

### Minimum Thresholds
- New code: 80% coverage
- Critical paths (auth, payments): 95% coverage
- Overall project: 70% coverage

### Measuring Coverage
```bash
pytest --cov=project/src --cov-report=term-missing project/tests/
```

## Rationale

### Why TDD?
- Catches bugs before they reach production
- Forces modular, testable design
- Documentation through test cases
- Confidence when refactoring

### The 2x Investment
- TDD takes roughly 2x the development time
- Payoff: Fewer bugs, faster debugging, safer refactoring
- Net positive for any code that will be maintained
