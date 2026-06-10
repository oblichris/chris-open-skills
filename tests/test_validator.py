from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "agent-chart"
sys.path.insert(0, str(SKILL_ROOT))

from agent_chart.validator import (
    ValidationError,
    inspect_dataframe,
    validate_chart,
)


def _df(columns: dict[str, list]) -> pd.DataFrame:
    return pd.DataFrame(columns)


class TestInspectDataframe(unittest.TestCase):
    def test_int_column(self):
        df = _df({"Revenue": [100, 200, 300]})
        lines = inspect_dataframe(df)
        joined = "\n".join(lines)
        self.assertIn("Revenue", joined)
        self.assertIn("int", joined)

    def test_float_column(self):
        df = _df({"Growth": [1.5, 2.3, 3.1]})
        lines = inspect_dataframe(df)
        joined = "\n".join(lines)
        self.assertIn("float", joined)

    def test_string_column(self):
        df = _df({"Name": ["Alice", "Bob"]})
        lines = inspect_dataframe(df)
        joined = "\n".join(lines)
        self.assertIn("string", joined)

    def test_percent_like_string(self):
        df = _df({"Rate": ["10%", "20%", "30%"]})
        lines = inspect_dataframe(df)
        joined = "\n".join(lines)
        self.assertIn("percent-like string", joined)

    def test_numeric_like_string_with_commas(self):
        df = _df({"Amount": ["1,000", "2,500", "3,200"]})
        lines = inspect_dataframe(df)
        joined = "\n".join(lines)
        self.assertIn("numeric-like string", joined)


class TestValidateChartBasicBar(unittest.TestCase):
    def test_valid_bar_chart(self):
        df = _df({"Year": [2021, 2022, 2023], "Revenue": [100, 130, 160]})
        spec = {"chart_type": "bar", "x": "Year", "y": "Revenue", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 3)
        self.assertIn("数据校验通过", result.summary[0])

    def test_empty_dataframe_raises(self):
        df = pd.DataFrame()
        spec = {"chart_type": "bar", "x": "X", "y": "Y"}
        with self.assertRaises(ValidationError) as ctx:
            validate_chart(df, spec)
        self.assertIn("empty", str(ctx.exception).lower())


class TestValidateChartFieldCheck(unittest.TestCase):
    def test_missing_x_field_raises(self):
        df = _df({"Year": [2021], "Revenue": [100]})
        spec = {"chart_type": "bar", "x": "Month", "y": "Revenue"}
        with self.assertRaises(ValidationError) as ctx:
            validate_chart(df, spec)
        self.assertIn("Month", str(ctx.exception))
        self.assertIn("Available fields", str(ctx.exception))

    def test_no_fields_specified_raises(self):
        df = _df({"Year": [2021], "Revenue": [100]})
        spec = {"chart_type": "bar"}
        with self.assertRaises(ValidationError) as ctx:
            validate_chart(df, spec)
        self.assertIn("No chart fields", str(ctx.exception))


