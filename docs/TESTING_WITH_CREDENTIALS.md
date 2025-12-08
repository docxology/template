# Testing with External Service Credentials

This guide explains how to configure and run tests that require external service credentials (Zenodo, GitHub, arXiv) and local tools (LaTeX).

## Overview

The test suite includes tests that make real API calls to external services. These tests are marked with special pytest markers and will automatically skip if credentials are not available.

## Quick Start

1. **Copy the example files:**
   ```bash
   cp .env.example .env
   cp test_credentials.yaml.example test_credentials.yaml
   ```

2. **Add your credentials** to `.env` (see sections below)

3. **Run all tests** (external service tests will be skipped if credentials not configured):
   ```bash
   pytest tests/
   ```

4. **Run only tests that don't require external services:**
   ```bash
   pytest tests/ -m "not requires_credentials"
   ```

## Credential Configuration

### Environment Variables (.env file)

Create a `.env` file in the repository root with your credentials:

```bash
# Zenodo Sandbox (recommended for testing)
ZENODO_SANDBOX_TOKEN=your_sandbox_token_here

# GitHub
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=username/test-repository

# arXiv (optional)
ARXIV_USERNAME=your_username
ARXIV_PASSWORD=your_password
```

### YAML Configuration (test_credentials.yaml)

Optionally, create `test_credentials.yaml` for additional configuration:

```yaml
zenodo:
  use_sandbox: true  # Always use sandbox for tests!
  
github:
  test_tag_prefix: "test-release-"
  
cleanup:
  auto_cleanup: true  # Automatically delete test artifacts
```

## Obtaining Credentials

### Zenodo Sandbox Token

