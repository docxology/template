# Advanced Modules Usage Guide

> **Comprehensive guide** for using all 6 advanced `src/` modules

**Quick Reference:** [API Reference](API_REFERENCE.md) | [Source Code Docs](../src/AGENTS.md) | [Advanced Usage](ADVANCED_USAGE.md)

This guide provides detailed documentation for using the advanced modules in the Research Project Template. These modules provide powerful capabilities for quality analysis, reproducibility, integrity verification, publishing workflows, scientific development, and build verification.

## Overview

The template includes 6 advanced modules that extend core functionality:

1. **Quality Checker** - Document quality analysis and metrics
2. **Reproducibility** - Environment tracking and build manifests
3. **Integrity** - File integrity and cross-reference validation
4. **Publishing** - Academic publishing workflow assistance
5. **Scientific Dev** - Scientific computing best practices
6. **Build Verifier** - Build process validation and verification

All modules follow the **thin orchestrator pattern** and maintain **100% test coverage**.

---

## Module 1: Quality Checker (`quality_checker.py`)

### Overview

The Quality Checker module provides comprehensive document quality analysis including readability metrics, structural analysis, and academic standards compliance checking.

**Use Cases:**
- Analyze document readability before publication
- Verify academic writing standards compliance
- Check document structure and formatting quality
- Generate quality reports for manuscripts

### Key Functions

#### `analyze_document_quality(pdf_path, text=None)`

Analyzes a complete document and returns quality metrics.

```python
from pathlib import Path
from quality_checker import analyze_document_quality

pdf_path = Path("output/pdf/project_combined.pdf")
metrics = analyze_document_quality(pdf_path)

print(f"Readability Score: {metrics.readability_score:.2f}")
print(f"Academic Compliance: {metrics.academic_compliance:.2f}")
print(f"Overall Score: {metrics.overall_score:.2f}")
```

**Returns:** `QualityMetrics` object with:
- `readability_score` - Flesch and Gunning Fog metrics
- `academic_compliance` - Compliance with academic standards
- `structural_integrity` - Document organization quality
- `formatting_quality` - Styling consistency
- `overall_score` - Composite quality score
- `issues` - List of detected issues
- `recommendations` - Improvement suggestions

#### `analyze_readability(text)`

Analyzes text readability using multiple metrics.

```python
from quality_checker import analyze_readability

text = "Your document text here..."
metrics = analyze_readability(text)

print(f"Flesch Score: {metrics['flesch_score']:.2f}")
print(f"Gunning Fog Index: {metrics['gunning_fog']:.2f}")
```

**Returns:** Dictionary with `flesch_score`, `gunning_fog`, `avg_sentence_length`, `avg_syllables_per_word`

#### `generate_quality_report(metrics)`

Generates a formatted quality report.

```python
from quality_checker import analyze_document_quality, generate_quality_report

metrics = analyze_document_quality(pdf_path)
report = generate_quality_report(metrics)
print(report)
```

### Integration Examples

#### Example 1: Quality Check Script

```python
#!/usr/bin/env python3
"""Script to check document quality."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quality_checker import analyze_document_quality, generate_quality_report

def main():
    pdf_path = Path("output/pdf/project_combined.pdf")
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return 1
    
    metrics = analyze_document_quality(pdf_path)
    report = generate_quality_report(metrics)
    
    print(report)
    
    if metrics.overall_score < 0.7:
        print("\n⚠️  Warning: Document quality below threshold")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Run quality checks before publication** - Ensure documents meet standards
2. **Set quality thresholds** - Define minimum scores for acceptance
3. **Review recommendations** - Address issues identified by the checker
4. **Track quality over time** - Monitor improvements across versions

### Troubleshooting

**Issue:** Quality scores seem too low
- **Solution:** Check if document has proper structure (abstract, introduction, etc.)
- **Solution:** Review readability metrics for overly complex sentences

**Issue:** PDF extraction fails
- **Solution:** Ensure PDF is not password-protected
- **Solution:** Verify PDF file is not corrupted

---

## Module 2: Reproducibility (`reproducibility.py`)

### Overview

The Reproducibility module provides tools for ensuring deterministic and verifiable research results through environment tracking, dependency management, and build verification.

**Use Cases:**
- Capture environment state for reproducibility
- Generate build manifests
- Verify experiment reproducibility
- Create reproducible environments

### Key Functions

#### `generate_reproducibility_report(output_dir)`

Generates a comprehensive reproducibility report.

```python
from pathlib import Path
from reproducibility import generate_reproducibility_report, save_reproducibility_report

