import unittest

from app import calculate_flooring, calculate_paint, calculate_panels, calculate_studs, calculate_trim


class StudCalculatorTests(unittest.TestCase):
    def test_eight_foot_wall_at_sixteen_inches(self):
        result = calculate_studs(
            {
                "wallLength": 8,
                "wallLengthUnit": "ft",
                "wallHeight": 8,
                "wallHeightUnit": "ft",
                "spacing": 16,
                "spacingUnit": "in",
                "stockLength": 8,
                "stockLengthUnit": "ft",
                "studPrice": 10,
                "extraStuds": 0,
                "studWaste": 0,
            }
        )

        self.assertEqual(result["baseStuds"], 7)
        self.assertEqual(result["pieceType"], "Piece")
        self.assertEqual(result["totalStuds"], 7)
        self.assertEqual(result["stockPieces"], 7)
        self.assertEqual(result["totalCost"], 70)

    def test_long_stock_can_cut_two_studs(self):
        result = calculate_studs(
            {
                "wallLength": 8,
                "wallLengthUnit": "ft",
                "wallHeight": 8,
                "wallHeightUnit": "ft",
                "spacing": 16,
                "spacingUnit": "in",
                "stockLength": 16,
                "stockLengthUnit": "ft",
                "studPrice": 20,
                "extraStuds": 0,
                "studWaste": 0,
            }
        )

        self.assertEqual(result["studsPerStockPiece"], 2)
        self.assertEqual(result["stockPieces"], 4)
        self.assertEqual(result["totalCost"], 80)


class PanelCalculatorTests(unittest.TestCase):
    def test_eight_by_eight_wall_needs_two_four_by_eight_sheets(self):
        result = calculate_panels(
            {
                "surfaceLength": 8,
                "surfaceLengthUnit": "ft",
                "surfaceHeight": 8,
                "surfaceHeightUnit": "ft",
                "panelWidth": 4,
                "panelWidthUnit": "ft",
                "panelHeight": 8,
                "panelHeightUnit": "ft",
                "openingsArea": 0,
                "openingsAreaUnit": "ft2",
                "panelWaste": 0,
                "panelPrice": 15,
            }
        )

        self.assertEqual(result["rawPanels"], 2)
        self.assertEqual(result["panels"], 2)
        self.assertEqual(result["totalCost"], 30)


class FlooringCalculatorTests(unittest.TestCase):
    def test_flooring_boxes_include_waste(self):
        result = calculate_flooring(
            {
                "floorLength": 12,
                "floorLengthUnit": "ft",
                "floorWidth": 10,
                "floorWidthUnit": "ft",
                "floorOpeningsArea": 0,
                "floorOpeningsAreaUnit": "ft2",
                "floorCoverage": 20,
                "floorCoverageUnit": "ft2",
                "floorWaste": 10,
                "floorPrice": 50,
            }
        )

        self.assertEqual(result["rawBoxes"], 6)
        self.assertEqual(result["boxes"], 7)
        self.assertEqual(result["totalCost"], 350)


class PaintCalculatorTests(unittest.TestCase):
    def test_paint_containers_include_ceiling_and_coats(self):
        result = calculate_paint(
            {
                "paintLength": 12,
                "paintLengthUnit": "ft",
                "paintWidth": 10,
                "paintWidthUnit": "ft",
                "paintHeight": 8,
                "paintHeightUnit": "ft",
                "paintOpeningsArea": 40,
                "paintOpeningsAreaUnit": "ft2",
                "paintCoverage": 400,
                "paintCoverageUnit": "ft2",
                "paintCoats": 2,
                "paintPrice": 55,
                "includeCeiling": "on",
            }
        )

        self.assertEqual(result["coats"], 2)
        self.assertEqual(result["containers"], 3)
        self.assertEqual(result["totalCost"], 165)


class TrimCalculatorTests(unittest.TestCase):
    def test_trim_pieces_include_openings_and_waste(self):
        result = calculate_trim(
            {
                "trimLength": 12,
                "trimLengthUnit": "ft",
                "trimWidth": 10,
                "trimWidthUnit": "ft",
                "trimOpeningsLength": 3,
                "trimOpeningsLengthUnit": "ft",
                "trimPieceLength": 8,
                "trimPieceLengthUnit": "ft",
                "trimWaste": 10,
                "trimPrice": 9,
            }
        )

        self.assertEqual(result["pieces"], 6)
        self.assertEqual(result["totalCost"], 54)


if __name__ == "__main__":
    unittest.main()
