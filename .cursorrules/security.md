# Security Standards and Guidelines

## Overview

This guide covers **development security standards** for the Research Project Template. These are the security practices developers must follow when writing code, in contrast to the security policy documented in `docs/SECURITY.md`.

## Input Validation Patterns

### Always Validate User Input

```python
# ✅ GOOD: Validate all external inputs
from infrastructure.core.exceptions import ValidationError

def process_user_data(data: dict) -> dict:
    """Process user data with validation."""
    # Validate required fields
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")

    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Required field missing: {field}")

    # Validate field types and formats
    name = data["name"]
    if not isinstance(name, str) or len(name) < 1:
        raise ValidationError("Name must be non-empty string")

    email = data["email"]
    if not isinstance(email, str) or "@" not in email:
        raise ValidationError("Invalid email format")

    # Sanitize and process
    sanitized = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "age": data.get("age", 0)  # Optional field with default
    }

    return sanitized
```

### Use Type Hints for Input Validation

```python
from typing import Optional
import re

def validate_email(email: str) -> str:
    """Validate email format and return normalized version."""
    if not isinstance(email, str):
        raise ValidationError("Email must be string")

    # Basic format validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValidationError("Invalid email format")

    return email.strip().lower()

def create_user(name: str, email: str, age: Optional[int] = None) -> dict:
    """Create user with validated inputs."""
    valid_name = validate_name(name)
    valid_email = validate_email(email)

    if age is not None:
        if not isinstance(age, int) or age < 0 or age > 150:
            raise ValidationError("Age must be integer between 0 and 150")

    return {
        "name": valid_name,
        "email": valid_email,
        "age": age
    }
```

## Secret Management

### Environment Variables Only

```python
# ✅ GOOD: Use environment variables for secrets
import os
from typing import Optional

class Config:
    """Configuration with secure secret handling."""

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("API_KEY")
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        self.jwt_secret: Optional[str] = os.getenv("JWT_SECRET")

    def validate_secrets(self) -> None:
        """Validate that all required secrets are present."""
        required_secrets = ["api_key", "database_url", "jwt_secret"]
        missing = [s for s in required_secrets if not getattr(self, s)]

        if missing:
            raise ConfigurationError(
                f"Missing required secrets: {', '.join(missing)}"
            )

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config = cls()
        config.validate_secrets()
        return config
```

### Never Hardcode Secrets

```python
# ❌ BAD: Never hardcode secrets
class BadConfig:
    API_KEY = "hardcoded-secret-key"  # NEVER DO THIS
    DB_PASSWORD = "password123"       # NEVER DO THIS

# ✅ GOOD: Always use environment variables
class GoodConfig:
    @property
    def api_key(self) -> str:
        key = os.getenv("API_KEY")
        if not key:
            raise ConfigurationError("API_KEY environment variable required")
        return key
```

### Secure File Operations

```python
import os
from pathlib import Path
from typing import BinaryIO

def safe_read_file(filepath: str | Path) -> str:
    """Safely read a file with security checks."""
    path = Path(filepath).resolve()

    # Prevent directory traversal attacks
    if ".." in str(path) or not path.is_absolute():
        raise SecurityError("Invalid file path")

    # Check file size to prevent resource exhaustion
    max_size = 10 * 1024 * 1024  # 10MB limit
    if path.stat().st_size > max_size:
        raise SecurityError("File too large")

    # Use secure permissions
    if oct(path.stat().st_mode)[-3:] != "600":
        raise SecurityError("File has insecure permissions")

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def safe_write_file(filepath: str | Path, content: str) -> None:
    """Safely write to a file with security checks."""
    path = Path(filepath).resolve()

    # Create directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically to prevent partial reads
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Set secure permissions before moving
    temp_path.chmod(0o600)
    temp_path.replace(path)
```

## Dependency Security

### Vulnerability Scanning

```bash
# Scan for vulnerabilities in dependencies
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check

# For uv projects
uv pip check  # Check for conflicts
uv pip audit  # Check for vulnerabilities
```

### Secure Dependency Management

```python
# ✅ GOOD: Pin exact versions for security
# pyproject.toml
[tool.uv]
dev-dependencies = [
    "pytest==7.4.3",
    "black==23.11.0",
    "mypy==1.7.1"
]

# ❌ BAD: Loose version constraints
# pyproject.toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",  # Too permissive
    "black>20.0",     # Even worse
]
```

### Safe Subprocess Usage

```python
import subprocess
from typing import List

def safe_run_command(command: List[str], timeout: int = 30) -> str:
    """Safely execute a command with security measures."""
    try:
        # Validate command arguments
        if not command or not all(isinstance(arg, str) for arg in command):
            raise SecurityError("Invalid command arguments")

        # Use shell=False to prevent shell injection
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )

        return result.stdout

    except subprocess.TimeoutExpired:
        raise SecurityError("Command timed out")
    except subprocess.CalledProcessError as e:
        raise SecurityError(f"Command failed: {e.stderr}")
    except Exception as e:
        raise SecurityError(f"Command execution failed: {e}")
```

## Security Testing Patterns

### Test Input Validation

