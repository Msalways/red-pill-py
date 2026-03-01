"""Smoke tests for Redpill Python SDK — no LLM required."""

import pytest
from redpill.processor.flattener import DataFlattener
from redpill.processor.normalizer import DataNormalizer, normalize_data
from redpill.spec.schema import (
    ChartSpec, AxisConfig, AggregationType, ChartType, SortConfig,
    SortDirection, RuntimeParams, Filter, FilterOperator,
)
from redpill.executor.polars_executor import PolarsExecutor
from redpill.client import Redpill


# ─── DataFlattener ────────────────────────────────────────────────────────────

class TestDataFlattener:
    def setup_method(self):
        self.f = DataFlattener()

    def test_flatten_nested_dict(self):
        result = self.f.flatten({"user": {"name": "Alice", "city": "NY"}, "score": 10})
        assert result == {"user.name": "Alice", "user.city": "NY", "score": 10}

    def test_flatten_returns_none_for_null(self):
        assert self.f.flatten(None) is None

    def test_process_array_of_dicts(self):
        records = self.f.process([{"a": 1, "b": {"c": 2}}, {"a": 3, "b": {"c": 4}}])
        assert len(records) == 2
        assert records[0] == {"a": 1, "b.c": 2}
        assert records[1] == {"a": 3, "b.c": 4}

    def test_process_wrapped_object(self):
        records = self.f.process({"tickets": [{"id": 1, "status": "open"}]})
        assert len(records) == 1
        assert records[0]["id"] == 1
        assert records[0]["status"] == "open"

    def test_process_empty_list(self):
        assert self.f.process([]) == []

    def test_deeply_nested_keys(self):
        result = self.f.flatten({"a": {"b": {"c": "deep"}}})
        assert result == {"a.b.c": "deep"}


# ─── DataNormalizer ───────────────────────────────────────────────────────────

class TestDataNormalizer:
    def setup_method(self):
        self.n = DataNormalizer()

    def test_detects_currency_symbols(self):
        result = self.n.detect_currency(["$1,200", "$500", "$300"])
        assert result == "currency"

    def test_no_currency_for_plain_numbers(self):
        result = self.n.detect_currency([100, 200, 300])
        assert result is None

    def test_parse_number_from_currency_string(self):
        assert self.n.parse_number("$1,200") == 1200.0

    def test_parse_number_from_plain_string(self):
        assert self.n.parse_number("1234.56") == pytest.approx(1234.56)

    def test_parse_number_returns_none_for_text(self):
        assert self.n.parse_number("hello") is None

    def test_infer_field_type_number(self):
        assert self.n.infer_field_type([1, 2, 3, 4, 5]) == "number"

    def test_infer_field_type_string(self):
        assert self.n.infer_field_type(["open", "closed", "pending"]) == "string"

    def test_normalize_data_converts_currency_strings(self):
        records = [{"status": "open", "amount": "$1,200"}, {"status": "closed", "amount": "$500"}]
        normalized, metadata = normalize_data(records)
        assert normalized[0]["amount"] == 1200.0
        assert "amount" in metadata.get("currency", {})


# ─── ChartSpec (Pydantic) ─────────────────────────────────────────────────────

class TestChartSpec:
    def test_minimal_valid_spec(self):
        spec = ChartSpec(
            chartType="bar",
            xAxis=AxisConfig(field="status"),
            yAxis=AxisConfig(field="count", aggregation=AggregationType.COUNT),
        )
        assert spec.chart_type == ChartType.BAR
        assert spec.x_axis.field == "status"

    def test_invalid_chart_type_raises(self):
        with pytest.raises(Exception):
            ChartSpec(
                chartType="unknown_type",  # type: ignore
                xAxis=AxisConfig(field="a"),
                yAxis=AxisConfig(field="b"),
            )

    def test_all_chart_types_valid(self):
        for chart_type in ChartType:
            spec = ChartSpec(
                chartType=chart_type.value,
                xAxis=AxisConfig(field="x"),
                yAxis=AxisConfig(field="y"),
            )
            assert spec.chart_type == chart_type

    def test_spec_from_dict_camelCase_aliases(self):
        spec = ChartSpec(**{
            "chartType": "line",
            "xAxis": {"field": "date"},
            "yAxis": {"field": "amount", "aggregation": "sum"},
        })
        assert spec.chart_type == ChartType.LINE

    def test_filter_in_params(self):
        spec = ChartSpec(
            chartType="bar",
            xAxis=AxisConfig(field="status"),
            yAxis=AxisConfig(field="status", aggregation=AggregationType.COUNT),
            params=RuntimeParams(
                filters=[Filter(field="priority", operator=FilterOperator.EQ, value="high")]
            ),
        )
        assert spec.params.filters[0].operator == FilterOperator.EQ


# ─── PolarsExecutor ───────────────────────────────────────────────────────────

