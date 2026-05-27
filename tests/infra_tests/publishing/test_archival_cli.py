"""Tests for infrastructure.publishing.archival_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.publishing.archival import ArchivalCredentials
from infrastructure.publishing import archival_cli


class TestBuildProviders:
    def test_builds_zenodo_provider(self) -> None:
        credentials = ArchivalCredentials(
            zenodo_token="zenodo-token",
            pinata_jwt=None,
            web3_storage_token=None,
        )
        providers = archival_cli._build_providers(["zenodo"], credentials)
        assert len(providers) == 1
        assert providers[0].name == "zenodo"

    def test_builds_multiple_providers(self) -> None:
        credentials = ArchivalCredentials(
            zenodo_token=None,
            pinata_jwt=None,
            web3_storage_token=None,
        )
        providers = archival_cli._build_providers(
            ["zenodo", "software_heritage"],
            credentials,
        )
        assert [provider.name for provider in providers] == ["zenodo", "software_heritage"]

    def test_builds_ipfs_providers(self) -> None:
        credentials = ArchivalCredentials(
            zenodo_token=None,
            pinata_jwt="pinata-jwt",
            web3_storage_token="web3-token",
        )
        providers = archival_cli._build_providers(
            ["ipfs_pinata", "ipfs_web3storage"],
            credentials,
        )
        assert [provider.name for provider in providers] == [
            "ipfs_pinata",
            "ipfs_web3storage",
        ]

    def test_unknown_provider_exits(self) -> None:
        credentials = ArchivalCredentials(
            zenodo_token=None,
            pinata_jwt=None,
            web3_storage_token=None,
        )
        with pytest.raises(SystemExit, match="Unknown provider"):
            archival_cli._build_providers(["not_a_provider"], credentials)


class TestArchivalCliMain:
    def test_dry_run_json_stdout(self, tmp_path: Path, capsys) -> None:
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "manifest.json").write_text('{"title": "Test bundle"}')

        exit_code = archival_cli.main(
            [
                "--bundle",
                str(bundle),
                "--providers",
                "zenodo",
            ]
        )

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert exit_code == 0
        assert payload["all_ok"] is True
        assert payload["receipts"][0]["provider"] == "zenodo"
        assert payload["receipts"][0]["status"] == "dry-run"

    def test_missing_bundle_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing-bundle"
        with pytest.raises(Exception, match="Bundle path does not exist"):
            archival_cli.main(
                [
                    "--bundle",
                    str(missing),
                    "--providers",
                    "zenodo",
                ]
            )
