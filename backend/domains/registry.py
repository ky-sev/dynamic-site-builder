import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DOMAINS_ROOT = Path(__file__).resolve().parent


# Represents domain metadata and navigation configuration discovered from a domain manifest.
class DomainManifest(BaseModel):
    key: str
    title: str
    description: str = ""
    icon: str = "folder"
    nav_order: int = 100
    route: str
    workflow_key: str
    default_fixture: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Discovers all domain manifests dynamically by scanning backend/domains/ for manifest.json files.
def discover_domain_manifests() -> List[DomainManifest]:
    manifests: List[DomainManifest] = []

    if not DOMAINS_ROOT.exists():
        return manifests

    for domain_dir in DOMAINS_ROOT.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith((".", "_")):
            continue

        manifest_file = domain_dir / "manifest.json"
        if manifest_file.exists():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                manifest = DomainManifest.model_validate(data)
                if manifest.is_active:
                    manifests.append(manifest)
            except Exception as e:
                logger.error(f"Error loading domain manifest at {manifest_file}: {e}")

    manifests.sort(key=lambda m: (m.nav_order, m.title))
    return manifests


# Looks up a domain by workflow_key or key and loads its default_fixture JSON if available.
def get_domain_default_fixture(workflow_key: str) -> Optional[Dict[str, Any]]:
    if not DOMAINS_ROOT.exists():
        return None

    for domain_dir in DOMAINS_ROOT.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith((".", "_")):
            continue

        manifest_file = domain_dir / "manifest.json"
        if manifest_file.exists():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                manifest = DomainManifest.model_validate(data)
                if (manifest.workflow_key == workflow_key or manifest.key == workflow_key) and manifest.default_fixture:
                    fixture_path = domain_dir / manifest.default_fixture
                    if fixture_path.exists():
                        return json.loads(fixture_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading fixture for workflow_key '{workflow_key}': {e}")

    return None
