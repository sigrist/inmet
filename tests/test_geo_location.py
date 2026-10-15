"""Tests for INMET geo-location alert metadata."""

from datetime import datetime, timedelta
from types import SimpleNamespace

from custom_components.inmet.geo_location import (
    INMET_TIME_ZONE,
    InmetEvent,
    _area_description,
    _bbox_from_polygon,
    _parse_alert_datetime,
)


def test_parse_alert_datetime_uses_brasilia_timezone() -> None:
    """INMET's local timestamps keep their UTC offset."""
    assert _parse_alert_datetime("2026-09-18 22:00") == datetime(
        2026, 9, 18, 22, 0, tzinfo=INMET_TIME_ZONE
    )


def test_area_description_prefers_states() -> None:
    """The compact state list is the best default area description."""
    assert _area_description(
        {
            "estados": "SP, RJ",
            "mesorregioes": "Metropolitana de Sao Paulo",
            "municipios": "Sao Paulo",
        }
    ) == "SP, RJ"


def test_area_description_falls_back_to_municipalities() -> None:
    """Area data remains useful when states and mesoregions are absent."""
    assert _area_description({"municipios": ["Campinas", "Valinhos"]}) == (
        "Campinas, Valinhos"
    )


def test_bbox_from_polygon() -> None:
    """A GeoJSON polygon becomes a compact longitude-first bounding box."""
    polygon = (
        '{"type":"Polygon","coordinates":'
        '[[[-47.1,-23.1],[-46.9,-23.1],[-46.9,-22.9],[-47.1,-23.1]]]}'
    )
    assert _bbox_from_polygon(polygon) == [-47.1, -23.1, -46.9, -22.9]


def test_bbox_from_multipolygon() -> None:
    """All component polygons contribute to a multi-polygon bounding box."""
    polygon = (
        '{"type":"MultiPolygon","coordinates":'
        '[[[[-47,-23],[-46,-23],[-46,-22],[-47,-23]]],'
        '[[[-45,-21],[-44,-21],[-44,-20],[-45,-21]]]]}'
    )
    assert _bbox_from_polygon(polygon) == [-47.0, -23.0, -44.0, -20.0]


def test_bbox_omits_malformed_geometry() -> None:
    """Malformed or unsupported geometry never leaks into entity attributes."""
    assert _bbox_from_polygon("not json") is None
    assert _bbox_from_polygon('{"type":"Point","coordinates":[-47,-23]}') is None


def test_entity_publishes_card_metadata() -> None:
    """The geo-location entity exposes compact metadata for alert cards."""
    manager = SimpleNamespace(latitude=lambda: -22.9, longitude=lambda: -47.1)
    event = InmetEvent(manager, "entry", "56051")
    event.hass = SimpleNamespace(
        config=SimpleNamespace(latitude=-22.9, longitude=-47.1)
    )
    event._update_from_feed(
        {
            "descricao": "Tempestade",
            "severidade": "Perigo Potencial",
            "id_severidade": 6,
            "riscos": ["Chuva forte"],
            "instrucoes": ["Fique em local seguro"],
            "aviso_cor": "#FFFE00",
            "alterado": False,
            "encerrado": False,
            "future": False,
            "inicio": "2026-10-15 00:01",
            "fim": "2026-10-15 23:59",
            "id_sequencia": 1,
            "updated_at": "2026-10-14T00:00:00.000Z",
            "estados": "CE, BA",
            "poligono": (
                '{"type":"Polygon","coordinates":'
                '[[[-47,-23],[-46,-23],[-46,-22],[-47,-23]]]}'
            ),
        }
    )

    attributes = event.extra_state_attributes
    assert attributes["updated_at"] == "2026-10-14T00:00:00.000Z"
    assert attributes["area"] == "CE, BA"
    assert attributes["bbox"] == [-47.0, -23.0, -46.0, -22.0]
    assert attributes["start_date"].utcoffset() == timedelta(hours=-3)
