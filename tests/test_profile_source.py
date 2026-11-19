from io import BytesIO
from pathlib import Path
import sys
import urllib.error

import pdfplumber
import pytest
import yaml

from resume_tool import cli, profile_source

GIST_URL = "https://gist.github.com/example/" + "a" * 32


@pytest.fixture
def remote(monkeypatch):
    content = [Path("examples/profile.yaml").read_bytes()]
    monkeypatch.setattr(profile_source.urllib.request, "urlopen", lambda *args, **kwargs: BytesIO(content[0]))
    return content


def test_first_sync_downloads_a_complete_reviewed_profile(tmp_path, remote):
    target = tmp_path / "nested" / "profile.yaml"
    profile_source.sync_profile(target, GIST_URL)
    profile = profile_source.read_profile(target)
    assert profile.name == "Alex Example"
    assert profile.experience[0].bullets[1] == "Reduced API response time by 30 percent through query optimization."
    assert profile.experience[1].company == "Sample Services"
    assert target.read_bytes() == remote[0]
    assert target.stat().st_mode & 0o777 == 0o600


def test_remote_changes_update_only_an_unchanged_local_copy(tmp_path, remote):
    target = tmp_path / "profile.yaml"
    target.write_bytes(remote[0])
    profile_source.sync_profile(target, GIST_URL)
    remote[0] = remote[0].replace(b"summary: null", b"summary: Updated remote achievements.")
    profile_source.sync_profile(target, GIST_URL)
    assert profile_source.read_profile(target).summary == "Updated remote achievements."

    local_edit = target.read_bytes().replace(b"Updated remote achievements.", b"Unsynchronized local achievements.")
    target.write_bytes(local_edit)
    remote[0] = remote[0].replace(b"Updated remote achievements.", b"Another remote revision.")
    with pytest.raises(ValueError, match="Nothing was overwritten"):
        profile_source.sync_profile(target, GIST_URL)
    assert target.read_bytes() == local_edit

    remote[0] = local_edit
    profile_source.sync_profile(target, GIST_URL)
    remote[0] = remote[0].replace(b"Unsynchronized local achievements.", b"Published and updated achievements.")
    profile_source.sync_profile(target, GIST_URL)
    assert profile_source.read_profile(target).summary == "Published and updated achievements."


def test_sync_fetches_new_revisions_when_raw_responses_are_cached(tmp_path, remote, monkeypatch):
    cache = {}
    ticks = iter((1, 2))
    monkeypatch.setattr(profile_source.time, "time_ns", lambda: next(ticks))

    def cached_download(request, **kwargs):
        return BytesIO(cache.setdefault(request.full_url, remote[0]))

    monkeypatch.setattr(profile_source.urllib.request, "urlopen", cached_download)
    target = tmp_path / "profile.yaml"
    profile_source.sync_profile(target, GIST_URL)
    remote[0] = remote[0].replace(b"summary: null", b"summary: Newly published achievements.")
    profile_source.sync_profile(target, GIST_URL)
    assert profile_source.read_profile(target).summary == "Newly published achievements."


@pytest.mark.parametrize("existing_baseline", [False, True])
def test_initial_source_or_source_change_cannot_overwrite_local_data(tmp_path, remote, existing_baseline):
    target = tmp_path / "profile.yaml"
    target.write_bytes(remote[0])
    if existing_baseline:
        profile_source.sync_profile(target, GIST_URL.replace("a" * 32, "b" * 32))
    original = target.read_bytes()
    remote[0] = remote[0].replace(b"Alex Example", b"Another Candidate")
    with pytest.raises(ValueError, match="Nothing was overwritten"):
        profile_source.sync_profile(target, GIST_URL)
    assert target.read_bytes() == original


@pytest.mark.parametrize("invalid", [
    b"reviewed: false\nname: Unreviewed Candidate\n",
    b"reviewed: true\nname: Candidate\nunknown_field: unsafe\n",
    b"reviewed: [",
    b"\xff",
    b"x" * 1_000_001,
])
def test_invalid_remote_profile_preserves_local_data(tmp_path, remote, invalid):
    target = tmp_path / "profile.yaml"
    target.write_bytes(remote[0])
    profile_source.sync_profile(target, GIST_URL)
    original = target.read_bytes()
    remote[0] = invalid
    with pytest.raises((ValueError, yaml.YAMLError)):
        profile_source.sync_profile(target, GIST_URL)
    assert target.read_bytes() == original


@pytest.mark.parametrize("url", [
    GIST_URL.replace("https:", "http:"),
    GIST_URL.replace("gist.github.com", "gist.github.com.evil.test"),
    GIST_URL.replace("gist.github.com", "localhost"),
    GIST_URL.replace("gist.github.com", "user:secret@gist.github.com"),
    GIST_URL + "?token=secret",
    GIST_URL + "#fragment",
    GIST_URL + "/" + "c" * 40,
])
def test_invalid_gist_urls_are_rejected_before_network_access(tmp_path, monkeypatch, url):
    def unexpected_request(*args, **kwargs):
        pytest.fail("Invalid URLs must not reach the network")

    monkeypatch.setattr(profile_source.urllib.request, "urlopen", unexpected_request)
    with pytest.raises(ValueError, match="PROFILE_GIST_URL"):
        profile_source.sync_profile(tmp_path / "profile.yaml", url)


@pytest.mark.parametrize("error", [
    urllib.error.HTTPError(GIST_URL, 404, "Not Found", None, None),
    urllib.error.URLError("network unavailable"),
    TimeoutError("request timed out"),
])
def test_download_failures_preserve_local_data_and_hide_the_url(tmp_path, remote, monkeypatch, error):
    target = tmp_path / "profile.yaml"
    target.write_bytes(remote[0])
    original = target.read_bytes()

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(profile_source.urllib.request, "urlopen", fail)
    with pytest.raises(ValueError) as caught:
        profile_source.sync_profile(target, GIST_URL)
    assert GIST_URL not in str(caught.value)
    assert target.read_bytes() == original


def test_failed_atomic_replacement_keeps_the_previous_profile(tmp_path, remote, monkeypatch):
    target = tmp_path / "profile.yaml"
    target.write_bytes(remote[0])
    profile_source.sync_profile(target, GIST_URL)
    original = target.read_bytes()
    remote[0] = remote[0].replace(b"Alex Example", b"Updated Candidate")

    def fail(*args):
        raise OSError("replacement failed")

    monkeypatch.setattr(profile_source.os, "replace", fail)
    with pytest.raises(OSError, match="replacement failed"):
        profile_source.sync_profile(target, GIST_URL)
    assert target.read_bytes() == original


@pytest.mark.parametrize("use_gist", [False, True])
def test_resume_cli_uses_the_configured_source(tmp_path, remote, monkeypatch, use_gist):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JOB_DESCRIPTION", raising=False)
    monkeypatch.setattr(sys, "argv", ["resume-tool", "resume"])
    if use_gist:
        monkeypatch.setenv("PROFILE_GIST_URL", GIST_URL)
    else:
        monkeypatch.delenv("PROFILE_GIST_URL", raising=False)
        Path("profile.yaml").write_bytes(remote[0])

        def unexpected_request(*args, **kwargs):
            pytest.fail("Local-only resume generation must not use the network")

        monkeypatch.setattr(profile_source.urllib.request, "urlopen", unexpected_request)
    assert cli.main() == 0
    pdf, = Path("output").glob("*/resume.pdf")
    with pdfplumber.open(pdf) as document:
        assert len(document.pages) == 1
        assert "Alex Example" in (document.pages[0].extract_text() or "")
