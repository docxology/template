"""LaTeX compilation utilities."""
from __future__ import annotations

import subprocess
import os
from pathlib import Path
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import CompilationError

logger = get_logger(__name__)


def compile_latex(
    tex_file: Path, 
    output_dir: Path, 
    compiler: str = "xelatex",
    timeout: int = 300
) -> Path:
    """Compile LaTeX file to PDF.
    
    Args:
        tex_file: Path to .tex file
        output_dir: Directory for output
        compiler: Compiler command (xelatex, pdflatex)
        timeout: Timeout in seconds
        
    Returns:
        Path to generated PDF
    """
    if not tex_file.exists():
        raise CompilationError("LaTeX file not found", context={"file": str(tex_file)})
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # IMPORTANT: -shell-escape is required for XeTeX to properly determine PNG image
    # dimensions. Without this flag, XeTeX cannot read PNG bounding box information
    # and will produce "Division by 0" errors when including graphics.
    cmd = [
        compiler,
        "-interaction=nonstopmode",
        "-shell-escape",
        f"-output-directory={output_dir}",
        str(tex_file)
    ]

    logger.info(f"Compiling {tex_file} with {compiler}")

    try:
        import time
        start_time = time.time()

        # Run twice for references (first pass generates aux, second resolves references)
        max_passes = 2
        for i in range(max_passes):
            pass_start = time.time()
            logger.debug(f"Pass {i+1}/{max_passes}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tex_file.parent # Run in file directory for imports
            )

            pass_duration = time.time() - pass_start
            logger.debug(f"Pass {i+1} completed in {pass_duration:.2f}s")
            
            # Note: xelatex may return non-zero exit code even when PDF is generated (due to warnings)
            # So we check for PDF existence rather than just exit code
            pdf_file_temp = output_dir / f"{tex_file.stem}.pdf"
            if not pdf_file_temp.exists():
                # Only raise error if PDF was NOT generated
                log_file = output_dir / f"{tex_file.stem}.log"
                log_content = log_file.read_text() if log_file.exists() else "No log file"
                
                # Enhanced error analysis for better troubleshooting
                error_hints = []

                # Detect specific LaTeX error patterns
                if "*** (job aborted, no legal \\end found)" in log_content:
                    error_hints.append("Document structure error: missing \\end{document} or unmatched \\begin{}/\\end{} pairs")
                if "Undefined control sequence" in log_content:
                    error_hints.append("Undefined LaTeX command - check for typos or missing packages")
                if "File `" in log_content and "not found" in log_content:
                    error_hints.append("Missing file reference - check figure paths and bibliography files")
                if "LaTeX Error: File" in log_content and "not found" in log_content:
                    error_hints.append("Missing LaTeX package - install required packages")
                if "Missing \\begin{document}" in log_content:
                    error_hints.append("Missing \\begin{document} command - check document structure")
                if "Division by 0" in log_content and "graphics" in log_content.lower():
                    error_hints.append("Graphics error - ensure PNG files are valid and -shell-escape flag is used")

                # Extract the most recent error messages for context
                error_lines = []
                for line in reversed(log_content.split('\n')):
                    line = line.strip()
                    if line and ('Error' in line or '!' in line or '***' in line):
                        error_lines.append(line)
                        if len(error_lines) >= 5:  # Get last 5 error lines
                            break
                recent_errors = '\n'.join(reversed(error_lines)) if error_lines else "No specific errors found in log"

                enhanced_suggestions = [
                    f"Check full log file: {log_file}",
                    "Verify LaTeX syntax in source file",
                    "Ensure all required packages are available",
                    "Check for missing figure files or incorrect paths",
                    "Verify document has proper \\begin{document} and \\end{document} structure"
                ]

                if error_hints:
                    enhanced_suggestions.extend([f"Common issue: {hint}" for hint in error_hints])

                raise CompilationError(
                    f"LaTeX compilation failed (exit code: {result.returncode})",
                    context={
                        "exit_code": result.returncode,
                        "stderr": result.stderr[:300] if result.stderr else "",
                        "log_file": str(log_file),
                        "log_tail": log_content[-800:] if len(log_content) > 800 else log_content,
                        "recent_errors": recent_errors,
                        "detected_issues": error_hints
                    },
                    suggestions=enhanced_suggestions
                )
                
        pdf_file = output_dir / f"{tex_file.stem}.pdf"
        if not pdf_file.exists():
            raise CompilationError("PDF not generated", context={"expected": str(pdf_file)})

        total_duration = time.time() - start_time
        logger.info(f"LaTeX compilation completed in {total_duration:.2f}s")

        return pdf_file
        
    except subprocess.TimeoutExpired:
        raise CompilationError("Compilation timed out", context={"timeout": timeout})
    except OSError as e:
        raise CompilationError(f"Execution failed: {e}", context={"command": compiler})

