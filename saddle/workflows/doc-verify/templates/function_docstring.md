# Function Docstring Template

Use this template when adding docstrings to Python functions.

## Format (Google Style)

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """[Brief one-line description].

    [Optional: Extended description providing more context,
    explaining the algorithm, or clarifying behavior]

    Args:
        param1: [Description of parameter, including valid values
            or constraints if applicable]
        param2: [Description of parameter]

    Returns:
        [Description of return value. For complex types, describe
        the structure]

    Raises:
        ExceptionType: [When this exception is raised]
        AnotherException: [When this is raised]

    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
        expected_output

    Note:
        [Optional: Any important caveats or special considerations]
    """
```

## Examples

### Simple Function

```python
def calculate_discount(price: float, percentage: float) -> float:
    """Calculate discounted price.

    Args:
        price: Original price in dollars.
        percentage: Discount percentage (0-100).

    Returns:
        The discounted price.

    Raises:
        ValueError: If percentage is not between 0 and 100.
    """
```

### Complex Function

```python
def process_payment(
    amount: Decimal,
    currency: str,
    customer_id: str,
    idempotency_key: str | None = None,
) -> PaymentResult:
    """Process a payment transaction.

    Validates the amount and currency, checks customer credit,
    then submits to the payment processor. Implements automatic
    retry with exponential backoff for transient failures.

    Args:
        amount: The payment amount in the smallest currency unit
            (e.g., cents for USD).
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR').
        customer_id: Unique identifier for the customer.
        idempotency_key: Optional key for idempotent requests.
            If not provided, a new key is generated.

    Returns:
        PaymentResult containing:
            - transaction_id: Unique transaction identifier
            - status: 'success', 'pending', or 'failed'
            - amount: Confirmed amount charged
            - timestamp: When the transaction was processed

    Raises:
        InvalidAmountError: If amount is negative or zero.
        InvalidCurrencyError: If currency code is not recognized.
        InsufficientFundsError: If customer has insufficient credit.
        PaymentProcessorError: If payment processor is unavailable
            after all retries.

    Example:
        >>> result = process_payment(
        ...     amount=Decimal('1000'),
        ...     currency='USD',
        ...     customer_id='cust_123',
        ... )
        >>> print(result.status)
        'success'

    Note:
        This function is idempotent when an idempotency_key is provided.
        Duplicate requests with the same key return the original result.
    """
```

### Async Function

```python
async def fetch_user_data(user_id: str, timeout: float = 30.0) -> UserData:
    """Fetch user data from the external API.

    Makes an async HTTP request to the user service. Implements
    caching to reduce API calls for frequently accessed users.

    Args:
        user_id: The unique user identifier.
        timeout: Request timeout in seconds.

    Returns:
        UserData object with user profile information.

    Raises:
        UserNotFoundError: If user doesn't exist.
        TimeoutError: If request exceeds timeout.
        APIError: If external API returns an error.
    """
```