output_dir = Path("output")
report = generate_reproducibility_report(output_dir)

# Save report
save_reproducibility_report(report, output_dir / "reproducibility.json")

print(f"Environment Hash: {report.environment_hash}")
print(f"Dependency Hash: {report.dependency_hash}")
print(f"Code Hash: {report.code_hash}")
```

**Returns:** `ReproducibilityReport` object with environment, dependency, code, and data hashes

#### `capture_environment_state()`

Captures current environment state.

```python
from reproducibility import capture_environment_state

env_state = capture_environment_state()
print(f"Python Version: {env_state['platform']['python_version']}")
print(f"Platform: {env_state['platform']['system']}")
```

**Returns:** Dictionary with platform info, environment variables, and directory contents

#### `verify_reproducibility(current_report, baseline_report)`

Verifies reproducibility by comparing reports.

```python
from reproducibility import load_reproducibility_report, verify_reproducibility

current = load_reproducibility_report(Path("current_report.json"))
baseline = load_reproducibility_report(Path("baseline_report.json"))

result = verify_reproducibility(current, baseline)

if result['reproducible']:
    print("✅ Builds are reproducible")
else:
    print("⚠️  Differences detected:", result['differences'])
```

### Integration Examples

#### Example 1: Reproducibility Check Script

```python
#!/usr/bin/env python3
"""Script to verify build reproducibility."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reproducibility import (
    generate_reproducibility_report,
    save_reproducibility_report,
    verify_reproducibility,
    load_reproducibility_report
)

def main():
    output_dir = Path("output")
    
    # Generate current report
    current_report = generate_reproducibility_report(output_dir)
    save_reproducibility_report(current_report, output_dir / "reproducibility_current.json")
    
    # Compare with baseline if exists
    baseline_path = output_dir / "reproducibility_baseline.json"
    if baseline_path.exists():
        baseline_report = load_reproducibility_report(baseline_path)
        result = verify_reproducibility(current_report, baseline_report)
        
        if result['reproducible']:
            print("✅ Build is reproducible")
            return 0
        else:
            print("⚠️  Reproducibility issues detected")
            for diff in result['differences']:
                print(f"  - {diff}")
            return 1
    
    # Save as baseline for first run
    save_reproducibility_report(current_report, baseline_path)
    print("✅ Baseline report saved")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Generate reports after each build** - Track environment changes
2. **Store baseline reports** - Use for reproducibility verification
3. **Version control reports** - Track changes over time
4. **Automate checks** - Integrate into build pipeline

### Troubleshooting

**Issue:** Dependency hash differs
- **Solution:** Ensure `uv.lock` is committed and up-to-date
- **Solution:** Check for environment variable differences

**Issue:** Code hash differs
- **Solution:** Verify all source files are committed
- **Solution:** Check for uncommitted changes

---

## Module 3: Integrity (`integrity.py`)

### Overview

The Integrity module provides utilities for ensuring research output validity through file integrity checking, cross-reference validation, and data consistency verification.

**Use Cases:**
- Verify output file integrity
- Validate cross-references in markdown
- Check data file consistency
- Ensure build artifact completeness

### Key Functions

#### `verify_output_integrity(output_dir)`

Performs comprehensive integrity verification.

```python
from pathlib import Path
from integrity import verify_output_integrity, generate_integrity_report

output_dir = Path("output")
report = verify_output_integrity(output_dir)

if report.overall_integrity:
    print("✅ All integrity checks passed")
else:
    print("⚠️  Integrity issues detected:")
    for issue in report.issues:
        print(f"  - {issue}")
```

**Returns:** `IntegrityReport` object with verification results

#### `verify_cross_references(markdown_files)`

Validates cross-reference integrity.

```python
from pathlib import Path
from integrity import verify_cross_references

markdown_files = list(Path("manuscript").glob("*.md"))
integrity = verify_cross_references(markdown_files)

if all(integrity.values()):
    print("✅ All cross-references valid")
else:
    print("⚠️  Cross-reference issues:")
    for ref_type, valid in integrity.items():
        if not valid:
            print(f"  - {ref_type}")
```

**Returns:** Dictionary mapping reference types to validity status

#### `verify_file_integrity(file_paths, expected_hashes=None)`

Verifies file integrity using hash comparison.

```python
from pathlib import Path
from integrity import verify_file_integrity

pdf_files = list(Path("output/pdf").glob("*.pdf"))
integrity = verify_file_integrity(pdf_files)

for file_path, valid in integrity.items():
    if valid:
        print(f"✅ {file_path}")
    else:
        print(f"⚠️  {file_path} - integrity check failed")
```

### Integration Examples

#### Example 1: Integrity Verification Script

```python
#!/usr/bin/env python3
"""Script to verify output integrity."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrity import verify_output_integrity, generate_integrity_report

