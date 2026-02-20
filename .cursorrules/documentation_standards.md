# Documentation Standards and Guidelines

## Overview

Every directory in the repository must have two documentation files:

1. **AGENTS.md** - documentation (detailed)
2. **README.md** - Quick reference guide (concise)

This ensures information is available while also providing fast lookup.

## Documentation Purpose

### AGENTS.md - Guide

**Purpose**:, detailed documentation for understanding and working with the code.

**Audience**: Developers who need deep understanding, AI agents seeking implementation details.

**Length**: As long as needed to be thorough (typically 100-500+ lines).

**Updates**: When features or architecture changes.

### README.md - Quick Reference

**Purpose**: Fast lookup of common tasks and key information.

**Audience**: Developers who need quick answers, first-time users.

**Length**: Concise, typically 50-150 lines.

**Updates**: When quick-start commands or key features change.

## AGENTS.md Structure

### Recommended Section Order

1. **Overview** (50-100 words)
   - What is this module/directory?
   - Why does it exist?
   - Who should use it?

2. **Key Concepts** (optional)
   - Terminology specific to this module
   - Architecture overview
   - Important principles

3. **File Organization**
   - Directory structure
   - Purpose of each file

4. **Installation/Setup** (if applicable)
   - Prerequisites
   - Installation steps
   - Configuration

5. **Usage Examples**
   - Common tasks with code samples
   - Real-world scenarios
   - Copy-paste ready examples

6. **Configuration** (if applicable)
   - All configuration options
   - Environment variables
   - Config file format

7. **Testing** (for modules with tests)
   - How to run tests
   - Test structure
   - Writing tests

8. **API Reference** (for modules)
   - Key classes and functions
   - Import statements
   - Parameters and returns

9. **Troubleshooting**
   - Common issues
   - Solutions
   - Debug tips

10. **Best Practices**
    - Do's and don'ts
    - Performance tips
    - Security considerations

11. **See Also / References**
    - Related documentation
    - External resources
    - Cross-references

### AGENTS.md Template

```markdown
# [Module/Directory Name] Documentation

## Overview

[2-3 sentences: what is this, why does it exist, who uses it]

## Quick Summary

[Optional: 1-2 key facts highlighted]

## Directory Structure

[File/folder layout with descriptions]

## Installation & Setup

[Steps to get started]

## Usage Examples

### Example 1: [Common Task]

[Code example with explanation]

## Configuration

[All configuration options]

## Testing

[How to run tests]

## API Reference

[Key functions/classes]

## Best Practices

- ✅ Do this
- ❌ Don't do this

## Troubleshooting

[Common issues and solutions]

## See Also

- [Related Module](../infrastructure/AGENTS.md) - Infrastructure documentation
- [External Resource](https://example.com) - External documentation
```

## README.md Structure

### Recommended Section Order

1. **Title** - One-line description
2. **Quick Start** - Minimal working example
3. **Key Features** - 3-5 bullet points
4. **Installation** - Copy-paste commands
5. **Common Commands** - 3-5 most used tasks
6. **More Information** - Link to AGENTS.md

### README.md Template

```markdown
# [Module Name]

[One-line description]

## Quick Start

[Minimal working example, 5-10 lines of code]

## Key Features

- Feature 1
- Feature 2
- Feature 3

## Installation

[Copy-paste ready command]

## Common Commands

### Task 1
\`\`\`bash
command here
\`\`\`

### Task 2
\`\`\`bash
command here
\`\`\`

## More Information

See [AGENTS.md](AGENTS.md) for documentation.
```

## Code Documentation Standards

### Module Docstrings

Every Python module should start with a docstring:

```python
"""Module name and one-line description.

Detailed description of what this module does, including key classes
and functions it provides. Explain the purpose and main use cases.

Example:
    Import and use the main class:
    
        from module import MainClass
        obj = MainClass()
        result = obj.method()

Attributes:
    CONSTANT: Description
    
Classes:
    MainClass: Main functionality
    
Functions:
    helper_function: Helper description
"""
```

### Class Docstrings

```python
class ClassName:
    """One-line summary of the class.
    
    Detailed description of what the class does, its purpose,
    and how it should be used.
    
    Attributes:
        attribute1 (str): Description
        attribute2 (int): Description
        
    Example:
        >>> obj = ClassName()
        >>> obj.method()
        'result'
    """
    
    def __init__(self, param: str) -> None:
        """Initialize the class.
        
        Args:
            param: Description
        """
```

### Function Docstrings

```python
def function_name(param1: str, param2: int = 10) -> str:
    """One-line summary (imperative form: "Do something").
    
    Detailed description explaining what the function does,
    why you would use it, and any important behavior.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 10)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> result = function_name("input", 5)
        >>> print(result)
        'output'
        
    Note:
        This function requires X permission.
        
    See Also:
        related_function: For similar operation
    """
```

## Writing Guidelines

### 1. Use Active Voice

```
✅ GOOD: "The module validates user input"
❌ BAD:  "User input is validated by the module"
```

### 2. Be Specific

```
✅ GOOD: "Returns a list of dictionaries containing user IDs and names"
❌ BAD:  "Returns a list"
```

### 3. Use Examples

Show, don't just tell:

