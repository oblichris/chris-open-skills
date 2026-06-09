from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "agent-chart"
sys.path.insert(0, str(SKILL_ROOT))

from agent_chart.parser import (
    PromptParseError,
    _detect_chart_type,
    _parse_assignments,
    parse_formats,
    parse_prompt,
)


class TestDetectChartTypeChinese(unittest.TestCase):
    def test_bar(self):
        self.assertEqual(_detect_chart_type("生成柱状图"), "bar")

    def test_line(self):
        self.assertEqual(_detect_chart_type("折线图趋势"), "line")

    def test_pie(self):
        self.assertEqual(_detect_chart_type("画一个饼图"), "pie")

    def test_donut(self):
        self.assertEqual(_detect_chart_type("环形图展示"), "donut")

    def test_scatter(self):
        self.assertEqual(_detect_chart_type("散点图分析"), "scatter")

    def test_stacked_bar(self):
        self.assertEqual(_detect_chart_type("堆叠柱状图"), "stacked_bar")

    def test_grouped_bar(self):
        self.assertEqual(_detect_chart_type("分组柱状图"), "grouped_bar")

    def test_horizontal_bar(self):
        self.assertEqual(_detect_chart_type("条形图"), "horizontal_bar")

    def test_combo_bar_line(self):
        self.assertEqual(_detect_chart_type("组合图展示"), "combo_bar_line")


class TestDetectChartTypeEnglish(unittest.TestCase):
    def test_bar_chart(self):
        self.assertEqual(_detect_chart_type("bar chart of revenue"), "bar")

    def test_line_chart(self):
        self.assertEqual(_detect_chart_type("line chart showing trend"), "line")

    def test_pie_chart(self):
        self.assertEqual(_detect_chart_type("pie chart of market share"), "pie")

    def test_donut_chart(self):
        self.assertEqual(_detect_chart_type("donut chart breakdown"), "donut")

    def test_scatter_plot(self):
        self.assertEqual(_detect_chart_type("scatter plot of correlation"), "scatter")

    def test_scatter(self):
        self.assertEqual(_detect_chart_type("scatter of x vs y"), "scatter")

    def test_stacked_bar(self):
        self.assertEqual(_detect_chart_type("stacked bar comparison"), "stacked_bar")

    def test_grouped_bar(self):
        self.assertEqual(_detect_chart_type("grouped bar by region"), "grouped_bar")

    def test_clustered_bar(self):
        self.assertEqual(_detect_chart_type("clustered bar by quarter"), "grouped_bar")

    def test_horizontal_bar(self):
        self.assertEqual(_detect_chart_type("horizontal bar ranking"), "horizontal_bar")

    def test_combo_chart(self):
        self.assertEqual(_detect_chart_type("combo chart revenue and margin"), "combo_bar_line")

    def test_combo_bar_line(self):
        self.assertEqual(_detect_chart_type("combo bar line chart"), "combo_bar_line")

    def test_bar_and_line(self):
        self.assertEqual(_detect_chart_type("bar and line mixed"), "combo_bar_line")


class TestDetectChartTypeError(unittest.TestCase):
    def test_no_keyword_raises(self):
        with self.assertRaises(PromptParseError) as ctx:
            _detect_chart_type("show me the data")
        self.assertIn("bar chart", str(ctx.exception))
        self.assertIn("scatter plot", str(ctx.exception))

    def test_error_mentions_english_and_chinese(self):
        with self.assertRaises(PromptParseError) as ctx:
            _detect_chart_type("something totally unrelated")
        msg = str(ctx.exception)
        self.assertIn("bar chart", msg)
        self.assertIn("柱状图", msg)


class TestParseAssignments(unittest.TestCase):
    def test_basic_x_y(self):
        result = _parse_assignments("bar chart, x=Year, y=Revenue")
        self.assertEqual(result["x"], "Year")
        self.assertEqual(result["y"], "Revenue")

    def test_chinese_equals(self):
        result = _parse_assignments("柱状图，x=年份，y=收入")
        self.assertEqual(result["x"], "年份")
        self.assertEqual(result["y"], "收入")

    def test_colon_separator(self):
        result = _parse_assignments("line chart, x:Month, y:Sales")
        self.assertEqual(result["x"], "Month")
        self.assertEqual(result["y"], "Sales")

    def test_title(self):
        result = _parse_assignments("bar chart, title=Revenue Growth, x=Year, y=Revenue")
        self.assertEqual(result["title"], "Revenue Growth")

    def test_multiple_y(self):
        result = _parse_assignments("grouped bar, x=Region, y=Sales,Profit,Cost")
        self.assertIsInstance(result["y"], list)
        self.assertEqual(result["y"], ["Sales", "Profit", "Cost"])


class TestParseFormats(unittest.TestCase):
    def test_default(self):
        self.assertEqual(parse_formats(None), ["svg", "png"])

    def test_single(self):
        self.assertEqual(parse_formats("png"), ["png"])

    def test_multiple(self):
        self.assertEqual(parse_formats("svg,png"), ["svg", "png"])

    def test_invalid(self):
        with self.assertRaises(PromptParseError):
            parse_formats("pdf")

    def test_dot_prefix(self):
        self.assertEqual(parse_formats(".svg,.png"), ["svg", "png"])


class TestParsePromptFull(unittest.TestCase):
    def test_english_bar_prompt(self):
        spec = parse_prompt("bar chart, x=Year, y=Revenue, title=Annual Revenue")
        self.assertEqual(spec["chart_type"], "bar")
        self.assertEqual(spec["x"], "Year")
        self.assertEqual(spec["y"], "Revenue")
        self.assertEqual(spec["title"], "Annual Revenue")

    def test_english_line_prompt(self):
        spec = parse_prompt("line chart of growth, x=Month, y=Growth")
        self.assertEqual(spec["chart_type"], "line")
        self.assertEqual(spec["x"], "Month")
        self.assertEqual(spec["y"], "Growth")

    def test_english_scatter_prompt(self):
        spec = parse_prompt("scatter plot, x=Height, y=Weight")
        self.assertEqual(spec["chart_type"], "scatter")
        self.assertEqual(spec["x"], "Height")
        self.assertEqual(spec["y"], "Weight")

    def test_chinese_bar_prompt(self):
        spec = parse_prompt("柱状图，x=年份，y=收入，标题=年度收入")
        self.assertEqual(spec["chart_type"], "bar")
        self.assertEqual(spec["x"], "年份")
        self.assertEqual(spec["y"], "收入")

    def test_empty_prompt_raises(self):
        with self.assertRaises(PromptParseError):
            parse_prompt("")

    def test_whitespace_prompt_raises(self):
        with self.assertRaises(PromptParseError):
            parse_prompt("   ")

    def test_output_name_from_prompt(self):
        spec = parse_prompt("bar chart, x=Year, y=Revenue, title=Sales")
        self.assertIn("output_name", spec)
        self.assertTrue(spec["output_name"])


if __name__ == "__main__":
    unittest.main()
