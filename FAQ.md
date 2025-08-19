# ❓ Frequently Asked Questions

## 🚀 **Getting Started**

### **Q: What is this template for?**
**A:** This is a comprehensive template for research projects that provides a standardized structure with test-driven development, automated PDF generation, and professional documentation workflows. It's perfect for academic papers, scientific documentation, technical reports, and any project requiring professional output.

### **Q: How do I use this template?**
**A:** Click the "Use this template" button on GitHub to create a new repository with this structure, then clone it and customize it for your project. The template includes everything you need to get started immediately.

### **Q: What programming languages does this support?**
**A:** The template is primarily designed for Python projects, but the documentation and PDF generation features work with any content. The core architecture focuses on Python with comprehensive testing and build automation.

## 🏗️ **Project Structure**

### **Q: Why is the project structured this way?**
**A:** The structure follows the "thin orchestrator pattern" which separates business logic (`src/`) from orchestration (`scripts/`). This ensures maintainable, testable code while keeping scripts lightweight and focused on their specific tasks.

### **Q: What's the difference between `src/` and `scripts/`?**
**A:** 
- **`src/`** contains all business logic, algorithms, and mathematical implementations with 100% test coverage
- **`scripts/`** are lightweight wrappers that import and use `src/` methods to generate figures, data, and outputs

### **Q: Do I need to keep the 100% test coverage requirement?**
**A:** While not strictly required, maintaining 100% test coverage ensures code quality and reliability. The build pipeline enforces this to maintain professional standards.

## 📚 **Documentation & PDF Generation**

### **Q: How does the PDF generation work?**
**A:** The template uses Pandoc to convert markdown files to LaTeX, then XeLaTeX to generate PDFs. The `render_pdf.sh` script orchestrates the entire process, including figure generation and cross-referencing.

### **Q: Can I customize the PDF output format?**
**A:** Yes! The LaTeX templates and Pandoc configurations can be customized. You can modify styles, add custom formatting, or even generate other formats like HTML or Word documents.

### **Q: How do I add cross-references between documents?**
**A:** The template includes a cross-referencing system that automatically generates links between markdown files. See `MARKDOWN_TEMPLATE_GUIDE.md` for detailed instructions.

### **Q: What if I don't need PDF generation?**
**A:** You can remove the PDF-related utilities and focus on the core project structure. The template is modular, so you can use only the parts you need.

## 🧪 **Testing & Development**

### **Q: Why is test coverage so important?**
**A:** Test coverage ensures that your core business logic works correctly and remains reliable as you make changes. It's especially important for research projects where accuracy is critical.

### **Q: How do I add new tests?**
**A:** Create test files in the `tests/` directory that follow the naming convention `test_*.py`. Use pytest fixtures and ensure your tests cover all code paths in your `src/` modules.

### **Q: Can I use different testing frameworks?**
**A:** While pytest is the default, you can adapt the template to use other testing frameworks. Just update the build scripts and CI configuration accordingly.

## 🔧 **Customization & Extension**

### **Q: How do I rename the project?**
**A:** Use the `rename_project.sh` script in `repo_utilities/` to automatically update all references to the project name throughout the codebase.

### **Q: Can I add new output formats?**
**A:** Absolutely! The template is designed to be extensible. You can add new output formats by creating new scripts and updating the build pipeline.

### **Q: How do I integrate with other tools?**
**A:** The template provides hooks and utilities that make it easy to integrate with CI/CD systems, documentation generators, and other development tools.

## 🚨 **Troubleshooting**

### **Q: The build pipeline fails - what should I check?**
**A:** 
1. Ensure all tests pass with 100% coverage
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
1. Run tests with verbose output: `pytest -v`
2. Use pytest's debugging features: `pytest --pdb`
3. Check coverage reports: `pytest --cov=src --cov-report=html`
4. Review the test output for specific error messages

## 🌟 **Advanced Usage**

### **Q: Can I use this for collaborative research?**
**A:** Yes! The template includes issue templates, pull request templates, and contribution guidelines that make collaboration easy and professional.

### **Q: How do I contribute improvements back to the template?**
**A:** Fork the repository, make your improvements, and submit a pull request. See `CONTRIBUTING.md` for detailed guidelines.

### **Q: Can I use this template commercially?**
**A:** Yes, the template is licensed under the Apache License 2.0, which allows commercial use, modification, and distribution.

### **Q: How do I stay updated with template improvements?**
**A:** Watch the repository for updates, check the changelog, and consider contributing improvements back to the community.

## 📞 **Getting Help**

### **Q: Where can I get more help?**
**A:** 
1. Check the comprehensive documentation in the markdown directory
2. Open an issue on GitHub for specific problems
3. Review the examples and workflow guides
4. Join the community discussions

For detailed documentation, see **[`README.md`](README.md)**, **[`ARCHITECTURE.md`](ARCHITECTURE.md)**, and **[`WORKFLOW.md`](WORKFLOW.md)**.

### **Q: Can I request new features?**
**A:** Yes! Use the feature request issue template to suggest improvements. We welcome all suggestions that would benefit the broader community.

---

**Still have questions? [Open an issue](https://github.com/docxology/template/issues) and we'll help you out! 🚀**

For more information, see **[`CONTRIBUTING.md`](CONTRIBUTING.md)** and **[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)**.
