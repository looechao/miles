import datetime
import importlib
import json
import runpy
from pathlib import Path

import gpxpy.gpx


def test_gpx_entrypoint_exports_activity(monkeypatch, tmp_path):
    source = Path(__file__).parent / "run_page"
    monkeypatch.syspath_prepend(str(source))
    config = importlib.import_module("config")
    database = importlib.import_module("generator.db")
    logger = importlib.import_module("synced_data_file_logger")
    folder = tmp_path / "gpx"
    folder.mkdir()
    output = tmp_path / "activities.json"
    monkeypatch.setattr(config, "GPX_FOLDER", str(folder))
    monkeypatch.setattr(config, "SQL_FILE", str(tmp_path / "activities.db"))
    monkeypatch.setattr(config, "JSON_FILE", str(output))
    monkeypatch.setattr(logger, "SYNCED_FILE", str(tmp_path / "imported.json"))
    monkeypatch.setattr(database.g, "reverse", lambda *_, **__: "Fixture location")

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack(name="Fixture run")
    track.type = "running"
    segment = gpxpy.gpx.GPXTrackSegment()
    start = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    for i in range(5):
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=30 + i * 0.001,
                longitude=120 + (i % 2) * 0.001,
                time=start + datetime.timedelta(seconds=i * 10),
            )
        )
    track.segments.append(segment)
    gpx.tracks.append(track)
    (folder / "fixture.gpx").write_text(gpx.to_xml())

    runpy.run_path(str(source / "gpx_sync.py"), run_name="__main__")

    activities = json.loads(output.read_text())
    assert len(activities) == 1
    assert activities[0]["name"] == "Fixture run"
    assert activities[0]["distance"] > 100
    assert activities[0]["summary_polyline"]
    assert activities[0]["location_country"] == "Fixture location"
    assert json.loads((tmp_path / "imported.json").read_text())
