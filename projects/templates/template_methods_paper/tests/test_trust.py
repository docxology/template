"""Tests for src.methods_dsl.trust — provenance tiers and hash-chained history."""

from __future__ import annotations

from src.methods_dsl.trust import ProvenanceTier, append_record, demo_chain_report, verify_chain


def test_append_record_to_empty_chain_links_to_genesis():
    chain = append_record((), "offset", "0.42", ProvenanceTier.DECLARED)
    assert len(chain) == 1
    assert chain[0].prev_hash == "0" * 64
    assert chain[0].tier is ProvenanceTier.DECLARED


def test_append_record_does_not_mutate_input_chain():
    chain = append_record((), "offset", "0.42", ProvenanceTier.DECLARED)
    extended = append_record(chain, "offset", "0.41", ProvenanceTier.CALIBRATED)
    assert len(chain) == 1  # original untouched
    assert len(extended) == 2
    assert extended[1].prev_hash == chain[0].record_hash


def test_verify_chain_empty_is_valid():
    assert verify_chain(()) is True


def test_verify_chain_valid_multi_record_chain():
    chain = ()
    chain = append_record(chain, "offset", "0.42", ProvenanceTier.DECLARED)
    chain = append_record(chain, "offset", "0.41", ProvenanceTier.CALIBRATED)
    chain = append_record(chain, "offset", "0.41", ProvenanceTier.VERIFIED)
    assert verify_chain(chain) is True


def test_verify_chain_detects_tampered_value():
    from dataclasses import replace

    chain = ()
    chain = append_record(chain, "offset", "0.42", ProvenanceTier.DECLARED)
    chain = append_record(chain, "offset", "0.41", ProvenanceTier.CALIBRATED)
    # Simulate downstream tampering: a record with an altered value but the
    # original (now-stale) record_hash, the way a corrupted store would look.
    tampered = replace(chain[0], value="9.99")
    tampered_chain = (tampered, chain[1])
    assert verify_chain(tampered_chain) is False


def test_verify_chain_detects_reordered_records():
    chain = ()
    chain = append_record(chain, "a", "1", ProvenanceTier.DECLARED)
    chain = append_record(chain, "b", "2", ProvenanceTier.DECLARED)
    reordered = (chain[1], chain[0])
    assert verify_chain(reordered) is False


def test_provenance_tier_values():
    assert {t.value for t in ProvenanceTier} == {"declared", "calibrated", "verified"}


def test_demo_chain_report_is_a_verified_three_record_chain():
    report = demo_chain_report()
    assert report == {"chain_length": 3, "verified": True}
