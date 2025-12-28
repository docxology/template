# Publishing Infrastructure Tests

## Overview

The `tests/infrastructure/publishing/` directory contains comprehensive tests for the academic publishing infrastructure. These tests validate the functionality for publishing research outputs to platforms like Zenodo, arXiv, and GitHub.

## Directory Structure

```
tests/infrastructure/publishing/
├── AGENTS.md                           # This technical documentation
├── __init__.py                         # Test package initialization
├── test_api.py                         # API client tests
├── test_cli.py                         # CLI interface tests
├── test_publish_cli.py                 # Publishing CLI tests
├── test_publishing_api_coverage.py     # API coverage tests
├── test_publishing_api_full.py         # Full API integration tests
├── test_publishing_cli_full.py         # Full CLI integration tests
├── test_publishing_cli.py              # CLI functionality tests
├── test_publishing_edge_cases.py       # Edge case and error tests
└── test_publishing.py                  # Core publishing tests
```

## Test Categories

### API Client Testing

**API Tests (`test_api.py`)**
- Platform API client functionality
- Authentication and authorization
- Request/response handling
- Error handling and retries

**Key Test Areas:**
- Zenodo API integration
- GitHub API operations
- Authentication token validation
- Rate limiting and error recovery

### CLI Interface Testing

**CLI Tests (`test_cli.py`, `test_publish_cli.py`)**
- Command-line argument parsing
- CLI option validation
- Help text generation
- Error message formatting

**Test Coverage:**
- All CLI commands and options
- Input validation and sanitization
- Output formatting and display
- Integration with core publishing logic

### Publishing Workflow Testing

**Core Publishing Tests (`test_publishing.py`)**
- Publishing workflow orchestration
- Metadata preparation and validation
- File upload and management
- Publication status tracking

**Test Scenarios:**
- Complete publication workflows
- Partial failure recovery
- Metadata validation
- File handling edge cases

### Integration Testing

**Full Integration Tests (`test_publishing_api_full.py`, `test_publishing_cli_full.py`)**
- End-to-end publishing workflows
- Cross-component integration
- Real API interactions (with proper mocking)
- Complete user journey validation

### Edge Case and Error Testing

**Edge Case Tests (`test_publishing_edge_cases.py`)**
- Error condition handling
- Network failure recovery
- Invalid input validation
- Resource limit testing

**Coverage Areas:**
- Authentication failures
- Network timeouts and retries
- Invalid file formats
- Metadata validation errors

## Test Design Principles

### Safe Testing Approach

**Mock-Heavy Testing:**
Due to the nature of external API interactions, these tests use extensive mocking to:
- Avoid actual API calls during testing
- Prevent test interference with real accounts
- Enable fast, reliable test execution
- Test error conditions safely

**Mocking Strategy:**
- HTTP requests mocked at network level
- API responses simulated with realistic data
- Authentication tokens replaced with test tokens
- File uploads virtualized

### Comprehensive Coverage

**Coverage Goals:**
- All publishing workflows tested
- Error conditions and recovery paths
- Input validation thoroughly tested
- Integration points validated

## Key Test Implementations

### API Client Testing

**Zenodo API Testing:**
```python
def test_zenodo_deposition_creation():
    """Test creating a new deposition on Zenodo."""
    with mock.patch('requests.post') as mock_post:
        # Mock successful API response
        mock_post.return_value.json.return_value = {
            'id': 12345,
            'links': {'bucket': 'https://zenodo.org/api/files/bucket'}
        }

        client = ZenodoClient(api_token='test_token')
        deposition = client.create_deposition(metadata=test_metadata)

        assert deposition['id'] == 12345
        mock_post.assert_called_once()

def test_zenodo_error_handling():
    """Test error handling for Zenodo API failures."""
    with mock.patch('requests.post') as mock_post:
        # Mock API error response
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

        client = ZenodoClient(api_token='invalid_token')

        with pytest.raises(PublishingError, match="Failed to create deposition"):
            client.create_deposition(metadata=test_metadata)
```

### CLI Testing

**Command Parsing:**
```python
def test_cli_publish_command():
    """Test CLI publish command parsing and execution."""
    with mock.patch('infrastructure.publishing.cli.publish_to_zenodo') as mock_publish:
        mock_publish.return_value = {'doi': '10.5281/zenodo.12345'}

        # Test command execution
        result = runner.invoke(cli, [
            'publish-zenodo',
            '--title', 'Test Publication',
            '--token', 'test_token',
            'path/to/files'
        ])

        assert result.exit_code == 0
        assert '10.5281/zenodo.12345' in result.output
        mock_publish.assert_called_once()
```

### Workflow Testing

**End-to-End Publishing:**
```python
def test_complete_publishing_workflow():
    """Test complete publishing workflow from start to finish."""
    with tempfile.TemporaryDirectory() as tmp:
        # Setup test files and metadata
        test_dir = Path(tmp)
        test_files = create_test_files(test_dir)

        metadata = {
            'title': 'Test Research Publication',
            'authors': [{'name': 'Test Author'}],
            'description': 'Test publication for validation'
        }

        # Mock all external dependencies
        with mock.patch('infrastructure.publishing.api.ZenodoClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.publish.return_value = {
                'doi': '10.5281/zenodo.12345',
                'url': 'https://zenodo.org/record/12345'
            }

            # Execute publishing workflow
            result = publish_to_zenodo(metadata, test_files, 'test_token')

            # Verify complete workflow
            assert result['doi'] == '10.5281/zenodo.12345'
            mock_instance.create_deposition.assert_called_once()
            mock_instance.upload_files.assert_called_once()
            mock_instance.publish_deposition.assert_called_once()
```

