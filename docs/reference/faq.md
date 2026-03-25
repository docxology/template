# ❓ Frequently Asked Questions

> **Common questions** and answers about the Research Project Template

**Quick Reference:** [Getting Started](../guides/getting-started.md) | [Troubleshooting](../operational/troubleshooting/) | [How To Use](../core/how-to-use.md)

## 🚀 **Getting Started**

### **Q: What is this template for?**

**A:** This is a template for research projects that provides a standardized structure with test-driven development, automated PDF generation, and professional documentation workflows. It's for academic papers, scientific documentation, technical reports, and any project requiring professional output.

### **Q: How do I use this template?**

**A:** Click the "Use this template" button on GitHub to create a new repository with this structure, then clone it and customize it for your project. The template includes everything you need to get started immediately.

### **Q: What programming languages does this support?**

**A:** The template is primarily designed for Python projects, but the documentation and PDF generation features work with any content. The core architecture focuses on Python with testing and build automation.

## 🏗️ **Project Structure**

### **Q: Why is the project structured this way?**

**A:** The structure follows the "thin orchestrator pattern" which separates business logic (`src/`) from orchestration (`scripts/`). This ensures maintainable, testable code while keeping scripts lightweight and focused on their specific tasks.

### **Q: What's the difference between `src/` and `scripts/`?**

**A:**
- **`projects/{name}/src/`** (Layer 2) contains business logic, algorithms, and mathematical implementations with robust test coverage.
- **`projects/{name}/scripts/`** are thin orchestrators that import use Layer 2 methods to generate specific figures, data, and outputs.
- **`scripts/`** (Layer 1 Root) are generic pipeline entry points that discover and execute the project-specific `scripts/`.

### **Q: What are the test coverage requirements?**

**A:** Coverage requirements are: 90% minimum for project code (currently achieving 100% - coverage!) and 60% minimum for infrastructure (currently achieving 83.33% - exceeds stretch goal!). The build pipeline enforces these to maintain professional standards.

## 📚 **Documentation & PDF Generation**

### **Q: How does the PDF generation work?**

**A:** The template uses Pandoc to convert markdown files to LaTeX, then XeLaTeX to generate PDFs. The `./run.sh` entry point (or `scripts/execute_pipeline.py`) runs the full pipeline sequence: tests, analysis scripts, PDF rendering, validation, and copy-out, with optional LLM stages when not using `--core-only`. Stage layout is documented in [RUN_GUIDE.md](../RUN_GUIDE.md).

### **Q: Can I customize the PDF output format?**

**A:** Yes! The LaTeX templates and Pandoc configurations can be customized. You can modify styles, add custom formatting, or even generate other formats like HTML or Word documents.

### **Q: How do I add cross-references between documents?**

**A:** The template includes a cross-referencing system that automatically generates links between markdown files. See `markdown-template-guide.md` for detailed instructions.

### **Q: What if I don't need PDF generation?**

**A:** You can remove the PDF-related utilities and focus on the core project structure. The template is modular, so you can use only the parts you need.

## 🧪 **Testing & Development**

### **Q: Why is test coverage so important?**

**A:** Test coverage ensures that your core business logic works correctly and remains reliable as you make changes. It's especially important for research projects where accuracy is critical.

### **Q: How do I add tests?**

**A:** Create test files in the `projects/{name}/tests/` directory that follow the naming convention `test_*.py`. Use pytest fixtures and ensure your tests cover all code paths in your `projects/{name}/src/` modules.

### **Q: Can I use different testing frameworks?**

**A:** While pytest is the default, you can adapt the template to use other testing frameworks. Just update the build scripts and CI configuration accordingly.

## 🔧 **Customization & Extension**

### **Q: How do I rename the project?**

**A:** Customize your project by editing `projects/{name}/manuscript/config.yaml` or setting environment variables (`AUTHOR_NAME`, `PROJECT_TITLE`, etc.). See [Configuration Guide](../operational/config/configuration.md) for details.

### **Q: Can I add new output formats?**

**A:** Absolutely! The template is designed to be extensible. You can add new output formats by creating new scripts and updating the build pipeline.

### **Q: How do I integrate with other tools?**

**A:** The template provides hooks and utilities that make it easy to integrate with CI/CD systems, documentation generators, and other development tools.

## 🚨 **Troubleshooting**

### **Q: The build pipeline fails - what should I check?**

**A:**