class TestPolarsExecutor:
    def setup_method(self):
        self.executor = PolarsExecutor()
        self.data = [
            {"status": "open",    "priority": "high",   "amount": 100},
            {"status": "open",    "priority": "low",    "amount": 200},
            {"status": "closed",  "priority": "high",   "amount": 300},
            {"status": "closed",  "priority": "low",    "amount": 400},
            {"status": "pending", "priority": "high",   "amount": 150},
        ]

    def _spec(self, **kwargs) -> ChartSpec:
        defaults = dict(
            chartType="bar",
            xAxis=AxisConfig(field="status"),
            yAxis=AxisConfig(field="status", aggregation=AggregationType.COUNT),
        )
        defaults.update(kwargs)
        return ChartSpec(**defaults)

    def test_count_by_status(self):
        result = self.executor.execute(spec=self._spec(), data=self.data)
        assert len(result.data) == 3
        open_row = next(d for d in result.data if d["x"] == "open")
        assert open_row["y"] == 2

    def test_sum_amount_by_status(self):
        spec = self._spec(yAxis=AxisConfig(field="amount", aggregation=AggregationType.SUM))
        result = self.executor.execute(spec=spec, data=self.data)
        closed = next(d for d in result.data if d["x"] == "closed")
        assert closed["y"] == 700

    def test_eq_filter(self):
        spec = self._spec(
            params=RuntimeParams(
                filters=[Filter(field="priority", operator=FilterOperator.EQ, value="high")]
            )
        )
        result = self.executor.execute(spec=spec, data=self.data)
        total = sum(d["y"] for d in result.data)
        assert total == 3  # 3 high-priority records

    def test_limit(self):
        spec = self._spec(params=RuntimeParams(limit=2))
        result = self.executor.execute(spec=spec, data=self.data)
        assert len(result.data) == 2

    def test_sort_desc(self):
        spec = self._spec(
            params=RuntimeParams(sort=SortConfig(field="y", direction=SortDirection.DESC))
        )
        result = self.executor.execute(spec=spec, data=self.data)
        ys = [d["y"] for d in result.data]
        assert ys == sorted(ys, reverse=True)

    def test_wrapped_object_input(self):
        result = self.executor.execute(spec=self._spec(), data={"tickets": self.data})
        assert len(result.data) > 0

    def test_json_string_input(self):
        import json
        result = self.executor.execute(spec=self._spec(), data=json.dumps(self.data))
        assert len(result.data) > 0

    def test_empty_data_returns_empty_result(self):
        result = self.executor.execute(spec=self._spec(), data=[])
        assert result.data == []

    def test_series_grouping(self):
        spec = ChartSpec(
            chartType="bar",
            xAxis=AxisConfig(field="status"),
            yAxis=AxisConfig(field="status", aggregation=AggregationType.COUNT),
            series={"field": "priority"},
        )
        result = self.executor.execute(spec=spec, data=self.data)
        assert len(result.data) == 5
        assert "series" in result.data[0]

    def test_metadata_chart_type(self):
        result = self.executor.execute(spec=self._spec(chartType="line"), data=self.data)
        assert result.metadata["chartType"].value == "line"

    def test_not_in_filter(self):
        spec = self._spec(
            params=RuntimeParams(
                filters=[Filter(field="priority", operator=FilterOperator.NOT_IN, value=["low"])]
            )
        )
        result = self.executor.execute(spec=spec, data=self.data)
        total = sum(d["y"] for d in result.data)
        assert total == 3  # only high-priority records


# ─── Redpill client ───────────────────────────────────────────────────────────

class TestRedpillClient:
    def test_build_raises_without_llm(self):
        with pytest.raises(ValueError, match="llm"):
            Redpill().build()

    def test_build_succeeds_with_llm(self):
        rp = Redpill().llm(lambda msgs, opts=None: {"content": "{}"}).build()
        assert rp is not None

    def test_method_chaining(self):
        dummy = lambda msgs, opts=None: {"content": "{}"}
        rp = (
            Redpill()
            .llm(dummy)
            .temperature(0.3)
            .max_tokens(1000)
            .sample_size(20)
            .debug_mode(True)
            .build()
        )
        assert rp._config.temperature == 0.3  # type: ignore[attr-defined]
        assert rp._config.max_tokens == 1000   # type: ignore[attr-defined]
        assert rp._config.sample_size == 20    # type: ignore[attr-defined]
        assert rp._config.debug_mode is True   # type: ignore[attr-defined]

    def test_execute_without_llm_call(self):
        """execute() never calls the LLM — it should work with a dummy callable."""
        dummy = lambda msgs, opts=None: {"content": "{}"}
        rp = Redpill().llm(dummy).build()
        result = rp.execute(
            spec={
                "chartType": "bar",
                "xAxis": {"field": "status"},
                "yAxis": {"field": "status", "aggregation": "count"},
            },
            data=[{"status": "open"}, {"status": "closed"}],
        )
        assert len(result.data) == 2