```python
# ✅ GOOD: Show what you mean
def process_data(data: List[str]) -> List[str]:
    """Convert strings to uppercase.
    
    Example:
        >>> process_data(["hello", "world"])
        ['HELLO', 'WORLD']
    """

# ❌ BAD: No examples
def process_data(data: List[str]) -> List[str]:
    """Process the data."""
```

### 4. Document Edge Cases

```python
def divide(a: int, b: int) -> float:
    """Divide a by b.
    
    Note:
        Returns inf if b is 0 (doesn't raise error).
    """
```

### 5. Explain the "Why"

```
✅ GOOD: "We validate email format early to provide immediate user feedback"
❌ BAD:  "We validate email format"
```

## Code Example Guidelines

### Copy-Paste Ready

Examples should be immediately runnable:

```python
# ✅ GOOD: Can copy-paste and run
from module import MyClass

obj = MyClass("data")
result = obj.process()
print(result)

# ❌ BAD: Incomplete, won't run
from module import MyClass
# ... setup here ...
result.process()
```

### Progressive Complexity

Start simple, then show advanced:

```
1. Basic usage
2. Common options
3. Advanced configuration
4. Error handling
```

### Realistic Data

Use real-world-like examples:

```python
# ✅ GOOD: Realistic example
users = [
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25, "email": "bob@example.com"},
]
for user in users:
    print(f"{user['name']}: {user['email']}")

# ❌ BAD: Unrealistic placeholder
users = [{"n": "a", "e": "e"}]
```

## Cross-References

### Internal Links

Link between related documentation:

```markdown
# Link to directory doc
See [infrastructure/AGENTS.md](../infrastructure/AGENTS.md)

# Link within same directory
See [README.md](README.md) for quick start

# Link to parent AGENTS.md
See [../AGENTS.md](../AGENTS.md) for overview
```

### "See Also" Sections

```markdown
## See Also

- [Related Module](../infrastructure/AGENTS.md) - Infrastructure documentation
- [External Resource](https://example.com) - External documentation
- [Configuration Guide](configuration.md) - Configuration documentation
```

## Format Standards

### Markdown Headings

- Use `#` for main title (AGENTS.md: document title)
- Use `##` for major sections
- Use `###` for subsections
- Use `####` for sub-subsections
- Don't go deeper than 4 levels

### Lists

```markdown
# Ordered lists for sequences
1. First step
2. Second step
3. Third step

# Bullet lists for options
- Option 1
- Option 2
- Option 3

# Nested lists with indentation
- Category
  - Subcategory
    - Item
```

### Code Blocks

```markdown
# Python code
\`\`\`python
code here
\`\`\`

# Bash commands
\`\`\`bash
command here
\`\`\`

# Output/Terminal
\`\`\`
output here
\`\`\`
```

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

## Maintenance Guidelines

### Update AGENTS.md When

- Architecture changes
- features added
- API changes
- Best practices discovered
- Examples become outdated

### Update README.md When

- Installation changes
- Quick start becomes outdated
- New common commands discovered
- Key features change

### Keep in Sync

Both files should reference:
- Same core concepts (but different depth)
- Same latest API (even if README is less detailed)
- Same project structure

## Documentation Checklist

Before committing documentation:

- [ ] AGENTS.md covers all major features
- [ ] README.md has working quick-start example
- [ ] All code examples are runnable
- [ ] Links are correct and working
- [ ] No outdated references
- [ ] Consistent terminology used
- [ ] Clear section hierarchy (headings)
- [ ] Examples are realistic
- [ ] Error conditions documented
- [ ] Cross-references to related docs included

## Common Mistakes to Avoid

1. **Outdated Examples** - Keep code examples current with API
2. **Missing Error Handling** - Show how to handle errors
3. **Insufficient Detail** - Explain the "why", not just "what"
4. **No Examples** - Include working code samples
5. **Broken Links** - Verify all internal links
6. **Inconsistent Terminology** - Use same terms throughout
7. **No See Also** - Link to related documentation
8. **Poor Organization** - Use consistent heading structure
9. **Overly Long README** - Keep it short; use AGENTS.md for details
10. **No Configuration Docs** - Document all config options

## Template Repository Examples

### Good AGENTS.md References

- [infrastructure/AGENTS.md](../infrastructure/AGENTS.md) - module docs
- [act_inf_metaanalysis/AGENTS.md](../projects/act_inf_metaanalysis/AGENTS.md) - Project code docs
- [tests/AGENTS.md](../tests/AGENTS.md) - Test framework docs

### Good README.md References

- [infrastructure/README.md](../infrastructure/README.md) - Quick patterns
- [scripts/README.md](../scripts/README.md) - Quick commands
- [act_inf_metaanalysis/README.md](../projects/act_inf_metaanalysis/README.md) - Project quick start

## See Also

- [testing_standards.md](testing_standards.md) - Document tests properly
- [type_hints_standards.md](type_hints_standards.md) - Type hint documentation
- [../docs/documentation-index.md](../docs/documentation-index.md) - documentation index
- [../docs/AGENTS.md](../docs/AGENTS.md) - Main project documentation
- [../AGENTS.md](../AGENTS.md) - Root documentation
- [../docs/core/architecture.md](../docs/core/architecture.md) - System architecture
