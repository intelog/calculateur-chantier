from __future__ import annotations

import argparse
import json
import math
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "public"

LENGTH_TO_INCHES = {
    "in": 1.0,
    "ft": 12.0,
    "cm": 0.39370078740157477,
    "m": 39.37007874015748,
}

AREA_TO_SQUARE_INCHES = {
    "in2": 1.0,
    "ft2": 144.0,
    "cm2": 0.15500031000062,
    "m2": 1550.0031000062,
}


class CalculatorError(ValueError):
    """Raised when a request contains invalid calculator input."""


def _number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if value is None or value == "":
        raise CalculatorError(f"{label} est requis.")

    if isinstance(value, str):
        value = value.strip().replace(",", ".")

    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CalculatorError(f"{label} doit etre un nombre.") from exc

    if not math.isfinite(parsed):
        raise CalculatorError(f"{label} doit etre un nombre valide.")

    if minimum is not None and parsed < minimum:
        raise CalculatorError(f"{label} doit etre au moins {minimum:g}.")

    return parsed


def _unit(data: dict[str, Any], key: str, allowed: dict[str, float], label: str) -> str:
    value = data.get(key)
    if value not in allowed:
        raise CalculatorError(f"{label} contient une unite invalide.")
    return str(value)


def _length_to_inches(
    data: dict[str, Any],
    value_key: str,
    unit_key: str,
    label: str,
    *,
    minimum: float = 0.0001,
) -> float:
    unit = _unit(data, unit_key, LENGTH_TO_INCHES, label)
    return _number(data.get(value_key), label, minimum=minimum) * LENGTH_TO_INCHES[unit]


def _area_to_square_inches(data: dict[str, Any], value_key: str, unit_key: str, label: str) -> float:
    unit = _unit(data, unit_key, AREA_TO_SQUARE_INCHES, label)
    return _number(data.get(value_key), label, minimum=0) * AREA_TO_SQUARE_INCHES[unit]


def _money(value: float) -> str:
    return f"{value:.2f} $"


def _format_length(inches: float) -> str:
    feet = inches / 12
    meters = inches * 0.0254
    return f"{feet:.2f} pi ({meters:.2f} m)"


def _format_area(square_inches: float) -> str:
    square_feet = square_inches / 144
    square_meters = square_inches * 0.00064516
    return f"{square_feet:.2f} pi2 ({square_meters:.2f} m2)"


