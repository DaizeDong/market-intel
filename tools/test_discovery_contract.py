"""Generated synthetic discovery coverage; no network or live inventory is used."""
import datetime as dt
from types import SimpleNamespace

import pytest

from test_private_writers import companion, load_writer

SINCE = dt.date(2031, 1, 1)
ATOM = '<feed xmlns="http://www.w3.org/2005/Atom">{}</feed>'
VIDEO = ('<entry><title>Synthetic tool update</title>'
         '<link href="https://example.com/synthetic-video"/>'
         '<published>2031-01-02T00:00:00Z</published>'
         '<description>Synthetic evidence.</description></entry>')


def response(payload=None, *, text="", status=200):
    def decode():
        if isinstance(payload, Exception):
            raise payload
        return payload
    return SimpleNamespace(status_code=status, text=text, json=decode)


@pytest.fixture
def discovery(monkeypatch):
    module = load_writer("discover")
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected HTTP request")
    monkeypatch.setattr(module.requests, "get", forbidden)
    monkeypatch.setattr(module, "_today", lambda: "2031-01-03")
    return module


@pytest.mark.parametrize("configuration", ["shipped", "empty", "invalid"])
def test_e6_unconfigured_fails_without_observation_or_write(
        configuration, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    if configuration == "empty":
        monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [])
    elif configuration == "invalid":
        monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                            [("Synthetic A", ""), ("Synthetic B", None)])
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e6", "--out", str(target)]) == 1
    captured = capsys.readouterr()
    assert "E6: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert "configured=0 attempted=0 completed=0" in captured.err
    assert "set verified UCIDs" in captured.err
    assert not target.parent.exists()


@pytest.mark.parametrize("failure", ["http", "request", "xml", "root"])
def test_e6_all_failed_feeds_are_not_empty_success(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [("Synthetic", "UCsynthetic")])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        return response(text={"xml": "<feed", "root": "<html/>"}.get(failure, ""),
                        status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    with pytest.raises(RuntimeError, match="no usable Atom feeds"):
        discovery.channel_e6_youtube(SINCE)
    assert len(calls) == 1
    assert "configured=1 attempted=1 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [ATOM.format(""), ATOM.format(
    VIDEO.replace("2031-01-02", "2030-01-02"))])
def test_e6_valid_empty_observation_allows_success_without_write(
        payload, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [("Synthetic", "UCsynthetic")])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k: response(text=payload))
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e6", "--since", str(SINCE), "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E6: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert not target.parent.exists()


@pytest.mark.parametrize("failure", ["http", "request", "xml", "root"])
def test_e6_partial_failure_keeps_valid_feed_rows(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                        [("Synthetic failed", "UCfailed"), ("Synthetic ready", "UCready")])
    def get(url, **kwargs):
        if url.endswith("UCready"):
            return response(text=ATOM.format(VIDEO))
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        return response(text={"xml": "<feed", "root": "<html/>"}.get(failure, ""),
                        status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    rows = discovery.channel_e6_youtube(SINCE)
    assert len(rows) == 1 and rows[0]["name"] == "Synthetic ready: Synthetic tool update"
    assert rows[0]["url"] == "https://example.com/synthetic-video"
    assert "configured=2 attempted=2 completed=1" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["http", "request", "json", "shape", "count", "boolean", "negative"])
