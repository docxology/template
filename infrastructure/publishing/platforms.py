"""Platform integration functions for academic publishing."""
from __future__ import annotations

import tarfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

import requests

from infrastructure.core.exceptions import PublishingError
from infrastructure.publishing.models import PublicationMetadata


def publish_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: List[Path],
    access_token: str,
    sandbox: bool = True
) -> str:
    """Publish to Zenodo.
    
    Args:
        metadata: Publication metadata
        file_paths: List of files to upload
        access_token: Zenodo API token
        sandbox: Use sandbox environment
        
    Returns:
        DOI of published deposition
    """
    from infrastructure.publishing.api import ZenodoClient, ZenodoConfig
    
    config = ZenodoConfig(access_token=access_token, sandbox=sandbox)
    client = ZenodoClient(config)
    
    # Create deposition
    dep_metadata = {
        "title": metadata.title,
        "upload_type": "publication",
        "publication_type": "article",
        "description": metadata.abstract,
        "creators": [{"name": author} for author in metadata.authors],
        "keywords": metadata.keywords,
        "license": metadata.license.lower()
    }
    
    dep_id = client.create_deposition(dep_metadata)
    
    # Upload files
    for path in file_paths:
        if path.exists():
            client.upload_file(dep_id, str(path))
            
    # Publish
    return client.publish(dep_id)


def prepare_arxiv_submission(
    output_dir: Path,
    metadata: PublicationMetadata
) -> Path:
    """Prepare submission package for arXiv.
    
    Args:
        output_dir: Directory containing build artifacts
        metadata: Publication metadata
        
    Returns:
        Path to generated .tar.gz file
    """
    submission_dir = output_dir / "arxiv_submission"
    if submission_dir.exists():
        shutil.rmtree(submission_dir)
    submission_dir.mkdir()
    
    # Copy LaTeX sources
    tex_dir = output_dir.parent / "manuscript"  # Assuming typical structure
    if tex_dir.exists():
        for item in tex_dir.glob("*"):
            if item.is_file() and item.suffix in ['.tex', '.bib', '.cls', '.bst']:
                shutil.copy2(item, submission_dir)
            elif item.is_dir() and item.name in ['figures']:
                shutil.copytree(item, submission_dir / item.name)
                
    # Create bbl file if it exists (arXiv needs it)
    bbl_file = output_dir / "pdf" / f"{metadata.title.replace(' ', '_')}.bbl"
    if bbl_file.exists():
        shutil.copy2(bbl_file, submission_dir)
        
    # Create tarball
    tar_path = output_dir / f"arxiv_submission_{datetime.now().strftime('%Y%m%d')}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(submission_dir, arcname="")
        
    return tar_path


def create_github_release(
    tag_name: str,
    release_name: str,
    description: str,
    assets: List[Path],
    token: str,
    repo: str
) -> str:
    """Create GitHub release.
    
    Args:
        tag_name: Git tag
        release_name: Release title
        description: Release notes
        assets: List of files to attach
        token: GitHub API token
        repo: Repository name (owner/repo)
        
    Returns:
        Release URL
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Create release
    url = f"https://api.github.com/repos/{repo}/releases"
    payload = {
        "tag_name": tag_name,
        "name": release_name,
        "body": description,
        "draft": False,
        "prerelease": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        release_data = response.json()
        upload_url = release_data["upload_url"].split("{")[0]
        html_url = release_data["html_url"]
        
        # Upload assets
        for asset in assets:
            if not asset.exists():
                continue
                
            name = asset.name
            with open(asset, "rb") as f:
                upload_headers = headers.copy()
                upload_headers["Content-Type"] = "application/octet-stream"
                requests.post(
                    f"{upload_url}?name={name}",
                    headers=upload_headers,
                    data=f
                )
                
        return html_url
        
    except requests.exceptions.RequestException as e:
        raise PublishingError(f"GitHub release failed: {e}")

