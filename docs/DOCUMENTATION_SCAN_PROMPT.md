# Repository-Wide Documentation Scan and Improvement Prompt

## Purpose

This prompt is designed for comprehensive, intelligent scanning and improvement of documentation across an entire repository. Use this prompt with AI assistants or as a guide for manual documentation reviews.

## The Prompt

```
Perform a comprehensive repository-wide documentation scan and intelligent improvement analysis. Follow this systematic approach:

## Phase 1: Discovery and Inventory

1. **Identify All Documentation Files**
   - Find all markdown files (.md) in the repository
   - Identify AGENTS.md and README.md files in each directory
   - List configuration files (pyproject.toml, config.yaml, etc.)
   - Catalog script files and their documentation

2. **Map Documentation Structure**
   - Create a hierarchy of documentation files
   - Identify root-level vs. directory-level documentation
   - Map cross-references between documents
   - Identify documentation categories (user guides, API docs, architecture, etc.)

## Phase 2: Accuracy Verification

For each documentation file, verify:

1. **Content Accuracy**
   - [ ] Commands and code examples are correct and runnable
   - [ ] File paths match actual repository structure
   - [ ] Script options match actual script implementations
   - [ ] Configuration options match actual config files
   - [ ] Version numbers and dates are current
   - [ ] Feature descriptions match actual code behavior

2. **Reference Accuracy**
   - [ ] All internal links resolve correctly
   - [ ] Relative paths are calculated correctly (../ for parent, ./ for same dir)
   - [ ] Anchor links (#section-name) match actual headings
   - [ ] External links are valid and accessible
   - [ ] File references point to existing files
   - [ ] No references to deleted or moved files

3. **Terminology Consistency**
   - [ ] Key terms used consistently across all docs
   - [ ] Architecture patterns described uniformly
   - [ ] Command syntax is consistent
   - [ ] File naming conventions are consistent

## Phase 3: Completeness Analysis

For each documentation area, check:

1. **Coverage Completeness**
   - [ ] All major features are documented
   - [ ] All scripts have usage documentation
   - [ ] All configuration options are explained
   - [ ] All error conditions have troubleshooting guidance
   - [ ] All workflows have step-by-step instructions

2. **Audience Completeness**
   - [ ] New user onboarding is clear
   - [ ] Developer documentation is comprehensive
   - [ ] Advanced usage is covered
   - [ ] Troubleshooting guides exist
   - [ ] Examples are provided for common tasks

3. **Cross-Reference Completeness**
   - [ ] Related topics are linked appropriately
   - [ ] Navigation paths are clear
   - [ ] See also sections are comprehensive
   - [ ] Index/table of contents is complete

## Phase 4: Quality Assessment

Evaluate documentation quality:

1. **Clarity and Readability**
   - [ ] Language is clear and concise
   - [ ] Technical jargon is explained
   - [ ] Examples illustrate concepts
   - [ ] Structure is logical and easy to follow
   - [ ] Headings are descriptive and hierarchical

2. **Actionability**
   - [ ] Instructions are step-by-step
   - [ ] Commands are copy-paste ready
   - [ ] Expected outputs are shown
   - [ ] Error handling is explained
   - [ ] Next steps are clear

3. **Maintainability**
   - [ ] Documentation is organized logically
   - [ ] Duplication is minimized
   - [ ] Single source of truth is established
   - [ ] Update procedures are clear
   - [ ] Version control is used appropriately

## Phase 5: Intelligent Improvements

Identify and propose improvements:

1. **Structural Improvements**
   - Consolidate duplicate information
   - Reorganize for better flow
   - Add missing navigation elements
   - Improve cross-referencing
   - Create missing index/glossary

2. **Content Improvements**
   - Add missing examples
   - Clarify ambiguous instructions
   - Expand incomplete sections
   - Update outdated information
   - Fix broken links and references

3. **User Experience Improvements**
   - Add quick start guides
   - Create troubleshooting sections
   - Add visual aids (diagrams, screenshots)
   - Improve code examples with context
   - Add "what's next" guidance

4. **Technical Improvements**
   - Standardize formatting
   - Improve code syntax highlighting
   - Add version information
   - Include compatibility notes
   - Document edge cases

## Phase 6: Verification and Validation

After improvements, verify:

1. **Automated Checks**
   - Run link checkers
   - Validate markdown syntax
   - Check for broken references
   - Verify code examples compile/run
   - Test all commands

2. **Manual Review**
   - Read through as a new user
   - Follow all workflows end-to-end
   - Verify all examples work
   - Check all cross-references
   - Validate consistency

3. **Cross-Reference Validation**
   - Follow all internal links
   - Verify relative paths
   - Check anchor links
   - Validate external links
   - Ensure no circular references

## Phase 7: Reporting

Generate comprehensive report:

1. **Summary Statistics**
   - Total files scanned
   - Issues found by category
   - Improvements made
   - Files updated
   - Links verified

2. **Issue Catalog**
   - Broken links with fixes
   - Outdated information updated
   - Missing documentation identified
   - Inconsistencies resolved
   - Quality improvements made

3. **Recommendations**
   - Areas needing more documentation
   - Structural improvements suggested
   - Process improvements for maintenance
   - Tools that could help
   - Future documentation needs

## Execution Guidelines

1. **Systematic Approach**: Work through each phase completely before moving to the next
2. **Prioritize Accuracy**: Fix errors before making improvements
3. **Maintain Consistency**: Apply standards uniformly across all docs
4. **Document Changes**: Keep track of what was changed and why
5. **Verify Everything**: Don't assume - verify all links, paths, and commands
6. **Think Like a User**: Consider different user personas and their needs
7. **Preserve Intent**: Don't change meaning when improving clarity

## Success Criteria

Documentation scan is successful when:
- ✅ All links resolve correctly
- ✅ All commands work as documented
- ✅ All file paths are accurate
- ✅ Terminology is consistent
- ✅ Examples are complete and runnable
- ✅ Navigation is intuitive
- ✅ Information is current and accurate
- ✅ No broken references exist
- ✅ Documentation is accessible to all user levels
- ✅ Maintenance procedures are clear

## Output Format

Provide:
1. Executive summary of findings
2. Detailed issue list with fixes
3. Improvement recommendations
4. Updated documentation files (if applicable)
5. Verification report showing all checks passed
```

## Usage Instructions

### For AI Assistants

Copy the prompt above and provide it with:
- Repository context
- Specific areas of concern (if any)
- Priority level (comprehensive vs. targeted scan)

### For Manual Reviews

Use this as a checklist:
1. Work through each phase systematically
2. Check off items as you verify them
3. Document findings in a report
4. Prioritize fixes by severity
5. Implement improvements incrementally

### For Automated Tools

Adapt this prompt to:
- Generate test cases for documentation validation
- Create linting rules
- Build documentation CI/CD checks
- Generate documentation coverage reports

## Customization

Adjust this prompt based on:
- **Repository Type**: Add domain-specific checks (e.g., API docs for libraries)
- **Documentation Style**: Adapt to your documentation standards
- **Tools Available**: Include checks for specific tools (pandoc, sphinx, etc.)
- **Team Needs**: Focus on areas most important to your team

## Maintenance

Review and update this prompt:
- After major documentation refactors
- When adding new documentation types
- When discovering new common issues
- When documentation standards evolve

---

**Note**: This prompt is designed to be comprehensive. For quick scans, focus on Phases 2-3 (Accuracy and Completeness). For deep improvements, complete all phases.