def test_e4_no_valid_pairs_fails(discovery, monkeypatch, capsys, failure):
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if failure == "request":
            raise discovery.requests.RequestException("synthetic failure")
        payload = {
            "json": ValueError("synthetic malformed JSON"), "shape": {},
            "count": {"downloads": [{}]}, "boolean": {"downloads": [{"downloads": True}]},
            "negative": {"downloads": [{"downloads": -1}]},
        }.get(failure, {"downloads": []})
        return response(payload, status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    with pytest.raises(RuntimeError, match="no usable npm response pairs"):
        discovery.channel_e4_npm(SINCE)
    assert len(calls) == (1 if failure == "request" else 2)
    assert "configured=1 attempted=1 completed=0" in capsys.readouterr().err


def test_e4_unconfigured_is_not_a_completed_observation(discovery, monkeypatch, capsys):
    monkeypatch.setattr(discovery, "NPM_PACKAGES", [])
    with pytest.raises(RuntimeError, match="no usable npm response pairs"):
        discovery.channel_e4_npm(SINCE)
    assert "configured=0 attempted=0 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [{"downloads": []}, {"downloads": [{"downloads": 1}]}])
def test_e4_valid_empty_or_below_threshold_allows_success(
        payload, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k: response(payload))
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e4", "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E4: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert not target.parent.exists()


def test_e4_partial_results_and_failure_logs_keep_package_order(discovery, monkeypatch, capsys):
    packages = ["synthetic-fail-a", "synthetic-ready-a", "synthetic-fail-b", "synthetic-ready-b"]
    monkeypatch.setattr(discovery, "NPM_PACKAGES", packages)
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        package = url.rsplit("/", 1)[1]
        return response({"downloads": [{"downloads": 1000}]},
                        status=503 if "fail" in package else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    rows = discovery.channel_e4_npm(SINCE)
    assert [row["name"] for row in rows] == ["synthetic-ready-a", "synthetic-ready-b"]
    assert all(row["surface"] == "E4" for row in rows)
    assert len(calls) == 8
    errors = capsys.readouterr().err
    assert errors.index("synthetic-fail-a") < errors.index("synthetic-fail-b")
    assert "configured=4 attempted=4 completed=2" in errors


@pytest.mark.parametrize("failed_period", ["last-week", "last-month"])
@pytest.mark.parametrize("failure", ["http", "request", "shape"])
@pytest.mark.parametrize("mixed", [False, True])
def test_e4_one_failed_period_never_completes_a_package(
        failed_period, failure, mixed, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    packages = ["synthetic-half"] + (["synthetic-complete"] if mixed else [])
    monkeypatch.setattr(discovery, "NPM_PACKAGES", packages)
    def get(url, **kwargs):
        period, package = url.rsplit("/", 2)[-2:]
        if package == "synthetic-half" and period == failed_period:
            if failure == "request":
                raise discovery.requests.RequestException("Synthetic failed period")
            return response({} if failure == "shape" else {"downloads": []},
                            status=503 if failure == "http" else 200)
        return response({"downloads": [{"downloads": 1000}]})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--channel", "e4", "--out", str(target)]) == (0 if mixed else 1)
    output = capsys.readouterr()
    assert f"configured={len(packages)} attempted={len(packages)} completed={int(mixed)}" in output.err
    assert "synthetic-half: failed" in output.err
    if mixed:
        contents = target.read_text(encoding="utf-8")
        assert "synthetic-complete" in contents and "synthetic-half" not in contents
        assert "E4: 1 candidates" in output.out
    else:
        assert "E4: FAIL" in output.out and not target.parent.exists()


@pytest.mark.parametrize("healthy_empty", [False, True])
def test_default_sweep_requires_a_completed_channel(
        healthy_empty, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if "/downloads/range/" in url:
            return response(status=503)
        if healthy_empty and "huggingface.co/api/spaces" in url:
            return SimpleNamespace(json=lambda: [], raise_for_status=lambda: None)
        raise discovery.requests.RequestException("synthetic unavailable source")
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/discovery.md"
    assert discovery.main(["--out", str(target)]) == (0 if healthy_empty else 1)
    captured = capsys.readouterr()
    assert f"failures: {5 if healthy_empty else 6}/6" in captured.out
    assert "E4: FAIL" in captured.out and "E6: FAIL" in captured.out
    assert not any("youtube.com" in url for url in calls)
    assert not target.parent.exists()


def test_main_persists_partial_discovery_from_real_channel(
        discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS",
                        [("Synthetic failed", "UCfailed"), ("Synthetic ready", "UCready")])
    monkeypatch.setattr(discovery.requests, "get",
                        lambda url, **k: response(text=ATOM.format(VIDEO),
                                                 status=503 if url.endswith("UCfailed") else 200))
    target = repository / "data/deliverables/reports/discovery.md"
    assert discovery.main(["--channel", "e6", "--since", str(SINCE), "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert "https://example.com/synthetic-video" in content
    assert "Synthetic failed:" not in content
    assert "E6: 1 candidates" in capsys.readouterr().out


def observation_response(payload=None, *, text="", status=200):
    reply = response(payload, text=text, status=status)
    def raise_for_status():
        if status >= 400:
            raise RuntimeError("synthetic HTTP failure")
    reply.raise_for_status = raise_for_status
    return reply


@pytest.mark.parametrize("channel,payload,text", [
    ("e1", None, "<html/>"),
    ("e1", None, "<rss/>"),
    ("e1", None, "<rss><wrong/></rss>"),
    ("e1", None, "<rss><channel/><channel/></rss>"),
    ("e1", None, "<wrapper><rss><channel/></rss></wrapper>"),
    ("e1", None, '<feed xmlns="https://example.com/not-atom"/>'),
    ("e1", None, "<feed"),
    ("e2", None, ""),
    ("e2", {}, ""),
    ("e2", [], ""),
    ("e2", {"items": None}, ""),
    ("e2", {"items": {}}, ""),
    ("e2", {"items": "synthetic"}, ""),
    ("e2", {"items": [None]}, ""),
    ("e2", {"items": ["synthetic"]}, ""),
    ("e3", None, ""),
    ("e3", {}, ""),
    ("e3", {"error": "synthetic"}, ""),
    ("e3", "", ""),
    ("e3", 0, ""),
    ("e3", False, ""),
    ("e3", [None], ""),
    ("e3", ["synthetic"], ""),
    ("e5", None, ""),
    ("e5", {}, ""),
    ("e5", [], ""),
    ("e5", {"hits": None}, ""),
    ("e5", {"hits": {}}, ""),
    ("e5", {"hits": "synthetic"}, ""),
    ("e5", {"hits": [None]}, ""),
    ("e5", {"hits": ["synthetic"]}, ""),
])
@pytest.mark.parametrize("through_main", [False, True])
def test_malformed_response_never_completes_an_observation(
        channel, payload, text, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response(payload, text=text)
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/malformed-observation.md"
    if through_main:
        assert discovery.main(["--channel", channel, "--since", str(SINCE),
                               "--out", str(target)]) == 1
        summary = capsys.readouterr()
        assert channel.upper() + ": FAIL" in summary.out
        assert "failures: 1/1" in summary.out
        assert not target.parent.exists()
    else:
        with pytest.raises((RuntimeError, ValueError, discovery.ET.ParseError)):
            discovery.CHANNELS[channel](SINCE)
    assert len(calls) == 1


@pytest.mark.parametrize("channel,payload,text", [
    ("e1", None, "<rss><channel/></rss>"),
    ("e1", None, ATOM.format("")),
    ("e1", None, "<feed/>"),
    ("e2", {"items": []}, ""),
    ("e3", [], ""),
    ("e5", {"hits": []}, ""),
])
def test_valid_empty_envelope_is_a_completed_observation(
        channel, payload, text, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    monkeypatch.setattr(discovery.requests, "get",
                        lambda *a, **k: observation_response(payload, text=text))
    target = repository / "data/deliverables/uncreated/valid-empty.md"
    assert discovery.main(["--channel", channel, "--since", str(SINCE),
                           "--out", str(target)]) == 0
    summary = capsys.readouterr()
    assert channel.upper() + ": 0 candidates" in summary.out
    assert "failures: 0/1" in summary.out
    assert not target.parent.exists()


@pytest.mark.parametrize("topics", [[], ["", None, "  "], [None]])
@pytest.mark.parametrize("through_main", [False, True])
def test_e2_unconfigured_fails_without_http_or_output(
        topics, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics)
    # The discovery fixture already makes any HTTP attempt fail this test.
    target = repository / "data/deliverables/uncreated/unconfigured-topics.md"
    if through_main:
        assert discovery.main(["--channel", "e2", "--out", str(target)]) == 1
        assert "E2: FAIL" in capsys.readouterr().out
        assert not target.parent.exists()
    else:
        with pytest.raises(RuntimeError, match="no usable GitHub topic responses"):
            discovery.channel_e2_github(SINCE)
        assert "configured=0 attempted=0 completed=0" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["shape", "json", "http", "request"])
@pytest.mark.parametrize("failed_first", [False, True])
def test_e2_partial_topic_failure_keeps_valid_rows_in_private_output(
        failure, failed_first, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    topics = ["synthetic-failed", "synthetic-ready"]
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics if failed_first else topics[::-1])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if "synthetic-ready" in url:
            return observation_response({"items": [{
                "full_name": "synthetic-owner/synthetic-tool",
                "html_url": "https://example.com/synthetic-github-tool",
                "stargazers_count": 75, "created_at": "2031-01-02T00:00:00Z",
                "description": "Synthetic useful observation.",
            }]})
        if failure == "request":
            raise discovery.requests.RequestException("synthetic unavailable topic")
        return observation_response(
            ValueError("synthetic malformed JSON") if failure == "json" else {},
            status=503 if failure == "http" else 200)
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/reports/partial-github.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count("https://example.com/synthetic-github-tool") == 1
    assert "synthetic-owner/synthetic-tool" in content
    assert "topic:synthetic-failed" not in content
    assert len(calls) == 2
    summary = capsys.readouterr()
    assert "E2: 1 candidates" in summary.out
    assert "configured=2 attempted=2 completed=1" in summary.err
    assert "synthetic-failed: failed" in summary.err


@pytest.mark.parametrize("healthy", [None, "e1-rss", "e1-atom", "e2", "e3", "e5"])
def test_default_sweep_distinguishes_invalid_bodies_from_valid_empty(
        healthy, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-topic"])
    monkeypatch.setattr(discovery, "NPM_PACKAGES", ["synthetic-package"])
    monkeypatch.setattr(discovery, "YOUTUBE_CHANNELS", [])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if url == discovery.PULSEMCP_FEED:
            feed = {"e1-rss": "<rss><channel/></rss>", "e1-atom": ATOM.format("")}
            return observation_response(text=feed.get(healthy, "<html/>"))
        if "api.github.com/search/repositories" in url:
            return observation_response({"items": []} if healthy == "e2" else {})
        if url == discovery.HF_SPACES_URL:
            return observation_response([] if healthy == "e3" else {})
        if url == discovery.HN_API:
            return observation_response({"hits": []} if healthy == "e5" else {})
        if "/downloads/range/" in url:
            return observation_response(status=503)
        pytest.fail("unexpected synthetic surface request")
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/whole-sweep.md"
    assert discovery.main(["--since", str(SINCE), "--out", str(target)]) == (
        1 if healthy is None else 0)
    summary = capsys.readouterr()
    assert f"failures: {6 if healthy is None else 5}/6" in summary.out
    assert not any("youtube.com" in url for url in calls)
    assert not target.parent.exists()


@pytest.mark.parametrize("channel,payload,text,expected_url", [
    ("e1", None,
     "<rss><channel><item/><item><title>Synthetic feed tool</title>"
     "<link>https://example.com/synthetic-feed-tool</link>"
     "<pubDate>2031-01-02</pubDate></item></channel></rss>",
     "https://example.com/synthetic-feed-tool"),
    ("e1", None, ATOM.format("<entry/>" + VIDEO),
     "https://example.com/synthetic-video"),
    ("e3", [{}, {"id": "synthetic-owner/synthetic-space",
                 "lastModified": "2031-01-02T00:00:00Z", "likes": 3,
                 "trendingScore": 2, "cardData": {"title": "Synthetic space"}}], "",
     "https://huggingface.co/spaces/synthetic-owner/synthetic-space"),
    ("e5", {"hits": [{"title": "Synthetic below threshold", "points": 1},
                    {"objectID": "synthetic-item", "title": "Synthetic HN tool",
                     "url": "https://example.com/synthetic-hn-tool", "points": 30}]}, "",
     "https://example.com/synthetic-hn-tool"),
])
def test_schema_valid_partial_candidates_still_persist(
        channel, payload, text, expected_url, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery.requests, "get",
                        lambda *a, **k: observation_response(payload, text=text))
    target = repository / "data/deliverables/reports/partial-candidates.md"
    assert discovery.main(["--channel", channel, "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count(expected_url) == 1
    assert "Synthetic below threshold" not in content
    assert channel.upper() + ": 1 candidates" in capsys.readouterr().out


@pytest.mark.parametrize("has_items", [False, True])
@pytest.mark.parametrize("through_main", [False, True])
def test_e2_incomplete_topic_never_completes_or_writes(
        has_items, through_main, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-incomplete"])
    items = [{"full_name": "synthetic-owner/partial-tool",
              "html_url": "https://example.com/partial-github-tool",
              "stargazers_count": 75, "description": "Synthetic partial observation."}] if has_items else []
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response({"incomplete_results": True, "items": items})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/incomplete-github.md"
    if through_main:
        assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                               "--out", str(target)]) == 1
    else:
        with pytest.raises(RuntimeError, match="no usable GitHub topic responses"):
            discovery.channel_e2_github(SINCE)
    captured = capsys.readouterr()
    assert "incomplete_results=true" in captured.err
    assert "configured=1 attempted=1 completed=0" in captured.err
    assert "completed=1" not in captured.err
    if through_main:
        assert "E2: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert len(calls) == 1 and not target.parent.exists()


@pytest.mark.parametrize("incomplete_first", [False, True])
def test_e2_incomplete_topic_preserves_completed_topics_only(
        incomplete_first, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    topics = ["synthetic-incomplete", "synthetic-empty", "synthetic-ready"]
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", topics if incomplete_first else topics[::-1])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        incomplete = "synthetic-incomplete" in url
        items = [] if "synthetic-empty" in url else [{
            "full_name": "synthetic-owner/partial-tool" if incomplete else "synthetic-owner/ready-tool",
            "html_url": "https://example.com/partial-github-tool" if incomplete else
                        "https://example.com/ready-github-tool",
            "stargazers_count": 75, "description": "Synthetic observation.",
        }]
        return observation_response({"incomplete_results": incomplete, "items": items})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/reports/complete-topics.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    content = target.read_text(encoding="utf-8")
    assert content.count("https://example.com/ready-github-tool") == 1
    assert "partial-github-tool" not in content and "synthetic-owner/partial-tool" not in content
    assert len(calls) == 3
    captured = capsys.readouterr()
    assert "E2: 1 candidates" in captured.out
    assert "configured=3 attempted=3 completed=2" in captured.err
    assert "synthetic-incomplete: failed" in captured.err and "incomplete_results=true" in captured.err


def test_e2_explicit_complete_empty_response_remains_success(
        discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-empty"])
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return observation_response({"total_count": 0, "incomplete_results": False, "items": []})
    monkeypatch.setattr(discovery.requests, "get", get)
    target = repository / "data/deliverables/uncreated/complete-empty-github.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 0
    captured = capsys.readouterr()
    assert "E2: 0 candidates" in captured.out and "failures: 0/1" in captured.out
    assert "configured=1 attempted=1 completed=1" in captured.err
    assert len(calls) == 1 and not target.parent.exists()


@pytest.mark.parametrize("invalid_flag", [None, 1, "false"])
def test_e2_malformed_completeness_metadata_is_not_empty_success(
        invalid_flag, discovery, companion, monkeypatch, capsys):
    repository, _, _, _ = companion
    monkeypatch.setattr(discovery, "GITHUB_TOPICS", ["synthetic-invalid"])
    monkeypatch.setattr(discovery.requests, "get", lambda *a, **k:
                        observation_response({"incomplete_results": invalid_flag, "items": []}))
    target = repository / "data/deliverables/uncreated/invalid-completeness.md"
    assert discovery.main(["--channel", "e2", "--since", str(SINCE),
                           "--out", str(target)]) == 1
    captured = capsys.readouterr()
    assert "expected boolean incomplete_results" in captured.err
    assert "configured=1 attempted=1 completed=0" in captured.err
    assert "E2: FAIL" in captured.out and "failures: 1/1" in captured.out
    assert not target.parent.exists()


import copy
import io
import json


@pytest.fixture
def poller(monkeypatch):
    module = load_writer("poll_surfaces")
    def forbidden(*args, **kwargs):
        pytest.fail("unexpected provider request")
    monkeypatch.setattr(module, "_http_json", forbidden)
    monkeypatch.setattr(module, "_gh_json", forbidden)
    monkeypatch.setattr(module.urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(module, "_now", lambda: dt.datetime(2031, 1, 3, tzinfo=dt.timezone.utc))
    return module


def set_poll_payload(poller, monkeypatch, surface, payload):
    if surface == "E1":
        monkeypatch.setattr(poller.urllib.request, "urlopen",
                            lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    else:
        monkeypatch.setattr(poller, "_gh_json" if surface == "E2" else "_http_json",
                            lambda *a, **k: copy.deepcopy(payload))


def invoke_poll(poller, monkeypatch, tmp_path, surface, *, dry_run=False):
    configuration = tmp_path / "synthetic-poll-config.json"
    configuration.write_text(json.dumps({"E2": {"topics": ["synthetic-topic"]}}), encoding="utf-8")
    argv = ["poll_surfaces.py", "--only", surface, "--config", str(configuration)]
    if dry_run:
        argv.append("--dry-run")
    monkeypatch.setattr(poller.sys, "argv", argv)
    return poller.main()


@pytest.mark.parametrize("surface,key", [("E1", "servers"), ("E2", "items"), ("E3", None), ("E5", "hits")])
@pytest.mark.parametrize("malformation", ["missing", "error", "null", "scalar", "row", "rows_type"])
def test_poll_invalid_envelopes_never_count_as_success(
        surface, key, malformation, poller, companion, tmp_path, monkeypatch, capsys):
    invalid = {"missing": {}, "error": {"error": "synthetic provider failure"},
               "null": None, "scalar": "synthetic", "row": [None], "rows_type": {}}
    payload = invalid[malformation]
    if key is not None and malformation not in {"missing", "error"}:
        payload = {key: payload}
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    output = capsys.readouterr().out
    assert "DEGRADED" in output and "surfaces_ok=0/1" in output
    assert "new=0" in output and f"degraded={surface}" in output
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,payload", [
    ("E1", {"servers": []}), ("E2", {"items": [], "incomplete_results": False}),
    ("E3", []), ("E5", {"hits": []})])
def test_poll_valid_empty_envelope_completes_without_writing(
        surface, payload, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    output = capsys.readouterr().out
    assert "surfaces_ok=1/1" in output and "degraded=none" in output and "new=0" in output
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,key", [("E1", "servers"), ("E2", "items"), ("E5", "hits")])
def test_poll_error_envelope_cannot_be_hidden_by_empty_result_field(
        surface, key, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, {key: [], "error": "synthetic provider error"})
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    assert "surfaces_ok=0/1" in capsys.readouterr().out
    assert not (companion[0] / "data/surface-inbox.jsonl").exists()


@pytest.mark.parametrize("surface,payload,key", [
    ("E1", {"servers": [
        {"name": "synthetic-visible", "github_stars": 100, "external_url": "https://example.com/e1"},
        {"name": "synthetic-filtered", "github_stars": 1}]}, "E1:synthetic-visible"),
    ("E3", [{"id": "example-org/synthetic-visible", "trendingScore": 5},
             {"id": "example-org/synthetic-filtered", "trendingScore": -1}],
     "E3:example-org/synthetic-visible"),
    ("E5", {"hits": [{"objectID": "synthetic-visible", "title": "Synthetic tool", "points": 50},
                       {"objectID": "synthetic-filtered", "title": "Synthetic minor", "points": 1}]},
     "E5:synthetic-visible"),
])
def test_poll_valid_nonempty_responses_keep_original_filters_and_fields(
        surface, payload, key, poller, companion, tmp_path, monkeypatch, capsys):
    set_poll_payload(poller, monkeypatch, surface, payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, surface) == 0
    row = json.loads((companion[0] / "data/surface-inbox.jsonl").read_text(encoding="utf-8"))
    assert row["key"] == key and row["surface"] == surface and row["discovered_at"]
    assert "surfaces_ok=1/1" in capsys.readouterr().out


@pytest.mark.parametrize("topics", [[], [None], [""], "synthetic-topic"])
def test_poll_e2_unconfigured_cannot_claim_a_completed_request(poller, monkeypatch, topics):
    with pytest.raises(ValueError, match="nonempty topic"):
        poller.surface_E2_github_velocity({"E2": {"topics": topics}}, 7)


def github_observation(name):
    return {"full_name": "example-org/" + name, "html_url": "https://example.com/" + name,
            "stargazers_count": 100, "created_at": "2031-01-02T00:00:00Z",
            "description": "Synthetic useful observation."}


@pytest.mark.parametrize("failure", ["request", "shape", "json"])
@pytest.mark.parametrize("failed_first", [False, True])
def test_poll_e2_retains_successes_in_both_topic_orders(
        failure, failed_first, poller, monkeypatch):
    topics = ["synthetic-ready", "synthetic-failed", "synthetic-later"]
    if failed_first:
        topics.insert(0, topics.pop(1))
    calls = []
    def request(path):
        calls.append(path)
        if "synthetic-failed" in path:
            if failure == "shape":
                return {"message": "synthetic provider failure"}
            raise (RuntimeError("synthetic transport failure") if failure == "request" else
                   ValueError("synthetic malformed JSON"))
        name = "synthetic-ready" if "synthetic-ready" in path else "synthetic-later"
        return {"items": [github_observation(name), github_observation("synthetic-shared")],
                "incomplete_results": False}
    monkeypatch.setattr(poller, "_gh_json", request)
    result = poller.surface_E2_github_velocity({"E2": {"topics": topics}}, 7)
    assert result.status == "DEGRADED" and result.completed == 2 and result.attempted == 3
    names = [row["title"] for row in result]
    expected = [topic for topic in topics if topic != "synthetic-failed"]
    assert names == ["example-org/" + expected[0], "example-org/synthetic-shared", "example-org/" + expected[1]]
    assert len(calls) == 3 and len(result.errors) == 1


@pytest.mark.parametrize("flag", [True, None, 1, "false"])
def test_poll_e2_incomplete_or_invalid_completion_cannot_be_all_green(
        flag, poller, companion, tmp_path, monkeypatch, capsys):
    payload = {"incomplete_results": flag, "items": [github_observation("synthetic-partial")]}
    set_poll_payload(poller, monkeypatch, "E2", payload)
    assert invoke_poll(poller, monkeypatch, tmp_path, "E2") == 0
    output = capsys.readouterr().out
    assert "DEGRADED" in output and "surfaces_ok=0/1" in output and "0/1 requests complete" in output
    target = companion[0] / "data/surface-inbox.jsonl"
    if flag is True:
        row = json.loads(target.read_text(encoding="utf-8"))
        assert row["title"] == "example-org/synthetic-partial"
        assert row["raw"]["incomplete_results"] is True
        assert "incomplete_results=true" in output
    else:
        assert not target.exists()


def test_poll_main_retains_partial_topic_rows_without_duplicate_replay(
        poller, companion, tmp_path, monkeypatch, capsys):
    def request(path):
        if "synthetic-failed" in path:
            raise RuntimeError("synthetic transport failure")
        return {"items": [github_observation("synthetic-retained")], "incomplete_results": False}
    monkeypatch.setattr(poller, "_gh_json", request)
    cfg = tmp_path / "synthetic-poll-config.json"
    cfg.write_text(json.dumps({"E2": {"topics": ["synthetic-ready", "synthetic-failed"]}}))
    monkeypatch.setattr(poller.sys, "argv", ["poll_surfaces.py", "--config", str(cfg), "--only", "E2"])
    assert poller.main() == 0
    target = companion[0] / "data/surface-inbox.jsonl"
    first = target.read_bytes()
    assert json.loads(first)["title"] == "example-org/synthetic-retained"
    assert "surfaces_ok=0/1" in capsys.readouterr().out
    assert poller.main() == 0
    assert target.read_bytes() == first
    assert "new=0" in capsys.readouterr().out
