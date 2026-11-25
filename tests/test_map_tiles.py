import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_osm_tiles_are_configurable_attributed_and_allowed_by_csp():
    settings = (ROOT / "config/settings/base.py").read_text(encoding="utf-8")
    report_template = (ROOT / "templates/complaints/report.html").read_text(encoding="utf-8")
    map_script = (ROOT / "static/js/report-map.js").read_text(encoding="utf-8")
    middleware = (ROOT / "config/middleware.py").read_text(encoding="utf-8")

    assert '"https://tile.openstreetmap.org/{z}/{x}/{y}.png"' in settings
    assert 'data-tile-url="{{ map_tile_url }}"' in report_template
    assert "L.tileLayer(mapNode.dataset.tileUrl" in map_script
    assert 'href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' in map_script
    image_sources = re.search(r"img-src ([^;]+);", middleware).group(1).split()
    assert image_sources == ["'self'", "data:", "https://tile.openstreetmap.org"]