```python
import pytest

def test_input_validation():
    """Test that malicious inputs are rejected."""

    # Test SQL injection attempts
    with pytest.raises(ValidationError):
        process_input("'; DROP TABLE users; --")

    # Test XSS attempts
    with pytest.raises(ValidationError):
        process_input("<script>alert('xss')</script>")

    # Test path traversal
    with pytest.raises(SecurityError):
        safe_read_file("../../../etc/passwd")

    # Test buffer overflow attempts
    with pytest.raises(ValidationError):
        process_input("A" * 1000000)  # Very long input

def test_secure_file_operations():
    """Test secure file handling."""

    # Test directory traversal protection
    with pytest.raises(SecurityError):
        safe_read_file("../secret.txt")

    # Test file size limits
    large_file = create_large_file(100 * 1024 * 1024)  # 100MB
    with pytest.raises(SecurityError):
        safe_read_file(large_file)

def test_secret_handling():
    """Test that secrets are handled securely."""

    # Test missing secrets
    with pytest.raises(ConfigurationError):
        Config.from_env()  # When env vars not set

    # Test secret validation
    config = Config()
    config.api_key = ""  # Invalid
    with pytest.raises(ValidationError):
        config.validate_secrets()
```

### Test Security Headers and Responses

```python
def test_secure_headers():
    """Test that responses include security headers."""

    response = make_api_request("/data")

    # Check for security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "Content-Security-Policy" in response.headers
```

## Secure Coding Practices

### Principle of Least Privilege

```python
# ✅ GOOD: Use minimal permissions
def read_config_file(filepath: str) -> dict:
    """Read config with read-only access."""
    with open(filepath, 'r') as f:  # Read-only mode
        return json.load(f)

# ❌ BAD: Unnecessary write permissions
def read_config_file(filepath: str) -> dict:
    """Read config but allows writing."""
    with open(filepath, 'r+') as f:  # Read-write mode - unnecessary
        return json.load(f)
```

### Fail-Safe Defaults

```python
# ✅ GOOD: Secure defaults
class SecureConfig:
    def __init__(self):
        self.debug_mode = False  # Secure default
        self.allow_external_access = False  # Secure default
        self.max_file_size = 1024 * 1024  # Reasonable limit

# ❌ BAD: Insecure defaults
class InsecureConfig:
    def __init__(self):
        self.debug_mode = True  # Insecure default
        self.allow_external_access = True  # Insecure default
        self.max_file_size = float('inf')  # No limit
```

### Secure Random Generation

```python
import secrets
import string

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_key() -> str:
    """Generate secure API key."""
    # Use secrets module, not random
    return secrets.token_urlsafe(32)

# ❌ BAD: Use secrets, not random
import random  # Insecure for crypto
def bad_generate_token(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))  # INSECURE
```

## Error Handling Security

### Avoid Information Leakage

```python
# ✅ GOOD: Generic error messages
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user with secure error handling."""
    try:
        user = get_user(username)
        if not user:
            return False  # Generic failure

        if not verify_password(password, user.hashed_password):
            return False  # Generic failure

        return True

    except Exception:
        # Log detailed error internally but return generic response
        logger.error("Authentication error", exc_info=True)
        return False

# ❌ BAD: Leaky error messages
def bad_authenticate_user(username: str, password: str) -> bool:
    """Authentication with information leakage."""
    try:
        user = get_user(username)
        if not user:
            raise ValueError("User does not exist")  # Leaks info

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")  # Leaks info

        return True

    except ValueError as e:
        # Error message reveals too much information
        raise AuthenticationError(str(e))  # Leaks sensitive info
```

### Secure Logging

```python
import logging

# ✅ GOOD: Sanitize data before logging
def log_user_action(user_id: str, action: str):
    """Log user action securely."""
    # Sanitize sensitive data
    safe_user_id = user_id.replace('\n', '').replace('\r', '')[:50]

    logger.info(f"User {safe_user_id} performed {action}")

# ❌ BAD: Log sensitive data
def bad_log_user_action(user_id: str, password: str, action: str):
    """Log with sensitive data exposure."""
    logger.info(f"User {user_id} with password {password} performed {action}")
```

## Network Security

### Safe HTTP Requests

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_secure_session() -> requests.Session:
    """Create requests session with security settings."""
    session = requests.Session()

    # Configure retries with backoff
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set reasonable timeouts
    session.timeout = 30

    return session

def secure_api_call(url: str, api_key: str) -> dict:
    """Make secure API call."""
    session = create_secure_session()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Research-Template/1.0"
    }

    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Validate response content type
        if 'application/json' not in response.headers.get('content-type', ''):
            raise SecurityError("Unexpected response content type")

        return response.json()

    except requests.RequestException as e:
        raise SecurityError(f"API request failed: {e}")
```

## Security Checklist

Before committing code:

- [ ] All user inputs are validated
- [ ] No secrets are hardcoded
- [ ] File operations are safe from traversal attacks
- [ ] Dependencies are pinned to secure versions
- [ ] Error messages don't leak sensitive information
- [ ] Logging doesn't expose secrets
- [ ] Random values use `secrets` module
- [ ] Network requests have timeouts and retries
- [ ] Security tests are included
- [ ] Dependencies are audited regularly

## Security Testing Integration

```python
# Add to pytest configuration
# pytest.ini
[tool:pytest]
addopts = --strict-markers
markers =
    security: marks tests as security-related
    integration: marks tests as integration tests

# Run security tests
pytest -m security

# Run all tests including security
pytest --cov --cov-report=html -m "not integration"  # Fast tests first
pytest -m integration  # Slower integration tests
```

## See Also

- [docs/SECURITY.md](../docs/development/SECURITY.md) - Security policy and vulnerability reporting
- [docs/BEST_PRACTICES.md](../docs/best-practices/BEST_PRACTICES.md) - Security best practices section
- [error_handling.md](error_handling.md) - Secure error handling patterns
- [testing_standards.md](testing_standards.md) - Security testing patterns

---

**Note**: This document focuses on development security practices. For security policy, vulnerability reporting, and security updates, see [docs/SECURITY.md](../docs/development/SECURITY.md).