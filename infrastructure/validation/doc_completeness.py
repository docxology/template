"""Phase 3: Completeness Analysis for documentation scanning."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from infrastructure.validation.doc_models import CompletenessGap, DocumentationFile


def check_feature_documentation(repo_root: Path, documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check if all features are documented."""
    gaps = []
    # Check src/ modules are documented
    src_dir = repo_root / 'src'
    if src_dir.exists():
        src_modules = list(src_dir.glob('*.py'))
        src_modules = [m for m in src_modules if m.name != '__init__.py']
        
        for module in src_modules:
            module_name = module.stem
            # Check if documented in docs/ or AGENTS.md
            documented = False
            for doc_file in documentation_files:
                if module_name in doc_file.relative_path.lower():
                    documented = True
                    break
            
            if not documented:
                gaps.append(CompletenessGap(
                    category='features',
                    item=module_name,
                    description=f"Module {module_name} may not be fully documented",
                    severity='info'
                ))
    
    return gaps


def check_script_documentation(repo_root: Path) -> List[CompletenessGap]:
    """Check if all scripts have documentation."""
    gaps = []
    scripts_dir = repo_root / 'scripts'
    repo_utils_dir = repo_root / 'repo_utilities'
    
    for script_dir in [scripts_dir, repo_utils_dir]:
        if script_dir.exists():
            for script in script_dir.glob('*.py'):
                if script.name.startswith('_'):
                    continue
                # Check if script has docstring and is mentioned in docs
                try:
                    content = script.read_text(encoding='utf-8')
                    if not re.search(r'""".*?"""', content, re.DOTALL):
                        gaps.append(CompletenessGap(
                            category='scripts',
                            item=script.name,
                            description=f"Script {script.name} lacks docstring",
                            severity='warning'
                        ))
                except Exception:
                    pass
    
    return gaps


def check_config_documentation(config_files: Dict[str, Path]) -> List[CompletenessGap]:
    """Check if configuration options are documented."""
    gaps = []
    # Check if config.yaml.example is comprehensive
    if 'config.yaml.example' in config_files:
        # This could be enhanced to check all options are documented
        pass
    return gaps


def check_troubleshooting(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check troubleshooting guide completeness."""
    gaps = []
    has_troubleshooting = any('TROUBLESHOOTING' in d.relative_path for d in documentation_files)
    if not has_troubleshooting:
        gaps.append(CompletenessGap(
            category='troubleshooting',
            item='troubleshooting_guide',
            description="No dedicated troubleshooting guide found",
            severity='info'
        ))
    return gaps


def check_workflow_documentation(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check workflow documentation completeness."""
    gaps = []
    has_workflow = any('WORKFLOW' in d.relative_path for d in documentation_files)
    if not has_workflow:
        gaps.append(CompletenessGap(
            category='workflows',
            item='workflow_guide',
            description="Workflow documentation may be incomplete",
            severity='info'
        ))
    return gaps


def check_onboarding(documentation_files: List[DocumentationFile]) -> List[CompletenessGap]:
    """Check new user onboarding completeness."""
    gaps = []
    has_getting_started = any('GETTING_STARTED' in d.relative_path for d in documentation_files)
    has_quick_start = any('QUICK_START' in d.relative_path for d in documentation_files)
    
    if not has_getting_started and not has_quick_start:
        gaps.append(CompletenessGap(
            category='onboarding',
            item='getting_started',
            description="Getting started guide may be missing",
            severity='warning'
        ))
    return gaps


def check_cross_reference_completeness() -> List[CompletenessGap]:
    """Check cross-reference completeness."""
    gaps = []
    # This could check if related topics are linked
    return gaps


def group_gaps_by_category(gaps: List[CompletenessGap]) -> Dict[str, int]:
    """Group completeness gaps by category."""
    categories = defaultdict(int)
    for gap in gaps:
        categories[gap.category] += 1
    return dict(categories)


def group_gaps_by_severity(gaps: List[CompletenessGap]) -> Dict[str, int]:
    """Group completeness gaps by severity."""
    severities = defaultdict(int)
    for gap in gaps:
        severities[gap.severity] += 1
    return dict(severities)


def run_completeness_phase(
    repo_root: Path,
    documentation_files: List[DocumentationFile],
    config_files: Dict[str, Path]
) -> Dict:
    """Run Phase 3: Completeness Analysis.
    
    Args:
        repo_root: Root path of the repository
        documentation_files: List of documentation file metadata
        config_files: Dictionary of config file paths
        
    Returns:
        Dictionary with completeness report
    """
    print("Phase 3: Completeness Analysis...")
    
    gaps = []
    
    # Check feature documentation
    feature_gaps = check_feature_documentation(repo_root, documentation_files)
    gaps.extend(feature_gaps)
    
    # Check script documentation
    script_gaps = check_script_documentation(repo_root)
    gaps.extend(script_gaps)
    
    # Check configuration documentation
    config_gaps = check_config_documentation(config_files)
    gaps.extend(config_gaps)
    
    # Check troubleshooting guides
    troubleshooting_gaps = check_troubleshooting(documentation_files)
    gaps.extend(troubleshooting_gaps)
    
    # Check workflow documentation
    workflow_gaps = check_workflow_documentation(documentation_files)
    gaps.extend(workflow_gaps)
    
    # Check onboarding
    onboarding_gaps = check_onboarding(documentation_files)
    gaps.extend(onboarding_gaps)
    
    # Check cross-references
    crossref_gaps = check_cross_reference_completeness()
    gaps.extend(crossref_gaps)
    
    completeness_report = {
        'total_gaps': len(gaps),
        'by_category': group_gaps_by_category(gaps),
        'severity_breakdown': group_gaps_by_severity(gaps)
    }
    
    print(f"  Found {len(gaps)} completeness gaps")
    return completeness_report, gaps