1. Ensure all tests pass with required coverage (90% project, 60% infra)
2. Check that all required dependencies are installed
3. Verify that your markdown files are properly formatted
4. Check the build logs for specific error messages

### **Q: My PDFs aren't generating correctly**

**A:**

1. Verify Pandoc and LaTeX are properly installed
2. Check that your markdown syntax is correct
3. Ensure all referenced figures and files exist
4. Review the LaTeX templates for any syntax issues

### **Q: How do I debug test failures?**

**A:**

1. Run tests with verbose output: `pytest projects/{name}/tests/ -v`
2. Use pytest's debugging features: `pytest --pdb`
3. Check coverage reports: `pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-report=html`
4. Review the test output for specific error messages

## 🌟 **Advanced Usage**

### **Q: Can I use this for collaborative research?**

**A:** Yes! The template includes issue templates, pull request templates, and contribution guidelines that make collaboration easy and professional.

### **Q: How do I contribute improvements back to the template?**

**A:** Fork the repository, make your improvements, and submit a pull request. See `contributing.md` for detailed guidelines.

### **Q: Can I use this template commercially?**

**A:** Yes, the template is licensed under the Apache License 2.0, which allows commercial use, modification, and distribution.

### **Q: How do I stay updated with template improvements?**

**A:** Watch the repository for updates, check the repository releases and commit history, and consider contributing improvements back to the community.

## 🧪 **Advanced Modules**

### **Q: What are the advanced modules?**

**A:** The template includes 12 infrastructure modules: core (logging, config, exceptions), documentation (figure management, glossary), validation (output verification, integrity), publishing (academic workflows), scientific (scientific computing), llm (local LLM assistance, literature search), rendering (multi-format output), reporting (pipeline reporting and error aggregation), project (project discovery and orchestration), steganography (watermarking, provenance), config (configuration schemas and templates), and docker (containerization). See [Modules Guide](../modules/modules-guide.md) for documentation.

### **Q: How do I use the advanced modules?**

**A:** See the [Modules Guide](../modules/modules-guide.md) for usage examples and integration patterns. Each module includes API documentation and best practices.

### **Q: Where can I find API documentation?**

**A:** API reference for all modules is available in [API Reference](../reference/api-reference.md), including function signatures, parameters, return values, and examples.

## ⚙️ **CI/CD & Automation**

### **Q: How do I set up CI/CD?**

**A:** See [`.github/README.md`](../../.github/README.md) for GitHub Actions setup, automated testing, and repository workflows.

### **Q: Can I automate PDF generation in CI?**

**A:** Yes. Start with [`.github/workflows/README.md`](../../.github/workflows/README.md), then adapt workflows to run `uv sync` and the pipeline entry point you need (see [RUN_GUIDE.md](../RUN_GUIDE.md)).

## 📦 **Dependency Management**

### **Q: How do I manage dependencies with uv?**

**A:** See the root [README.md](../../README.md) for `uv` install/sync commands, and use `uv run` to execute scripts consistently.

### **Q: What if I have dependency conflicts?**

**A:** Start with `uv lock --upgrade` (if used in your workflow) and re-run `uv sync`. If conflicts persist, simplify optional groups and ensure project dependencies are represented in the root environment when running under the root venv (see [docs/AGENTS.md](../AGENTS.md)).

## ⚡ **Performance**

### **Q: How can I optimize build times?**

**A:** See the [Performance Optimization Guide](../operational/config/performance-optimization.md) for strategies to reduce build times, including parallel execution, caching, and optimization techniques.

### **Q: What's the current build performance?**

**A:** See [Performance Optimization Guide](../operational/config/performance-optimization.md) for measurement and tuning, and [RUN_GUIDE.md](../RUN_GUIDE.md) for pipeline execution details.

## 📞 **Getting Help**

### **Q: Where can I get more help?**

**A:**

1. Check the documentation in the docs/ directory
2. Open an issue on GitHub for specific problems
3. Review the examples and workflow guides
4. Join the community discussions

For detailed documentation, see **[`README.md`](README.md)**, **[`../core/architecture.md`](../core/architecture.md)**, and **[`../core/workflow.md`](../core/workflow.md)**.

### **Q: Can I request features?**

**A:** Yes! Use the feature request issue template to suggest improvements. We welcome all suggestions that would benefit the broader community.

---

**Still have questions? [Open an issue](https://github.com/docxology/template/issues) and we'll help you out! 🚀**

For more information, see **[`contributing.md`](../development/contributing.md)** and **[`code-of-conduct.md`](../development/code-of-conduct.md)**.
