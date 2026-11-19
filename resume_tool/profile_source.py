"""Review-gated profile loading and conflict-aware Gist synchronization."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

from .models import Profile

MAX_PROFILE_BYTES = 1_000_000


def read_profile(path: Path) -> Profile:
    if path.stat().st_size > MAX_PROFILE_BYTES:
        raise ValueError("Profile exceeds 1 MB")
    profile = Profile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if not profile.reviewed:
        raise ValueError("Review the imported YAML and set reviewed: true before generating documents or matching")
    return profile


def sync_profile(path: Path, gist_url: str) -> None:
    """Fetch the latest profile.yaml, validating it before replacing an unchanged local copy."""
    parsed = urllib.parse.urlsplit(gist_url)
    match = re.fullmatch(r"/([A-Za-z0-9-]+)/([0-9a-fA-F]{20,40})/?", parsed.path)
    if parsed.scheme != "https" or parsed.netloc != "gist.github.com" or parsed.query or parsed.fragment or not match:
        raise ValueError("PROFILE_GIST_URL must be https://gist.github.com/OWNER/GIST_ID without a revision")
    owner, gist_id = (value.lower() for value in match.groups())
    raw_url = f"https://gist.githubusercontent.com/{owner}/{gist_id}/raw/profile.yaml"
    # Gist raw responses can remain cached after an edit, even with Cache-Control.
    request = urllib.request.Request(
        f"{raw_url}?fresh={time.time_ns()}",
        headers={"User-Agent": "resume-tool", "Cache-Control": "no-cache"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read(MAX_PROFILE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Could not download profile.yaml from the configured Gist (HTTP {exc.code})") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ValueError("Could not download the configured Gist; check connectivity and PROFILE_GIST_URL") from exc
    if len(content) > MAX_PROFILE_BYTES:
        raise ValueError("Gist profile exceeds 1 MB")

    state_path = path.with_name(f"{path.name}.gist-sync.json")
    source_hash = hashlib.sha256(raw_url.encode()).hexdigest()
    content_hash = hashlib.sha256(content).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".profile-sync-", dir=path.parent) as directory:
        downloaded = Path(directory) / "profile.yaml"
        downloaded.write_bytes(content)
        downloaded.chmod(0o600)
        read_profile(downloaded)

        local_hash = None
        if path.exists():
            if path.stat().st_size > MAX_PROFILE_BYTES:
                raise ValueError("Local profile exceeds 1 MB; refusing to overwrite it")
            local_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if local_hash is not None and local_hash != content_hash:
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
            if state != {"source": source_hash, "content": local_hash}:
                raise ValueError(
                    "Local profile differs from its last Gist sync; publish local changes to the Gist "
                    "before generating a resume, or choose a different PROFILE path. Nothing was overwritten."
                )
        state = Path(directory) / "state.json"
        state.write_text(json.dumps({"source": source_hash, "content": content_hash}) + "\n", encoding="utf-8")
        state.chmod(0o600)
        if local_hash != content_hash:
            os.replace(downloaded, path)
        os.replace(state, state_path)
