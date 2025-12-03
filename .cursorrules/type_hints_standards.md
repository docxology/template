# Type Hints and Annotations Standards

## Overview

All public APIs and module-level code must have complete type hints. This ensures code clarity, enables IDE support, and catches errors early.

## Coverage Requirements

- **Comprehensive for public APIs** - All functions exposed in `__init__.py`
- **Thorough for module code** - All functions in `core.py`, `cli.py`, etc.
- **Required for** - Function parameters, return types, variables
- **Optional for** - Internal helper functions, temporary variables (use sparingly)

## Basic Patterns

### Function Parameters and Returns

```python
# ✅ GOOD: Complete type hints
def process_data(input_data: str, count: int = 10) -> dict:
    """Process data with type hints on all parameters."""
    return {"processed": input_data, "count": count}

# ✅ GOOD: More complex return type
def get_users(db: Database, limit: int) -> list[dict]:
    """Return list of user dictionaries."""
    return db.query("SELECT * FROM users LIMIT ?", limit)

# ❌ BAD: Missing type hints
def process_data(input_data, count=10):
    """Missing type hints."""
    return {"processed": input_data, "count": count}

# ❌ BAD: Incomplete type hints
def process_data(input_data: str, count: int = 10):
    """Missing return type hint."""
    return {"processed": input_data, "count": count}
```

### Variable Annotations

```python
# ✅ GOOD: Annotate at initialization or declaration
from pathlib import Path

config_file: Path = Path("config.yaml")
user_count: int = 0
is_valid: bool = True

# ✅ GOOD: Can omit type if immediately obvious
result = process_data("input")  # OK if function return type is clear

# ❌ BAD: Unclear without annotation
data = load_from_file()  # What type is data?

# BETTER
data: dict = load_from_file()
```

### Class Methods

```python
class DataProcessor:
    """Example class with type hints."""
    
    def __init__(self, config: dict) -> None:
        """Initialize processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config: dict = config
    
    def process(self, data: str) -> dict:
        """Process data.
        
        Args:
            data: Input data
            
        Returns:
            Processed result
        """
        return {"result": data}
    
    @classmethod
    def from_file(cls, filepath: str) -> "DataProcessor":
        """Create processor from file.
        
        Args:
            filepath: Path to config file
            
        Returns:
            New DataProcessor instance
        """
        config = load_config(filepath)
        return cls(config)
    
    @staticmethod
    def validate(data: dict) -> bool:
        """Validate data format.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid
        """
        return "required_field" in data
```

## Complex Types

### Union Types (Multiple Possible Types)

```python
from typing import Union

# ✅ GOOD: Using Union for multiple types
def parse_input(value: Union[str, int]) -> str:
    """Parse string or integer input."""
    return str(value)

# ✅ GOOD: Python 3.10+ pipe syntax
def parse_input(value: str | int) -> str:
    """Parse string or integer input (Python 3.10+)."""
    return str(value)

# ✅ GOOD: Optional (Union with None)
def get_config(path: str) -> Union[dict, None]:
    """Get config from file, or None if not found."""
    if os.path.exists(path):
        return load_config(path)
    return None

# Shorthand for Optional
def get_config(path: str) -> dict | None:
    """Get config from file, or None if not found."""
    if os.path.exists(path):
        return load_config(path)
    return None
```

### Collection Types

```python
from typing import List, Dict, Set, Tuple

# ✅ GOOD: Specific element types
def process_items(items: List[str]) -> Dict[str, int]:
    """Process list of strings, return count dict."""
    return {item: len(item) for item in items}

# ✅ GOOD: Nested collections
def get_data() -> List[Dict[str, Union[str, int]]]:
    """Return list of dictionaries with string/int values."""
    return [{"name": "Alice", "age": 30}]

# ✅ GOOD: Python 3.9+ style (lowercase)
def process_items(items: list[str]) -> dict[str, int]:
    """Process list of strings, return count dict."""
    return {item: len(item) for item in items}

# ✅ GOOD: Set and Tuple
def get_unique_ids(data: List[Dict]) -> Set[int]:
    """Extract unique IDs."""
    return {item["id"] for item in data}

def get_coordinates() -> Tuple[int, int]:
    """Return x, y coordinates."""
    return (0, 0)

# ✅ GOOD: Variable-length tuple
def get_items() -> Tuple[str, ...]:
    """Return variable number of strings."""
    return ("a", "b", "c")

# ❌ BAD: Vague collection types
def process_items(items: list) -> dict:
    """Element types not specified."""
    return {}
```