1. Create account at [https://sandbox.zenodo.org/](https://sandbox.zenodo.org/)
2. Navigate to: Account Settings → Applications → Personal access tokens
3. Create new token with scopes: `deposit:write`, `deposit:actions`
4. Copy token to `.env` as `ZENODO_SANDBOX_TOKEN`

**Important:** Use the *sandbox* environment for testing, not production Zenodo!

### GitHub Personal Access Token

1. Go to [https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)
2. Create token with scopes:
   - `repo` (full repository access)
   - `write:packages` (for release assets)
   - `delete_repo` (optional, for test cleanup)
3. Set expiration and create token
4. Copy token to `.env` as `GITHUB_TOKEN`

**Repository Setup:**
- Create a test repository on GitHub (e.g., `username/test-automation`)
- Add repository name to `.env` as `GITHUB_REPO=username/test-automation`
- Tests will create and delete releases in this repository

### arXiv Credentials (Optional)

arXiv submission tests are optional and require SWORD API credentials:

1. Register for arXiv account
2. Contact arXiv to enable SWORD API access (not available by default)
3. Add credentials to `.env`

Most users can skip arXiv tests as they're not required for the core test suite.

## Test Markers

Tests are marked with the following markers:

| Marker | Description | Skip Condition |
|--------|-------------|----------------|
| `requires_zenodo` | Needs Zenodo API access | No `ZENODO_SANDBOX_TOKEN` |
| `requires_github` | Needs GitHub API access | No `GITHUB_TOKEN` or `GITHUB_REPO` |
| `requires_arxiv` | Needs arXiv API access | No `ARXIV_USERNAME` |
| `requires_latex` | Needs LaTeX installed | No `pdflatex` or `xelatex` |
| `requires_network` | Needs internet access | Offline environment |
| `requires_credentials` | Needs any external credentials | General credential marker |

## Running Tests Selectively

### Run all tests (skipping those without credentials):
```bash
pytest tests/
```

### Run only tests that don't need credentials:
```bash
pytest tests/ -m "not requires_credentials"
```

### Run only Zenodo tests:
```bash
pytest tests/ -m requires_zenodo
```

### Run only GitHub tests:
```bash
pytest tests/ -m requires_github
```

### Run only local tests (no network):
```bash
pytest tests/ -m "not requires_network"
```

### Run tests without LaTeX:
```bash
pytest tests/ -m "not requires_latex"
```

### Combine markers:
```bash
# Run tests that need neither credentials nor LaTeX
pytest tests/ -m "not requires_credentials and not requires_latex"

# Run all external service tests
pytest tests/ -m "requires_zenodo or requires_github"
```

## Test Cleanup

Tests automatically clean up after themselves:

- **Zenodo:** Test depositions are deleted after test completion
- **GitHub:** Test releases and tags are deleted after test completion
- **Files:** Temporary files are cleaned up using pytest's `tmp_path` fixtures

If cleanup fails (e.g., network error), you may need to manually delete test artifacts:

### Manual Zenodo Cleanup
```bash
# Visit Zenodo sandbox and delete test depositions
https://sandbox.zenodo.org/deposit
```

### Manual GitHub Cleanup
```bash
# Delete test releases via GitHub web UI or CLI
gh release delete test-release-12345678 --repo username/test-repo

# Delete test tags
git push --delete origin test-release-12345678
```

## Security Best Practices

1. **Never commit credentials:**
   - `.env` and `test_credentials.yaml` are in `.gitignore`
   - Always use `.env.example` for templates

2. **Use sandbox environments:**
   - Always use Zenodo *sandbox*, not production
   - Create dedicated test repositories on GitHub

3. **Rotate tokens regularly:**
   - GitHub tokens: Set expiration dates
   - Zenodo tokens: Regenerate periodically
   - Delete unused tokens

4. **Limit token scopes:**
   - Only grant minimum required permissions
   - Use separate tokens for different purposes

5. **Protect your `.env` file:**
   ```bash
   chmod 600 .env  # Owner read/write only
   ```

## Troubleshooting

### Tests are skipped

**Problem:** Tests marked with `requires_*` are being skipped

**Solution:** 
- Check `.env` file exists and has correct credentials
- Verify environment variables are loaded: `echo $ZENODO_SANDBOX_TOKEN`
- Run with `-v` to see skip reasons: `pytest tests/ -v`

### Zenodo API errors

**Problem:** Zenodo tests fail with authentication errors

**Solutions:**
- Verify token is for *sandbox*, not production
- Check token has `deposit:write` and `deposit:actions` scopes
- Ensure token hasn't expired
- Test token manually: `curl -H "Authorization: Bearer YOUR_TOKEN" https://sandbox.zenodo.org/api/deposit/depositions`

### GitHub API rate limiting

**Problem:** Tests fail with rate limit errors

**Solutions:**
- Authenticated requests have higher rate limits
- Wait for rate limit reset (check `X-RateLimit-Reset` header)
- Use a dedicated test account to avoid conflicts with personal usage

### LaTeX compilation failures

**Problem:** Rendering tests fail

**Solutions:**
- Install LaTeX: `sudo apt-get install texlive-latex-base texlive-xetex` (Ubuntu) or `brew install mactex` (macOS)
- Verify installation: `which pdflatex`
- Skip LaTeX tests: `pytest tests/ -m "not requires_latex"`

### Cleanup failures

**Problem:** Test artifacts not being deleted

**Solutions:**
- Check token permissions include deletion rights
- Manually delete via web UI
- Check cleanup logs for specific errors

## Environment Setup Examples

### Ubuntu/Debian
```bash
# Install LaTeX
sudo apt-get update
sudo apt-get install -y texlive-latex-base texlive-xetex pandoc

# Install Python dependencies
uv sync

# Configure credentials
cp .env.example .env
nano .env  # Add your credentials

# Run tests
pytest tests/
```

### macOS
```bash
# Install LaTeX
brew install --cask mactex
brew install pandoc

# Install Python dependencies
uv sync

# Configure credentials
cp .env.example .env
nano .env  # Add your credentials

# Run tests
pytest tests/
```

### Windows
```powershell
# Install MiKTeX or TeX Live
# Install pandoc from https://pandoc.org/

# Install Python dependencies
uv sync

# Configure credentials
copy .env.example .env
notepad .env  # Add your credentials

# Run tests
pytest tests/
```

## CI/CD Integration

For continuous integration, store credentials as secrets:

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup credentials
        run: |
          echo "ZENODO_SANDBOX_TOKEN=${{ secrets.ZENODO_SANDBOX_TOKEN }}" >> .env
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> .env
          echo "GITHUB_REPO=${{ secrets.GITHUB_REPO }}" >> .env
      
      - name: Install LaTeX
        run: |
          sudo apt-get update
          sudo apt-get install -y texlive-latex-base pandoc
      
      - name: Run tests
        run: pytest tests/
```

## Support

For issues or questions:

1. Check this documentation
2. Review test output with `-v` flag for detailed skip reasons
3. Verify credentials are correctly configured
4. Check external service status pages
5. File an issue with details of the problem

## See Also

- [tests/AGENTS.md](../tests/AGENTS.md) - Test suite documentation
- [tests/infrastructure/AGENTS.md](../tests/infrastructure/AGENTS.md) - Infrastructure test details
- [AGENTS.md](../AGENTS.md) - System documentation

