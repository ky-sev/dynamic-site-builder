import json
from pathlib import Path
from domains.registry import (
    DOMAINS_ROOT,
    DomainManifest,
    discover_domain_manifests,
    get_domain_default_fixture,
)


def test_discover_domain_manifests():
    manifests = discover_domain_manifests()
    assert len(manifests) >= 2

    # Check ordering
    nav_orders = [m.nav_order for m in manifests]
    assert nav_orders == sorted(nav_orders)

    keys = [m.key for m in manifests]
    assert "intake" in keys
    assert "opportunities" in keys


def test_all_domains_have_valid_manifests():
    excluded = {"workflow_engine", "__pycache__"}
    domain_dirs = [
        d for d in DOMAINS_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in excluded
    ]

    routes_seen = set()
    keys_seen = set()

    for d in domain_dirs:
        manifest_file = d / "manifest.json"
        assert manifest_file.exists(), f"Domain folder '{d.name}' is missing a manifest.json!"

        raw = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest = DomainManifest.model_validate(raw)

        assert manifest.key == d.name, f"Domain folder '{d.name}' does not match manifest key '{manifest.key}'"
        assert manifest.title.strip(), f"Domain '{d.name}' has empty title"
        assert manifest.route.startswith("/"), f"Domain '{d.name}' route must start with '/'"
        assert manifest.route not in routes_seen, f"Duplicate route '{manifest.route}' found in '{d.name}'"
        assert manifest.key not in keys_seen, f"Duplicate key '{manifest.key}' found in '{d.name}'"

        routes_seen.add(manifest.route)
        keys_seen.add(manifest.key)


def test_opportunities_and_intake_default_fixtures():
    # Test opportunities fixture lookup
    opp_fixture = get_domain_default_fixture("deal_opportunities")
    assert opp_fixture is not None
    assert opp_fixture.get("title") == "Opportunities"
    assert any(f["key"] == "fundingReceived" for f in opp_fixture["fields"])

    # Test intake fixture lookup
    intake_fixture = get_domain_default_fixture("deal_intake")
    assert intake_fixture is not None
    assert intake_fixture.get("title") == "Deal intake"
    assert any(f["key"] == "customerName" for f in intake_fixture["fields"])