### Callable Types

```python
from typing import Callable

# ✅ GOOD: Function that takes and returns
def apply_function(func: Callable[[int, int], int], a: int, b: int) -> int:
    """Apply a function to two integers."""
    return func(a, b)

# ✅ GOOD: Function with no parameters
def run_task(task: Callable[[], None]) -> None:
    """Run a task that takes no arguments."""
    task()

# ✅ GOOD: Function that returns a function
def get_multiplier(factor: int) -> Callable[[int], int]:
    """Return a function that multiplies by factor."""
    def multiply(x: int) -> int:
        return x * factor
    return multiply

# Usage
multiply_by_2 = get_multiplier(2)
result = multiply_by_2(5)  # 10
```

### Generic Types

```python
from typing import TypeVar, Generic

# ✅ GOOD: Generic type variable
T = TypeVar('T')

def first_item(items: List[T]) -> T:
    """Get first item from list."""
    return items[0]

# Usage works with any type
first_int = first_item([1, 2, 3])      # int
first_str = first_item(["a", "b"])     # str

# ✅ GOOD: Generic class
class Container(Generic[T]):
    """Container for any type."""
    
    def __init__(self, item: T) -> None:
        self.item = item
    
    def get(self) -> T:
        """Get the contained item."""
        return self.item

# Usage
int_container = Container[int](42)
str_container = Container[str]("hello")
```

## Special Types

### Literal Types (Specific Values)

```python
from typing import Literal

# ✅ GOOD: Only specific values allowed
def set_log_level(level: Literal["DEBUG", "INFO", "WARN", "ERROR"]) -> None:
    """Set log level to specific values only."""
    pass

# ✅ GOOD: With numbers
def set_direction(direction: Literal[0, 90, 180, 270]) -> None:
    """Set direction to cardinal directions."""
    pass

# Usage - only these values are valid
set_log_level("DEBUG")  # ✅ OK
set_log_level("INVALID")  # ❌ Type checker catches this
```

### TypedDict (Structured Dictionaries)

```python
from typing import TypedDict

# ✅ GOOD: Define dictionary structure
class UserData(TypedDict):
    """User data structure."""
    name: str
    email: str
    age: int
    is_active: bool

def create_user(data: UserData) -> None:
    """Create user from typed dictionary."""
    print(f"Creating user: {data['name']}")

# Usage - clear structure
user: UserData = {
    "name": "Alice",
    "email": "alice@example.com",
    "age": 30,
    "is_active": True
}
create_user(user)

# ✅ GOOD: Optional fields
class ConfigData(TypedDict, total=False):
    """Config with optional fields."""
    debug: bool  # Optional
    timeout: int  # Optional

config: ConfigData = {"debug": True}  # OK
```

### Protocol (Duck Typing)

```python
from typing import Protocol

# ✅ GOOD: Define interface without inheritance
class Drawable(Protocol):
    """Anything that can be drawn."""
    
    def draw(self) -> None:
        """Draw the object."""
        ...

class Circle:
    """Circle that implements Drawable."""
    
    def draw(self) -> None:
        """Draw circle."""
        print("Drawing circle")

class Square:
    """Square that implements Drawable."""
    
    def draw(self) -> None:
        """Draw square."""
        print("Drawing square")

def render(obj: Drawable) -> None:
    """Render any drawable object."""
    obj.draw()

# Works with any object implementing draw()
render(Circle())   # ✅ OK
render(Square())   # ✅ OK
```

## Inheritance and Self Types

### Using Self Type

```python
from typing import Self

# ✅ GOOD: Builder pattern with fluent API
class QueryBuilder:
    """Query builder with fluent API."""
    
    def filter(self, condition: str) -> Self:
        """Add filter and return self."""
        # ... add filter ...
        return self
    
    def limit(self, count: int) -> Self:
        """Add limit and return self."""
        # ... add limit ...
        return self
    
    def execute(self) -> list[dict]:
        """Execute query."""
        # ... execute ...
        return []

# Fluent usage
query = QueryBuilder().filter("active=true").limit(10).execute()
```

## Forward References

