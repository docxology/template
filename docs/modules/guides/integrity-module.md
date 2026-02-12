# Integrity & Validation Module

> **File integrity and cross-reference validation**

**Location:** `infrastructure/validation/integrity.py`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **File Integrity**: SHA256-based verification of output files
- **Cross-Reference Validation**: LaTeX reference integrity checking
- **Data Consistency**: Format and structure validation
- **Academic Standards**: Compliance with writing standards
- **Build Artifact Verification**: output validation

---

## Usage Examples

### Integrity Check

```python
from infrastructure.validation.integrity import verify_output_integrity

# Verify entire output directory
report = verify_output_integrity("output/")

if report.overall_integrity:
    print("✅ All integrity checks passed")
else:
    print("❌ Integrity issues found:")
    for issue in report.issues:
        print(f"- {issue}")
    for warning in report.warnings:
        print(f"⚠️ {warning}")
```

### Cross-Reference Validation

```python
from infrastructure.validation.integrity import verify_cross_references

# Check markdown files for reference integrity
markdown_files = ["manuscript/01_abstract.md", "manuscript/02_introduction.md"]
integrity_status = verify_cross_references(markdown_files)

for ref_type, is_valid in integrity_status.items():
    status = "✅" if is_valid else "❌"
    print(f"{status} {ref_type}")
```

---

## CLI Integration

```bash
# Automatic integrity validation
python3 scripts/04_validate_output.py

# Manual integrity check
python3 -m infrastructure.validation.integrity.cli output/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File hash mismatches | Check if outputs are deterministic |
| Cross-reference errors | Verify all labels are properly defined |
| Data format issues | Ensure consistent data serialization |

---

**Related:** [Publishing Module](publishing-module.md) | [Reporting Module](reporting-module.md)