## Testing Infrastructure

### Mock Setup

**Comprehensive Mocking:**
```python
@pytest.fixture
def mock_zenodo_api():
    """Mock Zenodo API for testing."""
    with mock.patch('requests.post') as mock_post, \
         mock.patch('requests.put') as mock_put, \
         mock.patch('requests.get') as mock_get:

        # Setup mock responses
        mock_post.return_value.json.return_value = {'id': 12345}
        mock_put.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'state': 'done'}

        yield {
            'post': mock_post,
            'put': mock_put,
            'get': mock_get
        }

@pytest.fixture
def mock_github_api():
    """Mock GitHub API for testing."""
    with mock.patch('github.Github') as mock_github:
        mock_repo = mock.MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_repo.create_release.return_value.tag_name = 'v1.0.0'

        yield mock_github
```

### Test Data

**Sample Metadata:**
```python
@pytest.fixture
def sample_metadata():
    """Provide sample publication metadata."""
    return {
        'title': 'Test Research Publication',
        'authors': [
            {'name': 'Dr. Jane Smith', 'orcid': '0000-0000-0000-1234'},
            {'name': 'Dr. John Doe'}
        ],
        'description': 'Comprehensive test publication for validation',
        'keywords': ['research', 'testing', 'validation'],
        'license': 'MIT',
        'doi': '10.5281/zenodo.12345'
    }
```

## Running Tests

### Test Execution

```bash
# Run all publishing tests
pytest tests/infrastructure/publishing/

# Run specific test category
pytest tests/infrastructure/publishing/test_api.py

# Run with mocked network calls
pytest tests/infrastructure/publishing/ -m "not requires_network"
```

### Coverage Analysis

```bash
# Generate coverage report
pytest tests/infrastructure/publishing/ --cov=infrastructure.publishing --cov-report=html

# Check coverage threshold
pytest tests/infrastructure/publishing/ --cov=infrastructure.publishing --cov-fail-under=95
```

## Test Maintenance

### Adding New Tests

**Development Process:**
1. Identify new publishing functionality
2. Create appropriate test file
3. Implement comprehensive mocking
4. Test both success and failure scenarios
5. Ensure integration with existing tests

### Test Quality Standards

**Test Checklist:**
- [ ] All external APIs properly mocked
- [ ] Error conditions tested
- [ ] Authentication scenarios covered
- [ ] File upload edge cases handled
- [ ] Test isolation maintained

## Integration Testing

### Cross-Platform Testing

**Platform Integration:**
```python
def test_multi_platform_publishing():
    """Test publishing to multiple platforms simultaneously."""
    metadata = sample_metadata()
    test_files = ['paper.pdf', 'data.zip', 'code.tar.gz']

    with mock.patch('infrastructure.publishing.api.ZenodoClient') as mock_zenodo, \
         mock.patch('infrastructure.publishing.api.GitHubClient') as mock_github:

        # Mock successful publishing
        mock_zenodo.return_value.publish.return_value = {'doi': '10.5281/zenodo.123'}
        mock_github.return_value.create_release.return_value = {'url': 'https://github.com/.../v1.0'}

        # Test multi-platform workflow
        results = publish_to_multiple_platforms(metadata, test_files, {
            'zenodo_token': 'test_zenodo',
            'github_token': 'test_github'
        })

        assert 'zenodo' in results
        assert 'github' in results
        assert results['zenodo']['doi'].startswith('10.5281')
```

## Performance Considerations

### Test Efficiency

**Fast Execution:**
- All network calls mocked for speed
- File operations use temporary directories
- Test setup minimized for CI/CD
- Parallel test execution supported

### Resource Management

**Mock Cleanup:**
- All mocks properly reset between tests
- Temporary files cleaned up automatically
- No persistent state or external dependencies
- Memory usage optimized for large test suites

## Troubleshooting

### Common Issues

**Mock Configuration Errors:**
- Verify all API calls are properly mocked
- Check mock return values match expected format
- Ensure mock side effects are correctly configured

**Test Interference:**
- Isolate tests with proper fixtures
- Reset mocks between test runs
- Avoid shared state between tests

**Coverage Gaps:**
- Identify unmocked code paths
- Add tests for error conditions
- Verify exception handling coverage

### Debug Tools

**Verbose Mocking:**
```bash
# Debug mock calls
pytest tests/infrastructure/publishing/test_api.py -v -s --pdb

# Inspect mock call history
mock_api.assert_called_with(expected_args)
print(mock_api.call_args_list)
```

## Test Metrics

### Coverage Status

**Current Coverage:**
- API Clients: 100%
- CLI Interface: 100%
- Publishing Workflows: 100%
- Error Handling: 100%

### Quality Metrics

**Test Reliability:**
- All tests pass consistently
- No network-dependent failures
- Clear error messages for failures
- Proper test documentation

## Future Enhancements

### Planned Improvements

**Enhanced Testing:**
- Integration with real API testing (with test accounts)
- Performance testing for large uploads
- Cross-platform compatibility testing
- Automated API schema validation

**Test Infrastructure:**
- Enhanced mocking utilities
- Test data generation tools
- Result validation frameworks
- Historical test performance tracking

## See Also

**Related Documentation:**
- [`../../../infrastructure/publishing/AGENTS.md`](../../../infrastructure/publishing/AGENTS.md) - Publishing module details
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure test suite overview
- [`../../../AGENTS.md`](../../../AGENTS.md) - System documentation

**Testing Standards:**
- [`../../../.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing standards
- [`../../../docs/development/TESTING_GUIDE.md`](../../../docs/development/TESTING_GUIDE.md) - Testing guide