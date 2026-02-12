# Tests - Blake Active Inference

## Purpose

Comprehensive test suite validating visualization generation and manuscript consistency.

## Test Modules

### `test_visualization.py`

Tests for all figure generation functions.

**Test Classes:**

| Class | Purpose |
|-------|---------|
| `TestVisualizationModule` | Core figure generation validation |
| `TestBlakeQuotations` | Quotation source accuracy |
| `TestFontSizeEnforcement` | 11pt minimum font compliance |
| `TestThematicAtlasFigure` | Atlas figure tests |
| `TestNewtonsSleepFigure` | Prior dominance figure tests |
| `TestFourZoasFigure` | Factorized model figure tests |
| `TestTemporalHorizonsFigure` | Temporal depth figure tests |
| `TestCollectiveJerusalemFigure` | Multi-agent figure tests |
| `TestUnicodeSubscripts` | LaTeX compatibility check |

### `test_manuscript.py`

Tests for manuscript structure and content consistency.

**Test Classes:**

| Class | Purpose |
|-------|---------|
| `TestThemeCountConsistency` | Verifies all 8 themes are consistently referenced |
| `TestCitationIntegrity` | All citations resolve to bibliography |
| `TestFigureIntegrity` | All referenced figures exist |
| `TestManuscriptStructure` | Required files present and non-empty |
| `TestSectionNumbering` | Section sequence validation |
| `TestCrossReferences` | Anchor uniqueness |
| `TestFigureQuality` | Figure resolution (min 50KB) |
| `TestPDFOutput` | PDF generation validation |
| `TestMarkdownFormatting` | Style consistency checks |

## Running Tests

```bash
# From repository root
uv run pytest projects/blake_active_inference/tests/ -v

# With coverage
uv run pytest projects/blake_active_inference/tests/ --cov=projects/blake_active_inference/src

# Specific test file
uv run pytest projects/blake_active_inference/tests/test_manuscript.py -v
```

## Test Counts

- `test_visualization.py`: 30 tests
- `test_manuscript.py`: 22 tests
- **Total**: 52 tests