class TestValidateChartNumericCoercion(unittest.TestCase):
    def test_percent_string_coerced(self):
        df = _df({"Label": ["A", "B", "C"], "Value": ["10%", "20%", "30%"]})
        spec = {"chart_type": "bar", "x": "Label", "y": "Value", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        notes = "\n".join(result.spec.get("data_notes", []))
        self.assertIn("percent", notes.lower())

    def test_comma_number_coerced(self):
        df = _df({"Label": ["A", "B"], "Value": ["1,000", "2,500"]})
        spec = {"chart_type": "bar", "x": "Label", "y": "Value", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertTrue(pd.api.types.is_numeric_dtype(result.data["Value"]))

    def test_all_nan_field_raises(self):
        df = _df({"Label": ["A", "B"], "Value": ["xxx", "yyy"]})
        spec = {"chart_type": "bar", "x": "Label", "y": "Value"}
        with self.assertRaises(ValidationError) as ctx:
            validate_chart(df, spec)
        self.assertIn("not numeric", str(ctx.exception))


class TestValidateChartMissingValues(unittest.TestCase):
    def test_rows_with_missing_y_dropped(self):
        df = _df({"Year": [2021, 2022, 2023], "Revenue": [100, None, 160]})
        spec = {"chart_type": "bar", "x": "Year", "y": "Revenue", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 2)
        summary = "\n".join(result.summary)
        self.assertIn("已忽略缺失行", summary)

    def test_all_rows_missing_raises(self):
        df = _df({"Year": [2021, 2022], "Revenue": [None, None]})
        spec = {"chart_type": "bar", "x": "Year", "y": "Revenue"}
        with self.assertRaises(ValidationError):
            validate_chart(df, spec)


class TestValidatePieDonut(unittest.TestCase):
    def test_pie_chart_valid(self):
        df = _df({"Brand": ["A", "B", "C"], "Share": [40, 35, 25]})
        spec = {"chart_type": "pie", "label": "Brand", "value": "Share", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 3)

    def test_donut_chart_valid(self):
        df = _df({"Brand": ["A", "B"], "Share": [60, 40]})
        spec = {"chart_type": "donut", "label": "Brand", "value": "Share", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 2)

    def test_pie_suspicious_total_warns(self):
        df = _df({"Brand": ["A", "B", "C"], "Share": [40, 35, 20]})
        spec = {"chart_type": "pie", "label": "Brand", "value": "Share", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        summary = "\n".join(result.summary)
        self.assertIn("百分比", summary)

    def test_pie_exact_100_no_warning(self):
        df = _df({"Brand": ["A", "B", "C"], "Share": [40, 35, 25]})
        spec = {"chart_type": "pie", "label": "Brand", "value": "Share", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        summary = "\n".join(result.summary)
        self.assertNotIn("百分比", summary)


class TestValidateComboChart(unittest.TestCase):
    def test_combo_with_large_ratio_enables_secondary_y(self):
        df = _df({"Month": ["Jan", "Feb", "Mar"], "Revenue": [1000, 2000, 3000], "Margin": [5.1, 5.2, 5.3]})
        spec = {"chart_type": "combo_bar_line", "x": "Month", "bar_y": "Revenue", "line_y": "Margin", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertTrue(result.spec["secondary_y"])
        summary = "\n".join(result.summary)
        self.assertIn("双轴", summary)

    def test_combo_with_similar_scale_no_secondary_y(self):
        df = _df({"Month": ["Jan", "Feb"], "Revenue": [100, 200], "Margin": [80, 90]})
        spec = {"chart_type": "combo_bar_line", "x": "Month", "bar_y": "Revenue", "line_y": "Margin", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertFalse(result.spec["secondary_y"])


class TestValidateGroupedStackedBar(unittest.TestCase):
    def test_grouped_bar_multiple_y(self):
        df = _df({"Region": ["East", "West"], "Sales": [100, 200], "Profit": [30, 60]})
        spec = {"chart_type": "grouped_bar", "x": "Region", "y": ["Sales", "Profit"], "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 2)

    def test_stacked_bar_multiple_y(self):
        df = _df({"Year": [2021, 2022], "Revenue": [100, 130], "Cost": [60, 70]})
        spec = {"chart_type": "stacked_bar", "x": "Year", "y": ["Revenue", "Cost"], "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 2)


class TestValidateHorizontalBar(unittest.TestCase):
    def test_horizontal_bar_valid(self):
        df = _df({"Company": ["A", "B", "C"], "Count": [10, 25, 18]})
        spec = {"chart_type": "horizontal_bar", "x": "Count", "y": "Company", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 3)


class TestValidateScatter(unittest.TestCase):
    def test_scatter_basic(self):
        df = _df({"Height": [160, 170, 180], "Weight": [55, 65, 75]})
        spec = {"chart_type": "scatter", "x": "Height", "y": "Weight", "output_formats": ["svg"]}
        result = validate_chart(df, spec)
        self.assertEqual(len(result.data), 3)


class TestValidateUnsupportedChartType(unittest.TestCase):
    def test_unsupported_type_raises(self):
        df = _df({"X": [1, 2], "Y": [3, 4]})
        spec = {"chart_type": "radar", "x": "X", "y": "Y"}
        with self.assertRaises(ValidationError) as ctx:
            validate_chart(df, spec)
        self.assertIn("Unsupported chart_type", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