def main():
    output_dir = Path("output")
    
    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        return 1
    
    report = verify_output_integrity(output_dir)
    report_text = generate_integrity_report(report)
    
    print(report_text)
    
    if not report.overall_integrity:
        print("\n⚠️  Integrity checks failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Run integrity checks after builds** - Verify output quality
2. **Store integrity manifests** - Track file hashes over time
3. **Validate cross-references** - Ensure document consistency
4. **Check data consistency** - Verify data file integrity

### Troubleshooting

**Issue:** Cross-references fail validation
- **Solution:** Check label spelling matches references exactly
- **Solution:** Ensure all referenced sections exist

**Issue:** File integrity checks fail
- **Solution:** Verify files are not corrupted
- **Solution:** Check file permissions

---

## Module 4: Publishing (`publishing.py`)

### Overview

The Publishing module provides academic publishing workflow assistance including DOI validation, citation generation, publication metadata handling, and repository integration.

**Use Cases:**
- Extract publication metadata from manuscripts
- Generate citations in multiple formats (BibTeX, APA, MLA)
- Validate DOI format
- Create publication packages
- Generate submission checklists

### Key Functions

#### `extract_publication_metadata(markdown_files)`

Extracts publication metadata from markdown files.

```python
from pathlib import Path
from publishing import extract_publication_metadata

markdown_files = list(Path("manuscript").glob("*.md"))
metadata = extract_publication_metadata(markdown_files)

print(f"Title: {metadata.title}")
print(f"Authors: {', '.join(metadata.authors)}")
print(f"DOI: {metadata.doi}")
```

**Returns:** `PublicationMetadata` object with extracted information

#### `generate_citation_bibtex(metadata)`

Generates BibTeX citation.

```python
from publishing import extract_publication_metadata, generate_citation_bibtex

metadata = extract_publication_metadata(markdown_files)
bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

**Returns:** BibTeX-formatted citation string

#### `validate_doi(doi)`

Validates DOI format and checksum.

```python
from publishing import validate_doi

doi = "10.5281/zenodo.12345678"
if validate_doi(doi):
    print("✅ Valid DOI")
else:
    print("⚠️  Invalid DOI format")
```

**Returns:** Boolean indicating DOI validity

#### `create_publication_package(output_dir, metadata)`

Creates a complete publication package.

```python
from pathlib import Path
from publishing import extract_publication_metadata, create_publication_package

metadata = extract_publication_metadata(markdown_files)
package = create_publication_package(Path("output"), metadata)

print(f"Package created: {package['package_path']}")
print(f"Files included: {len(package['files'])}")
```

### Integration Examples

#### Example 1: Publication Package Generator

```python
#!/usr/bin/env python3
"""Script to create publication package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from publishing import (
    extract_publication_metadata,
    create_publication_package,
    generate_citation_bibtex,
    generate_citation_apa
)

def main():
    markdown_files = list(Path("manuscript").glob("*.md"))
    output_dir = Path("output")
    
    # Extract metadata
    metadata = extract_publication_metadata(markdown_files)
    
    # Generate citations
    bibtex = generate_citation_bibtex(metadata)
    apa = generate_citation_apa(metadata)
    
    print("BibTeX Citation:")
    print(bibtex)
    print("\nAPA Citation:")
    print(apa)
    
    # Create package
    package = create_publication_package(output_dir, metadata)
    print(f"\n✅ Publication package created: {package['package_path']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Extract metadata early** - Use in manuscript generation
2. **Validate DOIs** - Ensure proper format before publication
3. **Generate all citation formats** - Support multiple citation styles
4. **Create packages before submission** - Include all required files

### Troubleshooting

**Issue:** Metadata extraction incomplete
- **Solution:** Ensure markdown files have proper headers
- **Solution:** Check for author information in expected format

**Issue:** DOI validation fails
- **Solution:** Verify DOI format (e.g., `10.5281/zenodo.12345678`)
- **Solution:** Check DOI checksum calculation

---

## Module 5: Scientific Dev (`scientific_dev.py`)

### Overview

The Scientific Dev module provides scientific computing best practices including numerical stability checking, performance benchmarking, documentation generation, and scientific workflow templates.

**Use Cases:**
- Check numerical stability of algorithms
- Benchmark function performance
- Generate scientific API documentation
- Validate scientific implementations
- Create reproducible experiment templates

### Key Functions

#### `check_numerical_stability(func, test_inputs, tolerance=1e-12)`

Checks numerical stability of a function.

```python
from scientific_dev import check_numerical_stability
import numpy as np

def my_algorithm(x):
    return x ** 2 / (x + 1e-10)

test_inputs = np.linspace(-10, 10, 100)
stability = check_numerical_stability(my_algorithm, test_inputs)

print(f"Stability Score: {stability.stability_score:.2f}")
print(f"Behavior: {stability.actual_behavior}")
for rec in stability.recommendations:
    print(f"  - {rec}")
```

**Returns:** `StabilityTest` object with analysis results

#### `benchmark_function(func, test_inputs, iterations=100)`

Benchmarks function performance.

```python
from scientific_dev import benchmark_function
import numpy as np

def compute_statistics(data):
    return np.mean(data), np.std(data)

test_inputs = [np.random.rand(1000) for _ in range(10)]
result = benchmark_function(compute_statistics, test_inputs, iterations=50)

print(f"Function: {result.function_name}")
print(f"Execution Time: {result.execution_time:.4f}s")
print(f"Iterations: {result.iterations}")
```

**Returns:** `BenchmarkResult` object with performance metrics

#### `validate_scientific_implementation(func, test_cases)`

Validates scientific implementation correctness.

```python
from scientific_dev import validate_scientific_implementation

def linear_regression(x, y):
    # Implementation here
    pass

test_cases = [
    ([1, 2, 3], [2, 4, 6], 2.0),  # Should return slope ~2
    ([0, 1, 2], [1, 2, 3], 1.0),  # Should return slope ~1
]

result = validate_scientific_implementation(linear_regression, test_cases)
print(f"Validation Passed: {result['all_passed']}")
```

### Integration Examples

#### Example 1: Scientific Validation Script

```python
#!/usr/bin/env python3
"""Script to validate scientific implementation."""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scientific_dev import (
    check_numerical_stability,
    benchmark_function,
    validate_scientific_implementation
)

def my_algorithm(x):
    """Example algorithm to validate."""
    return np.sin(x) / x

def main():
    # Test numerical stability
    test_inputs = np.linspace(-np.pi, np.pi, 1000)
    stability = check_numerical_stability(my_algorithm, test_inputs)
    
    print(f"Numerical Stability Score: {stability.stability_score:.2f}")
    if stability.stability_score < 0.8:
        print("⚠️  Stability issues detected")
        for rec in stability.recommendations:
            print(f"  - {rec}")
    
    # Benchmark performance
    benchmark = benchmark_function(my_algorithm, test_inputs[:10], iterations=100)
    print(f"\nPerformance: {benchmark.execution_time:.4f}s")
    
    return 0 if stability.stability_score >= 0.8 else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Test numerical stability** - Ensure algorithms handle edge cases
2. **Benchmark performance** - Monitor execution time
3. **Validate implementations** - Verify correctness with test cases
4. **Document scientific APIs** - Generate comprehensive documentation

### Troubleshooting

**Issue:** Stability score is low
- **Solution:** Add input validation and error handling
- **Solution:** Check for NaN/inf values in calculations

**Issue:** Benchmark results inconsistent
- **Solution:** Increase iteration count for more reliable results
- **Solution:** Warm up functions before benchmarking

---

## Module 6: Build Verifier (`build_verifier.py`)

### Overview

The Build Verifier module provides comprehensive build verification including artifact verification, output consistency checking, build process validation, and reproducibility testing.

**Use Cases:**
- Verify build artifacts are correct
- Validate build reproducibility
- Check build environment consistency
- Generate build verification reports

### Key Functions

#### `verify_build_artifacts(output_dir, expected_files)`

Verifies that expected build artifacts are present.

```python
from pathlib import Path
from build_verifier import verify_build_artifacts

output_dir = Path("output")
expected_files = {
    "pdf": ["01_abstract.pdf", "project_combined.pdf"],
    "figures": ["example_figure.png"],
    "data": ["example_data.csv"]
}

result = verify_build_artifacts(output_dir, expected_files)

if result['verification_passed']:
    print("✅ All artifacts present")
else:
    print("⚠️  Missing files:", result['missing_files'])
```

**Returns:** Dictionary with verification results

#### `verify_build_reproducibility(build_command, expected_outputs, iterations=3)`

Verifies build reproducibility by running builds multiple times.

```python
from build_verifier import verify_build_reproducibility

build_command = ["./repo_utilities/render_pdf.sh"]
expected_outputs = {
    "output/pdf/project_combined.pdf": "expected_hash"
}

result = verify_build_reproducibility(build_command, expected_outputs, iterations=3)

if result['consistent_results']:
    print("✅ Build is reproducible")
else:
    print("⚠️  Reproducibility issues detected")
```

**Returns:** Dictionary with reproducibility verification results

#### `verify_build_environment()`

Validates build environment.

```python
from build_verifier import verify_build_environment

env = verify_build_environment()

if env['all_available']:
    print("✅ All required tools available")
else:
    print("⚠️  Missing tools:", env['missing_tools'])
```

### Integration Examples

#### Example 1: Build Verification Script

```python
#!/usr/bin/env python3
"""Script to verify build artifacts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build_verifier import (
    verify_build_artifacts,
    verify_build_environment,
    create_build_verification_script
)

def main():
    output_dir = Path("output")
    
    # Check environment
    env = verify_build_environment()
    if not env['all_available']:
        print("⚠️  Missing required tools")
        return 1
    
    # Verify artifacts
    expected_files = {
        "pdf": ["project_combined.pdf"],
        "figures": ["example_figure.png"],
        "data": ["example_data.csv"]
    }
    
    result = verify_build_artifacts(output_dir, expected_files)
    
    if result['verification_passed']:
        print("✅ Build verification passed")
        return 0
    else:
        print("⚠️  Build verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Best Practices

1. **Verify after each build** - Ensure artifacts are correct
2. **Test reproducibility** - Run builds multiple times
3. **Check environment** - Validate required tools are available
4. **Generate reports** - Document verification results

### Troubleshooting

**Issue:** Artifacts missing
- **Solution:** Check build completed successfully
- **Solution:** Verify expected file names match actual files

**Issue:** Build not reproducible
- **Solution:** Check for non-deterministic operations
- **Solution:** Verify random seed usage

---

## Summary

All advanced modules provide powerful capabilities for research projects:

- **Quality Checker** - Document quality analysis
- **Reproducibility** - Environment and build tracking
- **Integrity** - Output verification
- **Publishing** - Academic workflow assistance
- **Scientific Dev** - Scientific computing best practices
- **Build Verifier** - Build process validation

For detailed API documentation, see [API Reference](API_REFERENCE.md).

For source code details, see [Source Code Documentation](../src/AGENTS.md).

---

**Related Documentation:**
- [Advanced Usage Guide](ADVANCED_USAGE.md) - Complete advanced workflow
- [API Reference](API_REFERENCE.md) - Detailed function documentation
- [Best Practices](BEST_PRACTICES.md) - Usage recommendations
- [Source Code Docs](../src/AGENTS.md) - Module implementation details

