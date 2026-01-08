# Refactoring Prompt

## Purpose

Refactor existing code following the clean break approach, ensuring improved maintainability while preserving functionality and meeting all quality standards.

## Context

This prompt enforces the clean break refactoring approach and leverages refactoring standards:

- [`../../projects/project/docs/refactor_playbook.md`](../../projects/project/docs/refactor_playbook.md) - Refactoring procedures
- [`../../projects/project/docs/refactor_hotspots.md`](../../projects/project/docs/refactor_hotspots.md) - Code quality analysis
- [`../../.cursorrules/refactoring.md`](../../.cursorrules/refactoring.md) - Clean break refactoring standards
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing during refactoring

## Prompt Template

```
You are refactoring code in the Research Project Template using the CLEAN BREAK APPROACH. This means NO BACKWARD COMPATIBILITY - migration with full testing and documentation updates.

CODE TO REFACTOR: [Specify the file/module/function to refactor]
REFACTORING GOAL: [Describe what improvement to achieve - readability, performance, maintainability, etc.]

REFACTORING REQUIREMENTS:

## 1. Clean Break Approach - CRITICAL REQUIREMENT

**NO BACKWARD COMPATIBILITY**: rewrite with new APIs. Old code is replaced entirely.

### Migration Strategy
```python
# BEFORE: Old API (to be completely removed)
def old_function(data):
    # Monolithic implementation
    result = []
    for item in data:
        processed = item * 2  # Hardcoded logic
        result.append(processed)
    return result

# AFTER: New API (replacement)
def process_data_items(items: List[float]) -> List[float]:
    """Process data items with clear separation of concerns.

    Args:
        items: Input data items to process

    Returns:
        Processed data items
    """
    return [process_single_item(item) for item in items]

def process_single_item(item: float) -> float:
    """Process a single data item.

    Args:
        item: Individual data item

    Returns:
        Processed item
    """
    validate_item(item)
    return item * 2

def validate_item(item: float) -> None:
    """Validate data item.

    Args:
        item: Item to validate

    Raises:
        ValueError: If item is invalid
    """
    if not isinstance(item, (int, float)):
        raise ValueError(f"Item must be numeric, got {type(item)}")
```

### Migration Process
1. **Create new implementation** with improved design
2. **Update all callers** to use new API
3. **Remove old code entirely**
4. **Update tests** for new implementation
5. **Update documentation** completely

## 2. Refactoring Process

### Phase 1: Analysis and Planning

**Code Quality Assessment:**
```python
# Analyze code complexity and issues
def analyze_code_quality(code_path: Path) -> Dict[str, Any]:
    """Analyze code quality metrics."""
    return {
        'complexity': calculate_cyclomatic_complexity(code_path),
        'duplication': find_code_duplication(code_path),
        'dependencies': analyze_dependencies(code_path),
        'test_coverage': measure_test_coverage(code_path),
        'maintainability_index': calculate_maintainability_index(code_path)
    }
```

**Refactoring Planning:**
- Identify specific issues (complexity, duplication, coupling)
- Define clear improvement goals
- Plan modularization strategy
- Design new API structure

### Phase 2: Implementation

**Modularization Techniques:**
```python
# BEFORE: Monolithic class
class DataProcessor:
    def __init__(self, config):
        self.config = config

    def process(self, data):
        # Validation, processing, logging all mixed
        if not data:
            raise ValueError("No data")

        result = []
        for item in data:
            processed = self._transform(item)
            result.append(processed)

        print(f"Processed {len(result)} items")
        return result

    def _transform(self, item):
        return item * 2

# AFTER: Separated concerns
@dataclass
class ProcessingConfig:
    """Configuration for data processing."""
    multiplier: float = 2.0
    validate_input: bool = True

class DataValidator:
    """Handles data validation logic."""

    def validate(self, data: List[float]) -> None:
        """Validate input data.

        Args:
            data: Data to validate

        Raises:
            ValueError: If validation fails
        """
        if not data:
            raise ValueError("Data cannot be empty")

        if not all(isinstance(x, (int, float)) for x in data):
            raise ValueError("All data must be numeric")

class DataTransformer:
    """Handles data transformation logic."""

    def __init__(self, config: ProcessingConfig):
        self.config = config

    def transform_item(self, item: float) -> float:
        """Transform single data item.

        Args:
            item: Item to transform

        Returns:
            Transformed item
        """
        return item * self.config.multiplier

