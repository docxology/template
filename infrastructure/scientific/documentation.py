"""Scientific documentation generation utilities.

Provides automatic documentation generation for scientific code:
- Function documentation from signatures and docstrings
- API documentation for modules
- Markdown-formatted scientific documentation
- Parameter and return value extraction
"""
from __future__ import annotations

import inspect
from typing import Callable, Any


def generate_scientific_documentation(func: Callable) -> str:
    """Generate scientific documentation for a function.

    Args:
        func: Function to document

    Returns:
        Markdown formatted scientific documentation
    """
    docstring = inspect.getdoc(func) or "No documentation available"
    signature = inspect.signature(func)

    # Extract parameter information
    parameters = []
    for param_name, param in signature.parameters.items():
        param_info = f"- `{param_name}`"
        if param.annotation != inspect.Parameter.empty:
            param_info += f" ({param.annotation.__name__})"
        if param.default != inspect.Parameter.empty:
            param_info += f", default: {param.default}"
        parameters.append(param_info)

    # Extract return information
    return_info = ""
    if signature.return_annotation != inspect.Signature.empty:
        return_info = f"Returns: {signature.return_annotation.__name__}"

    documentation = f"""## {func.__name__}

**Function**: `{func.__name__}{signature}`

### Description
{docstring}

### Parameters
{chr(10).join(parameters)}

### {return_info if return_info else 'Returns'}
No return annotation specified.

### Usage Example
```python
# Example usage would go here
result = {func.__name__}(example_input)
```

### Scientific Context
This function implements [mathematical concept] with [specific approach].
"""

    return documentation


def generate_api_documentation(module: Any) -> str:
    """Generate comprehensive API documentation for a scientific module.

    Args:
        module: Python module to document

    Returns:
        Markdown formatted API documentation
    """
    functions = []
    classes = []

    for name in dir(module):
        if name.startswith('_'):
            continue

        obj = getattr(module, name)
        if inspect.isfunction(obj):
            functions.append((name, obj))
        elif inspect.isclass(obj):
            classes.append((name, obj))

    doc = []
    doc.append(f"# {module.__name__} API Documentation")
    doc.append("")

    if functions:
        doc.append("## Functions")
        doc.append("")

        for name, func in functions:
            docstring = inspect.getdoc(func) or "No documentation available"
            signature = inspect.signature(func)

            doc.append(f"### `{name}`")
            doc.append(f"**Signature**: `{name}{signature}`")
            doc.append("")
            doc.append("**Description**:")
            doc.append(f"{docstring}")
            doc.append("")

    if classes:
        doc.append("## Classes")
        doc.append("")

        for name, cls in classes:
            docstring = inspect.getdoc(cls) or "No documentation available"

            doc.append(f"### `{name}`")
            doc.append("**Description**:")
            doc.append(f"{docstring}")
            doc.append("")

    return '\n'.join(doc)

