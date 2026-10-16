import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("filter_before_saving", [False, True])
def test_web_sync_respects_route_privacy(monkeypatch, filter_before_saving):
    monkeypatch.syspath_prepend(str(Path(__file__).parent / "run_page"))
    sync = importlib.import_module("strava_web_sync")
    monkeypatch.setattr(
        sync, "IGNORE_BEFORE_SAVING", filter_before_saving, raising=False
    )
    streams = {"latlng": [[30.0, 120.0], [30.01, 120.01]]}
    monkeypatch.setattr(sync, "_fetch_streams", lambda *_: streams)
    filtered = []

    def redact(route):
        filtered.append(route)
        return "redacted-route"

    monkeypatch.setattr(sync, "filter_out", redact, raising=False)
    saved = []
    monkeypatch.setattr(
        sync, "update_or_create_activity", lambda _, activity: saved.append(activity)
    )
    commits = []
    session = SimpleNamespace(commit=lambda: commits.append(True))

    sync._sync_one(None, session, {"id": 1, "sport_type": "Run"})

    source_route = sync._polyline_encode(streams["latlng"])
    assert source_route
    expected = "redacted-route" if filter_before_saving else source_route
    assert len(saved) == 1
    assert saved[0].map.summary_polyline == expected
    assert filtered == ([source_route] if filter_before_saving else [])
    assert commits == [True]