class DataProcessor:
    """Orchestrates data processing with separated concerns."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.validator = DataValidator()
        self.transformer = DataTransformer(config)
        self.logger = get_logger(__name__)

    def process(self, data: List[float]) -> List[float]:
        """Process data with validation and logging.

        Args:
            data: Input data to process

        Returns:
            Processed data
        """
        if self.config.validate_input:
            self.validator.validate(data)

        result = [self.transformer.transform_item(item) for item in data]

        self.logger.info(f"Processed {len(result)} items")
        return result
```

### Phase 3: Testing and Validation

**Testing During Refactoring:**
```python
# Test new implementation thoroughly
def test_refactored_data_processor():
    """Test refactored DataProcessor maintains functionality."""
    config = ProcessingConfig(multiplier=3.0, validate_input=True)

    processor = DataProcessor(config)

    # Test normal operation
    data = [1, 2, 3, 4, 5]
    result = processor.process(data)

    assert result == [3, 6, 9, 12, 15]

    # Test validation
    with pytest.raises(ValueError):
        processor.process([])

    with pytest.raises(ValueError):
        processor.process(["not", "numeric"])

# Ensure backward compatibility is NOT maintained
def test_old_api_removed():
    """Verify old monolithic API is completely removed."""
    # This should fail - old API no longer exists
    with pytest.raises(NameError):
        old_function([1, 2, 3])  # Old function removed
```

### Phase 4: Documentation Updates

**Documentation Migration:**
```markdown
# BEFORE: Inadequate documentation
## DataProcessor
Processes data by multiplying by 2.

# AFTER: documentation
## Data Processing Module

This module provides data processing capabilities with clear separation of concerns.

### Classes

#### `ProcessingConfig`
Configuration dataclass for data processing operations.

**Attributes:**
- `multiplier` (float): Multiplication factor (default: 2.0)
- `validate_input` (bool): Whether to validate input data (default: True)

#### `DataValidator`
Handles input validation logic.

**Methods:**
- `validate(data: List[float]) -> None`: Validates input data

#### `DataTransformer`
Handles data transformation operations.

**Methods:**
- `transform_item(item: float) -> float`: Transforms single data item

#### `DataProcessor`
Main orchestrator class for data processing operations.

**Methods:**
- `process(data: List[float]) -> List[float]`: Processes dataset

### Usage Example

```python
from data_processing import ProcessingConfig, DataProcessor

# Configure processing
config = ProcessingConfig(multiplier=3.0)

# Create processor
processor = DataProcessor(config)

# Process data
result = processor.process([1, 2, 3])
# Result: [3, 6, 9]
```
```

## 3. Refactoring Techniques

### Extract Method/Function
```python
# BEFORE: Long method with multiple responsibilities
def process_user_data(user_data):
    # Validation
    if not user_data.get('email'):
        raise ValueError("Email required")

    # Data cleaning
    user_data['email'] = user_data['email'].strip().lower()

    # Database operation
    user_id = save_to_database(user_data)

    # Notification
    send_welcome_email(user_data['email'])

    return user_id

# AFTER: Separated responsibilities
def validate_user_data(user_data: Dict[str, Any]) -> None:
    """Validate user data requirements."""
    if not user_data.get('email'):
        raise ValueError("Email is required")

def clean_user_email(user_data: Dict[str, Any]) -> None:
    """Clean and normalize email address."""
    user_data['email'] = user_data['email'].strip().lower()

def save_user_to_database(user_data: Dict[str, Any]) -> int:
    """Save user data to database."""
    # Database operations
    return user_id

def send_user_notification(email: str) -> None:
    """Send welcome notification to user."""
    # Email sending logic
    pass

def process_user_registration(user_data: Dict[str, Any]) -> int:
    """Process user registration workflow.

    Args:
        user_data: User registration data

    Returns:
        New user ID
    """
    validate_user_data(user_data)
    clean_user_email(user_data)

    user_id = save_user_to_database(user_data)
    send_user_notification(user_data['email'])

    return user_id
```

### Replace Conditional with Polymorphism
```python
# BEFORE: Complex conditional logic
class ReportGenerator:
    def generate_report(self, data, report_type):
        if report_type == "pdf":
            return self._generate_pdf_report(data)
        elif report_type == "html":
            return self._generate_html_report(data)
        elif report_type == "json":
            return self._generate_json_report(data)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

# AFTER: Polymorphic design
from abc import ABC, abstractmethod

class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> str:
        """Generate report from data."""
        pass

class PDFReportGenerator(ReportGenerator):
    """Generates PDF reports."""

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate PDF report."""
        # PDF generation logic
        return "pdf_content"

class HTMLReportGenerator(ReportGenerator):
    """Generates HTML reports."""

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        # HTML generation logic
        return "html_content"

class JSONReportGenerator(ReportGenerator):
    """Generates JSON reports."""

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        # JSON generation logic
        return "json_content"

def create_report_generator(report_type: str) -> ReportGenerator:
    """Factory function for report generators."""
    generators = {
        "pdf": PDFReportGenerator,
        "html": HTMLReportGenerator,
        "json": JSONReportGenerator,
    }

    generator_class = generators.get(report_type)
    if not generator_class:
        raise ValueError(f"Unknown report type: {report_type}")

    return generator_class()
```

### Remove Code Duplication
```python
# BEFORE: Duplicated validation logic
def process_customer_order(order_data):
    if not order_data.get('customer_id'):
        raise ValueError("Customer ID required")
    if not order_data.get('items'):
        raise ValueError("Order must have items")
    # Process order...

def process_supplier_order(order_data):
    if not order_data.get('supplier_id'):
        raise ValueError("Supplier ID required")
    if not order_data.get('items'):
        raise ValueError("Order must have items")
    # Process order...

