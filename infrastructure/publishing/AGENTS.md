# Publishing Module

## Purpose

The Publishing module provides tools for academic publishing workflows. It enables DOI management, citation generation in multiple formats, publication metadata extraction, and automated publishing to major academic platforms (Zenodo, arXiv, GitHub).

## Architecture

### Core Components

**core.py**
- Publication metadata extraction and management
- DOI validation and formatting
- Citation generation (BibTeX, APA, MLA formats)
- Publication package creation
- Submission checklist generation
- Academic standards compliance
- Publication metrics and complexity analysis
- Repository metadata generation

**api.py**
- Zenodo API client with sandbox support
- arXiv submission package preparation
- GitHub release creation and automation
- DOI minting and archival
- Metrics tracking and reporting

## Key Features

### Metadata Extraction
```python
from infrastructure.publishing import extract_publication_metadata

metadata = extract_publication_metadata([Path("manuscript.md")])
```

### Citation Generation
```python
from infrastructure.publishing import (
    generate_citation_bibtex,
    generate_citation_apa,
    generate_citation_mla
)

bibtex = generate_citation_bibtex(metadata)
apa = generate_citation_apa(metadata)
mla = generate_citation_mla(metadata)
```

### Publishing to Platforms
```python
from infrastructure.publishing import (
    publish_to_zenodo,
    prepare_arxiv_submission,
    create_github_release
)

# Publish to Zenodo
doi = publish_to_zenodo(metadata, files, access_token)

# Prepare arXiv submission
arxiv_package = prepare_arxiv_submission(Path("output/"), metadata)

# Create GitHub release
url = create_github_release(
    "v1.0", "Release 1.0", "Release notes", files, token, "owner/repo"
)
```

## Testing

Run publishing tests with:
```bash
pytest tests/infra_tests/test_publishing/
```

## Configuration

Environment variables:
- `ZENODO_TOKEN` - Zenodo API token (for `publish_to_zenodo`)
- `GITHUB_TOKEN` - GitHub API token (for `create_github_release`)

## Integration

Publishing module is used by:
- Publication automation workflows
- Repository management
- DOI and citation management
- Academic dissemination pipelines

## Troubleshooting

### Metadata Extraction Fails

**Issue**: `extract_publication_metadata()` returns empty or incomplete metadata.

**Solutions**:
- Verify markdown files contain required metadata fields
- Check YAML frontmatter format is correct
- Ensure author information is properly formatted
- Review config.yaml for metadata
- Check file encoding (UTF-8 required)

### DOI Validation Errors

**Issue**: DOI validation fails for valid-looking DOIs.

**Solutions**:
- Verify DOI format matches standard pattern
- Check DOI checksum calculation
- Ensure DOI prefix is valid
- Review DOI registration status
- Try with known-good DOI for comparison

### Citation Generation Issues

**Issue**: Generated citations have incorrect formatting.

**Solutions**:
- Verify metadata contains all required fields
- Check citation format specifications
- Review author name formatting
- Ensure publication dates are valid
- Test with different citation formats

### Zenodo Upload Fails

**Issue**: `publish_to_zenodo()` fails with API errors.

**Solutions**:
- Verify `ZENODO_TOKEN` is set and valid
- Check token has correct permissions
- Review file sizes (Zenodo has limits)
- Ensure sandbox flag matches token type
- Check API rate limits
- Review error messages for specific issues

### GitHub Release Creation Fails

**Issue**: `create_github_release()` fails with API errors.

**Solutions**:
- Verify `GITHUB_TOKEN` is set and valid
- Check token has `repo` scope permissions
- Verify repository name format (`owner/repo`)
- Review file sizes (GitHub has limits)
- Check API rate limits
- Ensure tag doesn't already exist

### arXiv Submission Preparation Issues

**Issue**: `prepare_arxiv_submission()` creates invalid package.

**Solutions**:
- Verify all required files are included
- Check file naming conventions
- Ensure LaTeX files compile correctly
- Review arXiv submission requirements
- Check for disallowed packages or commands

## Best Practices

### Metadata Management

- **Metadata**: Include all required fields in config.yaml
- **Version Control**: Keep metadata in version-controlled config file
- **Consistent Formatting**: Use consistent author name formatting
- **Validate Early**: Validate metadata before publishing

### DOI Management

- **Register Early**: Register DOI before final publication
- **Use Persistent URLs**: Always use DOI URLs, not direct links
- **Track Versions**: Associate DOI with specific versions
- **Document DOI**: Include DOI in all publication materials

### Citation Generation

- **Multiple Formats**: Generate citations in multiple formats
- **Validate Format**: Check citations against style guides
- **Include All Fields**: Ensure all required fields are present
- **Test Citations**: Verify citations work in bibliography systems

### Platform Publishing

- **Use Sandbox First**: Test with sandbox environments before production
- **Secure Tokens**: Never commit API tokens to version control
- **Handle Errors**: Implement retry logic for transient failures
- **Monitor Status**: Track publication status after upload

### Submission Preparation

- **Follow Guidelines**: Adhere to platform-specific requirements
- **Test Locally**: Test submission packages before uploading
- **Document Process**: Document submission steps for reproducibility
- **Version Control**: Track submission package versions

### Error Handling

- **Graceful Degradation**: Handle API failures gracefully
- **Retry Logic**: Implement retry for transient failures
- **Clear Messages**: Provide actionable error messages
- **Log Operations**: Log all publishing operations for debugging

## See Also

- [README.md](README.md) - Quick reference guide
- [`core/`](../core/) - Foundation utilities
- [`validation/`](../validation/) - Validation & quality assurance

