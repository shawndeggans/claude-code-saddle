# Documentation Policy

Documentation MUST be updated alongside code changes. The doc-verify hook checks for documentation gaps before commits.

## What Requires Documentation

### New Modules
- Every new Python module needs a module-level docstring
- Explain the module's purpose and key components
- List main exports

### Public Functions and Classes
- All public functions (not starting with `_`) need docstrings
- All public classes need class-level docstrings
- Use Google-style or NumPy-style docstrings consistently

### API Changes
- New endpoints require API documentation
- Changed endpoints require updated documentation
- Breaking changes require CHANGELOG entry

### New Features
- Major features need README updates
- User-facing changes need CHANGELOG entries
- Architecture changes need design doc updates

## Docstring Format

### Functions (Google Style)
```python
def process_payment(amount: float, currency: str) -> PaymentResult:
    """Process a payment transaction.

    Validates the amount and currency, then submits to the payment
    processor. Handles retries for transient failures.

    Args:
        amount: The payment amount in the smallest currency unit.
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR').

    Returns:
        PaymentResult containing transaction ID and status.

    Raises:
        InvalidAmountError: If amount is negative or zero.
        PaymentFailedError: If payment processor rejects transaction.
    """
```

### Classes
```python
class PaymentProcessor:
    """Handles payment transactions with external processors.

    Supports multiple payment providers through a unified interface.
    Implements retry logic and idempotency for reliability.

    Attributes:
        provider: The payment provider name.
        timeout: Request timeout in seconds.

    Example:
        >>> processor = PaymentProcessor('stripe')
        >>> result = processor.charge(1000, 'USD')
    """
```

### Modules
```python
"""Payment processing module.

This module provides the core payment handling functionality,
including transaction processing, refunds, and reporting.

Key Components:
    - PaymentProcessor: Main interface for payment operations
    - Transaction: Represents a single payment transaction
    - RefundManager: Handles refund requests

Usage:
    from project.payments import PaymentProcessor
    processor = PaymentProcessor('stripe')
"""
```

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

### Added
- New payment retry logic with exponential backoff

### Changed
- Increased default timeout from 30s to 60s

### Fixed
- Race condition in concurrent payment processing

### Removed
- Deprecated `legacy_charge()` method
```

## What Doesn't Require Documentation

- Private functions (starting with `_`)
- Test files
- Migration files
- Configuration files
- Simple property accessors

## Enforcement

### doc-verify Hook
- Runs on pre-commit
- Checks staged Python files for missing docstrings
- Warns on new public functions without documentation
- Blocks commit if critical documentation is missing

### Manual Verification
- Run `./scripts/run-cleanup.sh` to check documentation coverage
- Review generated warnings before committing