# AFTER: Shared validation
def validate_order_data(order_data: Dict[str, Any], entity_type: str) -> None:
    """Validate order data for any entity type.

    Args:
        order_data: Order data to validate
        entity_type: Type of entity ('customer' or 'supplier')

    Raises:
        ValueError: If validation fails
    """
    entity_id_field = f"{entity_type}_id"

    if not order_data.get(entity_id_field):
        raise ValueError(f"{entity_type.title()} ID is required")

    if not order_data.get('items'):
        raise ValueError("Order must contain items")

    if not isinstance(order_data['items'], list):
        raise ValueError("Items must be a list")

def process_customer_order(order_data: Dict[str, Any]) -> OrderResult:
    """Process customer order with validation."""
    validate_order_data(order_data, 'customer')
    # Customer-specific processing...

def process_supplier_order(order_data: Dict[str, Any]) -> OrderResult:
    """Process supplier order with validation."""
    validate_order_data(order_data, 'supplier')
    # Supplier-specific processing...
```

## 4. Safety Measures

### Testing Throughout Refactoring
- **Start with tests** of existing functionality
- **Test after each change** to ensure preservation of behavior
- **Add tests for new code** as it's written
- **Performance regression testing** to ensure no degradation

### Incremental Changes with Validation
```python
# Refactoring workflow with validation
def refactor_with_safety(original_function, new_implementation):
    """Safely refactor function with validation."""

    # 1. Create test suite for original
    test_suite = create_test_suite_for_function(original_function)

    # 2. Run tests to establish baseline
    baseline_results = run_test_suite(test_suite)

    # 3. Implement new version
    refactored_function = new_implementation

    # 4. Run same tests on new implementation
    refactored_results = run_test_suite(test_suite, refactored_function)

    # 5. Validate identical behavior
    assert_results_identical(baseline_results, refactored_results)

    # 6. Additional quality checks
    assert_improved_quality(refactored_function, original_function)

    return refactored_function
```

### Rollback Procedures
```python
# Maintain rollback capability during refactoring
class RefactoringCheckpoint:
    """Manages refactoring checkpoints for safe rollback."""

    def __init__(self, code_path: Path):
        self.code_path = code_path
        self.backups = []

    def create_checkpoint(self):
        """Create backup of current code state."""
        backup_path = self.code_path.with_suffix(f'.backup_{len(self.backups)}')
        shutil.copy2(self.code_path, backup_path)
        self.backups.append(backup_path)

    def rollback_to_checkpoint(self, checkpoint_index: int):
        """Rollback to specific checkpoint."""
        if checkpoint_index >= len(self.backups):
            raise ValueError("Invalid checkpoint index")

        backup_path = self.backups[checkpoint_index]
        shutil.copy2(backup_path, self.code_path)

    def cleanup_checkpoints(self):
        """Remove backup files after successful refactoring."""
        for backup in self.backups:
            backup.unlink()
        self.backups.clear()
```

## Key Requirements

- [ ] **Clean break approach**: No backward compatibility, migration
- [ ] testing before, during, and after refactoring
- [ ] Modularization with clear separation of concerns
- [ ] Improved code quality metrics (complexity, maintainability)
- [ ] documentation updates
- [ ] Type hints on all new APIs
- [ ] Error handling standardization
- [ ] Logging integration
- [ ] Performance validation (no regression)

## Standards Compliance Checklist

### Refactoring Standards ([`../../.cursorrules/refactoring.md`](../../.cursorrules/refactoring.md))
- [ ] Clean break approach (no backward compatibility)
- [ ] Modularization with single responsibility principle
- [ ] Testing during refactoring (full coverage maintained)
- [ ] Safety measures (incremental changes, rollback capability)
- [ ] Documentation updates during refactoring

### Code Quality Standards ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] Type hints on all new APIs
- [ ] Black formatting and isort compliance
- [ ] Google-style docstrings
- [ ] Error handling with custom exceptions
- [ ] Unified logging system

### Testing Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] No mocks policy maintained
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] data testing throughout refactoring
- [ ] Integration testing for refactored modules

## Example Usage

**Input:**
```
CODE TO REFACTOR: src/data_processor.py (monolithic 200-line function)
REFACTORING GOAL: Separate concerns into validator, transformer, and orchestrator classes
```

**Expected Output:**
- New modular classes: `DataValidator`, `DataTransformer`, `DataProcessor`
- test suite ensuring identical functionality
- Updated AGENTS.md and README.md documentation
- All callers updated to use new API
- Old monolithic code completely removed

## Related Documentation

- [`../../projects/project/docs/refactor_playbook.md`](../../projects/project/docs/refactor_playbook.md) - refactoring procedures
- [`../../projects/project/docs/refactor_hotspots.md`](../../projects/project/docs/refactor_hotspots.md) - Code quality analysis
- [`../../.cursorrules/refactoring.md`](../../.cursorrules/refactoring.md) - Clean break refactoring standards
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing during refactoring
```
