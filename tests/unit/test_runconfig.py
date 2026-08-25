from fisl.scenario.runconfig import (
    build_run_configuration,
    default_run_profile,
    new_run_id,
    reproducibility_fingerprint,
)


def test_run_ids_unique_and_sortable():
    a = new_run_id(timestamp_ms=1_000_000)
    b = new_run_id(timestamp_ms=2_000_000)
    assert len(a) == len(b) == 26
    assert a != b
    assert a < b  # ULIDs sort by creation time


def test_run_configuration_carries_identity_but_fingerprint_excludes_run_id():
    profile = default_run_profile("headless")
    common = dict(
        resolved_scenario_hash="sha256:abc",
        seed=7,
        baseline_sha256="sha256:def",
        factorio_version="2.0.77",
        fisl_versions={"fisl-core": "0.1.0"},
        mod_manifest={"base": "2.0.77", "fisl-core": "0.1.0"},
        run_profile=profile,
    )
    fp1 = reproducibility_fingerprint(**common)
    fp2 = reproducibility_fingerprint(**common)
    assert fp1 == fp2

    run_a = build_run_configuration(
        resolved_scenario_hash="sha256:abc",
        seed=7,
        baseline_path="baseline.zip",
        baseline_sha256="sha256:def",
        run_profile=profile,
    )
    run_b = build_run_configuration(
        resolved_scenario_hash="sha256:abc",
        seed=7,
        baseline_path="baseline.zip",
        baseline_sha256="sha256:def",
        run_profile=profile,
    )
    assert run_a["run_id"] != run_b["run_id"]


def test_seed_changes_fingerprint():
    profile = default_run_profile("headless")
    base = dict(
        resolved_scenario_hash="sha256:abc",
        baseline_sha256="sha256:def",
        factorio_version="2.0.77",
        fisl_versions={},
        mod_manifest={},
        run_profile=profile,
    )
    assert reproducibility_fingerprint(seed=1, **base) != reproducibility_fingerprint(seed=2, **base)


def test_interactive_profile_matches_adr_0018():
    profile = default_run_profile("interactive")
    assert profile["server_auto_pause"] is False
    assert profile["disconnect_policy"] == "abort"
    assert profile["required_learner_connection"] is True
