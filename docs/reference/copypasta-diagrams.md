# 📋 Copypasta — Architecture Diagrams & Comparisons

> **Ready-to-use diagrams and tables** for presentations and documentation

**See also:** [Copypasta — Descriptions & Code](copypasta.md) | [Copypasta — Outreach](copypasta-outreach.md)

---

## 🗺️ System Architecture Diagrams

### 🏗️ System Overview

```mermaid
graph TB
    subgraph "Research Project Template"
        SRC[📁 src/<br/>Core business logic<br/>Tested]
        TESTS[🧪 tests/<br/>Test suite<br/>coverage]
        SCRIPTS[📜 scripts/<br/>Thin orchestrators<br/>Use src/ methods]
        MANUSCRIPT[📚 manuscript/<br/>Research manuscript<br/>Cross-referenced]
        PIPELINE[📊 scripts/\n<br/>Build pipeline<br/>Stage scripts]
        OUTPUT[📤 output/<br/>Generated files<br/>PDFs, figures, data]
    end
    
    subgraph "Thin Orchestrator Pattern"
        SRC -->|"provides tested methods"| SCRIPTS
        SCRIPTS -->|"import & use"| SRC
        SCRIPTS -->|"generate"| OUTPUT
        TESTS -->|"validate"| SRC
    end
    
    subgraph "Build Pipeline"
        RENDER[🚀 execute_pipeline.py<br/>Pipeline Orchestrator]
        RENDER -->|"runs tests"| TESTS
        RENDER -->|"executes scripts"| SCRIPTS
        RENDER -->|"builds PDFs"| OUTPUT
    end
    
    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef pattern fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef pipeline fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SRC,TESTS,SCRIPTS,MANUSCRIPT,REPO_UTILS core
    class SRC,SCRIPTS pattern
    class RENDER pipeline
    class OUTPUT output
```

### ⚡ Development Workflow

```mermaid
flowchart TD
    START([🚀 Start Development]) --> TESTS[🧪 Write Tests First]
    TESTS --> IMPLEMENT[💻 Implement Functionality]
    IMPLEMENT --> VALIDATE[✅ Run Tests & Check Coverage]
    VALIDATE -->|Coverage below requirements| ADD_TESTS[➕ Add Missing Tests]
    ADD_TESTS --> VALIDATE
    VALIDATE -->|Coverage requirements met| INTEGRATION[🔗 Test Script Integration]
    INTEGRATION --> DOCS[📚 Update Documentation]
    DOCS --> PIPELINE[🚀 Run Pipeline]
    PIPELINE --> SUCCESS[🎉 Development]
    
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    
    class TESTS,IMPLEMENT,VALIDATE,ADD_TESTS,INTEGRATION,DOCS,PIPELINE process
    class START,SUCCESS success
```

### 📊 Output Generation Flow

```mermaid
graph LR
    subgraph "Input Sources"
        SRC[📁 src/ modules]
        MD[📚 Markdown files]
        PREAMBLE[📝 LaTeX preamble]
    end
    
    subgraph "Processing Pipeline"
        TESTS[🧪 Test validation]
        SCRIPTS[📜 Script execution]
        VALIDATION[✅ Markdown validation]
        GLOSSARY[📖 Glossary generation]
    end
    
    subgraph "Generated Outputs"
        FIGS[🖼️ Figures]
        DATA[📊 Data files]
        PDFS[📄 PDFs]
        TEX[🔤 LaTeX exports]
    end
    
    SRC --> TESTS
    SRC --> SCRIPTS
    MD --> VALIDATION
    SRC --> GLOSSARY
    SCRIPTS --> FIGS
    SCRIPTS --> DATA
    MD --> PDFS
    MD --> TEX
    
    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SRC,MD,PREAMBLE input
    class TESTS,SCRIPTS,VALIDATION,GLOSSARY process
    class FIGS,DATA,PDFS,TEX output
```

---

## 📊 Feature Comparison Table

| Feature | Traditional Approach | This Template | Benefit |
|---------|---------------------|---------------|---------|
| **Project Structure** | Manual organization | 🏗️ Standardized structure | Consistency across projects |
| **Testing** | Optional coverage | 🧪 Coverage requirements enforced | Reliable, bug-free code |
| **Documentation** | Manual updates | 📚 Auto-synchronized | Code-doc always in sync |
| **PDF Generation** | Manual LaTeX editing | 🚀 Automated from markdown | Save hours of formatting |
| **Figure Integration** | Manual file management | 🖼️ Automated generation | Seamless figure inclusion |
| **Cross-referencing** | Manual numbering | 🔗 Automatic system | Professional academic output |
| **Quality Assurance** | Manual review | ✅ Automated validation | Consistent high quality |
| **Collaboration** | Ad-hoc workflows | 🤝 Standardized processes | Team efficiency |

---

## 🔗 Quick Links Section

### 🌐 Essential URLs

🔗 **[GitHub Template](https://github.com/docxology/template)** — Click "Use this template"  
📚 **[Documentation](https://github.com/docxology/template#readme)** — Project overview  
🐛 **[Issues](https://github.com/docxology/template/issues)** — Report bugs & request features  
💬 **[Discussions](https://github.com/docxology/template/discussions)** — Join the community  

### 🚀 Key Features to Highlight

✅ **Test-driven development** with coverage  
✅ **Automated PDF generation** from markdown  
✅ **Professional LaTeX output** with cross-referencing  
✅ **Automated figure generation** from Python scripts  
✅ **Cross-referencing system** for equations & figures  
✅ **Standardized project structure** for consistency  
✅ **Thin orchestrator pattern** for maintainability  
✅ **Publication-ready outputs** for academic use  

### 📖 Documentation Navigation

🚀 **[How To Use Guide](../core/how-to-use.md)** — Usage guide from basic to advanced  
🏗️ **[Architecture Guide](../core/architecture.md)** — System design overview  
⚡ **[Workflow Guide](../core/workflow.md)** — Development process  
📝 **[Markdown Guide](../usage/markdown-template-guide.md)** — Writing & formatting  
🎯 **[Examples Showcase](../usage/examples-showcase.md)** — Real-world usage  
🔧 **[Thin Orchestrator Summary](../architecture/thin-orchestrator-summary.md)** — Pattern implementation  
🗺️ **[Development Roadmap](../development/roadmap.md)** — Future plans  
🤝 **[Contributing Guide](../development/contributing.md)** — How to contribute  
❓ **[FAQ](../reference/faq.md)** — Common questions

---

**Related:** [Copypasta — Descriptions & Code](copypasta.md) | [Copypasta — Outreach](copypasta-outreach.md)