```python
# ✅ GOOD: Use quotes for forward references
class Node:
    """Tree node."""
    
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.left: "Node | None" = None
        self.right: "Node | None" = None
    
    def add_child(self, child: "Node") -> None:
        """Add child node."""
        pass

# ✅ GOOD: Using __future__ annotations (Python 3.7+)
from __future__ import annotations

class Node:
    """Tree node (with future annotations)."""
    
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.left: Node | None = None
        self.right: Node | None = None
```

## Type Checking

### mypy Static Type Checking

```bash
# Check types in project
mypy infrastructure/

# Strict mode (recommended)
mypy --strict infrastructure/

# Check specific file
mypy infrastructure/core.py
```

### Configuration (mypy.ini)

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
```

### Ignoring Type Checks

```python
# ✅ GOOD: Only when necessary
import subprocess

# Type checker doesn't know about this library
result = subprocess.run(["ls"], capture_output=True)  # type: ignore

# Better: Use a library with types, or stub files
from pathlib import Path

files = list(Path(".").glob("*.py"))  # No type ignore needed
```

## Common Type Patterns

### Return Type Patterns

```python
# ✅ GOOD: Success/failure pattern
def validate_email(email: str) -> bool:
    """Return validation result."""
    return "@" in email

# ✅ GOOD: Result with error
def parse_config(filepath: str) -> dict | None:
    """Return dict or None if parsing failed."""
    try:
        return json.load(open(filepath))
    except Exception:
        return None

# ✅ GOOD: Multiple return types (use Union)
def get_value(key: str) -> str | int | None:
    """Get value by key."""
    return None
```

### Context Manager Pattern

```python
from typing import Iterator, Callable
from contextlib import contextmanager

# ✅ GOOD: Context manager
class Connection:
    """Database connection."""
    
    def __enter__(self) -> "Connection":
        """Enter context."""
        return self
    
    def __exit__(self, *args: object) -> None:
        """Exit context."""
        pass

# ✅ GOOD: Generator-based context manager
@contextmanager
def get_connection(url: str) -> Iterator[Connection]:
    """Get database connection."""
    conn = Connection(url)
    try:
        yield conn
    finally:
        conn.close()
```

## Convention and Best Practices

### 1. Import Type Hints at Module Top

```python
from typing import (
    List, Dict, Optional, Union, Tuple, Callable,
    Any, TypeVar, Generic
)

# Not inside functions
def good_function(items: List[str]) -> Dict[str, int]:
    pass
```

### 2. Use Modern Syntax (Python 3.9+)

```python
# ✅ GOOD: Python 3.9+
def process(items: list[str]) -> dict[str, int]:
    pass

# ⚠️ OK: Still works but older style
from typing import List, Dict

def process(items: List[str]) -> Dict[str, int]:
    pass
```

### 3. Be Specific

```python
# ✅ GOOD: Specific types
def process(items: list[str], mapping: dict[str, int]) -> None:
    pass

# ❌ BAD: Too generic
def process(items: list, mapping: dict) -> None:
    pass

# ❌ VERY BAD: Any type loses type safety
def process(items: list[Any], mapping: dict[Any, Any]) -> None:
    pass
```

### 4. Don't Over-Annotate

```python
# ✅ GOOD: Necessary annotations only
def create_user(name: str, age: int) -> User:
    user = User(name, age)  # Type clear from function
    return user

# ❌ UNNECESSARY: Over-annotating
def create_user(name: str, age: int) -> User:
    user: User = User(name, age)  # Type already known from assignment
    return user
```

## Quality Checklist

Before committing code:

- [ ] All public functions have type hints
- [ ] All parameters have type hints
- [ ] All return types specified
- [ ] Complex types use specific generics (not `Any`)
- [ ] Type hints are accurate (tested with mypy)
- [ ] No `# type: ignore` unless necessary
- [ ] Forward references use quotes or `__future__` imports
- [ ] Module docstrings explain type requirements
- [ ] Examples show type usage

## See Also

- [documentation_standards.md](documentation_standards.md) - Document types in docstrings
- [testing_standards.md](testing_standards.md) - Test type hints
- [error_handling.md](error_handling.md) - Exception type hints
- [../docs/API_REFERENCE.md](../docs/API_REFERENCE.md) - Type examples in API documentation
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Type system design
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)






