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
        # Run twice for references
        for i in range(2):
            logger.debug(f"Pass {i+1}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tex_file.parent # Run in file directory for imports
            )
            
            # Note: xelatex may return non-zero exit code even when PDF is generated (due to warnings)
            # So we check for PDF existence rather than just exit code
            pdf_file_temp = output_dir / f"{tex_file.stem}.pdf"
            if not pdf_file_temp.exists():
                # Only raise error if PDF was NOT generated
                log_file = output_dir / f"{tex_file.stem}.log"
                log_content = log_file.read_text() if log_file.exists() else "No log file"
                
                raise CompilationError(
                    "LaTeX compilation failed",
                    context={
                        "exit_code": result.returncode,
                        "stderr": result.stderr[:200],
                        "log_tail": log_content[-500:] if len(log_content) > 500 else log_content
                    }
                )
                
        pdf_file = output_dir / f"{tex_file.stem}.pdf"
        if not pdf_file.exists():
            raise CompilationError("PDF not generated", context={"expected": str(pdf_file)})
            
        return pdf_file
        
    except subprocess.TimeoutExpired:
        raise CompilationError("Compilation timed out", context={"timeout": timeout})
    except OSError as e:
        raise CompilationError(f"Execution failed: {e}", context={"command": compiler})