def _checked(value: Any) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def calculate_studs(data: dict[str, Any]) -> dict[str, Any]:
    piece_type = str(data.get("structureType") or "Piece")
    wall_length = _length_to_inches(data, "wallLength", "wallLengthUnit", "Longueur")
    wall_height = _length_to_inches(data, "wallHeight", "wallHeightUnit", "Hauteur")
    spacing = _length_to_inches(data, "spacing", "spacingUnit", "Espacement")
    stock_length = _length_to_inches(data, "stockLength", "stockLengthUnit", "Longueur achetee")
    price = _number(data.get("studPrice", 0), "Prix par piece", minimum=0)
    extras = int(math.ceil(_number(data.get("extraStuds", 0), "Pieces en extra", minimum=0)))
    waste_percent = _number(data.get("studWaste", 0), "Perte", minimum=0)

    if spacing > wall_length:
        base_studs = 2
    else:
        base_studs = int(math.ceil(wall_length / spacing)) + 1

    studs_before_waste = base_studs + extras
    total_studs = int(math.ceil(studs_before_waste * (1 + waste_percent / 100)))

    warnings: list[str] = []
    if stock_length < wall_height:
        studs_per_stock_piece = 0
        stock_pieces = 0
        warnings.append(
            "La longueur achetee est plus courte que la hauteur de coupe. "
            "Choisis une piece plus longue pour calculer le cout."
        )
    else:
        studs_per_stock_piece = max(1, int(stock_length // wall_height))
        stock_pieces = int(math.ceil(total_studs / studs_per_stock_piece))

    used_linear = total_studs * wall_height
    purchased_linear = stock_pieces * stock_length
    waste_linear = max(0, purchased_linear - used_linear)
    actual_average_spacing = wall_length / max(1, base_studs - 1)
    total_cost = stock_pieces * price

    return {
        "pieceType": piece_type,
        "baseStuds": base_studs,
        "extraStuds": extras,
        "studsBeforeWaste": studs_before_waste,
        "totalStuds": total_studs,
        "studsPerStockPiece": studs_per_stock_piece,
        "stockPieces": stock_pieces,
        "cutLength": _format_length(wall_height),
        "stockLength": _format_length(stock_length),
        "usedLinear": _format_length(used_linear),
        "purchasedLinear": _format_length(purchased_linear),
        "wasteLinear": _format_length(waste_linear),
        "averageSpacing": _format_length(actual_average_spacing),
        "totalCost": round(total_cost, 2),
        "totalCostLabel": _money(total_cost),
        "warnings": warnings,
    }


def calculate_panels(data: dict[str, Any]) -> dict[str, Any]:
    surface_length = _length_to_inches(data, "surfaceLength", "surfaceLengthUnit", "Longueur a couvrir")
    surface_height = _length_to_inches(data, "surfaceHeight", "surfaceHeightUnit", "Hauteur a couvrir")
    panel_width = _length_to_inches(data, "panelWidth", "panelWidthUnit", "Largeur du panneau")
    panel_height = _length_to_inches(data, "panelHeight", "panelHeightUnit", "Hauteur du panneau")
    openings = _area_to_square_inches(data, "openingsArea", "openingsAreaUnit", "Surface a retirer")
    waste_percent = _number(data.get("panelWaste", 0), "Perte", minimum=0)
    price = _number(data.get("panelPrice", 0), "Prix par feuille", minimum=0)

    gross_area = surface_length * surface_height
    if openings > gross_area:
        openings = gross_area

    net_area = max(0, gross_area - openings)
    panel_area = panel_width * panel_height
    raw_panels = net_area / panel_area if panel_area else 0
    panels = int(math.ceil(raw_panels * (1 + waste_percent / 100)))
    purchased_area = panels * panel_area
    surplus_area = max(0, purchased_area - net_area)
    total_cost = panels * price

    return {
        "grossArea": _format_area(gross_area),
        "netArea": _format_area(net_area),
        "panelArea": _format_area(panel_area),
        "rawPanels": round(raw_panels, 2),
        "panels": panels,
        "purchasedArea": _format_area(purchased_area),
        "surplusArea": _format_area(surplus_area),
        "totalCost": round(total_cost, 2),
        "totalCostLabel": _money(total_cost),
    }


def calculate_flooring(data: dict[str, Any]) -> dict[str, Any]:
    floor_length = _length_to_inches(data, "floorLength", "floorLengthUnit", "Longueur du plancher")
    floor_width = _length_to_inches(data, "floorWidth", "floorWidthUnit", "Largeur du plancher")
    openings = _area_to_square_inches(data, "floorOpeningsArea", "floorOpeningsAreaUnit", "Surface a retirer")
    coverage = _area_to_square_inches(data, "floorCoverage", "floorCoverageUnit", "Couverture par boite")
    waste_percent = _number(data.get("floorWaste", 0), "Perte", minimum=0)
    price = _number(data.get("floorPrice", 0), "Prix par boite", minimum=0)

    if coverage <= 0:
        raise CalculatorError("Couverture par boite doit etre plus grande que 0.")

    gross_area = floor_length * floor_width
    net_area = max(0, gross_area - min(openings, gross_area))
    raw_boxes = net_area / coverage
    boxes = int(math.ceil(raw_boxes * (1 + waste_percent / 100)))
    purchased_area = boxes * coverage
    surplus_area = max(0, purchased_area - net_area)
    total_cost = boxes * price

    return {
        "grossArea": _format_area(gross_area),
        "netArea": _format_area(net_area),
        "coverage": _format_area(coverage),
        "rawBoxes": round(raw_boxes, 2),
        "boxes": boxes,
        "purchasedArea": _format_area(purchased_area),
        "surplusArea": _format_area(surplus_area),
        "totalCost": round(total_cost, 2),
        "totalCostLabel": _money(total_cost),
    }


def calculate_paint(data: dict[str, Any]) -> dict[str, Any]:
    room_length = _length_to_inches(data, "paintLength", "paintLengthUnit", "Longueur de la piece")
    room_width = _length_to_inches(data, "paintWidth", "paintWidthUnit", "Largeur de la piece")
    room_height = _length_to_inches(data, "paintHeight", "paintHeightUnit", "Hauteur des murs")
    openings = _area_to_square_inches(data, "paintOpeningsArea", "paintOpeningsAreaUnit", "Surface a retirer")
    coverage = _area_to_square_inches(data, "paintCoverage", "paintCoverageUnit", "Couverture par contenant")
    coats = int(math.ceil(_number(data.get("paintCoats", 1), "Nombre de couches", minimum=1)))
    price = _number(data.get("paintPrice", 0), "Prix par contenant", minimum=0)

    if coverage <= 0:
        raise CalculatorError("Couverture par contenant doit etre plus grande que 0.")

    wall_area = 2 * (room_length + room_width) * room_height
    ceiling_area = room_length * room_width if _checked(data.get("includeCeiling")) else 0
    net_area = max(0, wall_area + ceiling_area - min(openings, wall_area + ceiling_area))
    area_with_coats = net_area * coats
    containers = int(math.ceil(area_with_coats / coverage))
    total_cost = containers * price

    return {
        "wallArea": _format_area(wall_area),
        "ceilingArea": _format_area(ceiling_area),
        "netArea": _format_area(net_area),
        "areaWithCoats": _format_area(area_with_coats),
        "coverage": _format_area(coverage),
        "coats": coats,
        "containers": containers,
        "totalCost": round(total_cost, 2),
        "totalCostLabel": _money(total_cost),
    }


def calculate_trim(data: dict[str, Any]) -> dict[str, Any]:
    room_length = _length_to_inches(data, "trimLength", "trimLengthUnit", "Longueur de la piece")
    room_width = _length_to_inches(data, "trimWidth", "trimWidthUnit", "Largeur de la piece")
    openings = _length_to_inches(
        data,
        "trimOpeningsLength",
        "trimOpeningsLengthUnit",
        "Longueur a retirer",
        minimum=0,
    )
    piece_length = _length_to_inches(data, "trimPieceLength", "trimPieceLengthUnit", "Longueur d'une moulure")
    waste_percent = _number(data.get("trimWaste", 0), "Perte", minimum=0)
    price = _number(data.get("trimPrice", 0), "Prix par moulure", minimum=0)

    perimeter = 2 * (room_length + room_width)
    net_length = max(0, perimeter - min(openings, perimeter))
    needed_length = net_length * (1 + waste_percent / 100)
    pieces = int(math.ceil(needed_length / piece_length))
    purchased_length = pieces * piece_length
    surplus_length = max(0, purchased_length - net_length)
    total_cost = pieces * price

    return {
        "perimeter": _format_length(perimeter),
        "netLength": _format_length(net_length),
        "neededLength": _format_length(needed_length),
        "pieceLength": _format_length(piece_length),
        "pieces": pieces,
        "purchasedLength": _format_length(purchased_length),
        "surplusLength": _format_length(surplus_length),
        "totalCost": round(total_cost, 2),
        "totalCostLabel": _money(total_cost),
    }


class CalculatorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        routes = {
            "/api/calculate/studs": calculate_studs,
            "/api/calculate/panels": calculate_panels,
            "/api/calculate/flooring": calculate_flooring,
            "/api/calculate/paint": calculate_paint,
            "/api/calculate/trim": calculate_trim,
        }

        calculator = routes.get(self.path)
        if calculator is None:
            self._send_json({"error": "Route introuvable."}, HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            result = calculator(payload)
        except CalculatorError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except json.JSONDecodeError:
            self._send_json({"error": "Le corps de la requete doit etre du JSON valide."}, HTTPStatus.BAD_REQUEST)
            return

        self._send_json(result)

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise CalculatorError("Le corps de la requete doit etre un objet JSON.")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


def run(host: str, port: int) -> None:
    if not PUBLIC_DIR.exists():
        raise SystemExit("Le dossier public est introuvable.")

    server = ThreadingHTTPServer((host, port), CalculatorHandler)
    url_host = "localhost" if host in {"", "0.0.0.0"} else host
    print(f"Calculateur disponible: http://{url_host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret du serveur.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculateur de materiaux avec interface web.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Adresse d'ecoute.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Port web.")
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
