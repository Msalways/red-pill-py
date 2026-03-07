"""Polars-based executor for chart data transformation."""

import json
import re
import sys
from datetime import datetime, timedelta
from typing import Any, AsyncIterator

import polars as pl

from redpillx.spec.schema import (
    ChartSpec,
    ChartDataResult,
    FilterOperator,
    AggregationType,
    TimeRangeUnit,
    SortDirection,
    ChartType,
)
from redpillx.processor.flattener import DataFlattener
from redpillx.processor.normalizer import normalize_data, DataNormalizer


DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%Y%m%d",
]


class PolarsExecutor:
    """Executes chart spec transformations using Polars."""

    def __init__(self) -> None:
        self._flattener = DataFlattener()
        self._normalizer = DataNormalizer()
        self._field_metadata: dict[str, Any] = {}

    def execute(
        self,
        spec: ChartSpec,
        data: Any,
    ) -> ChartDataResult:
        """Execute the spec on data to produce chart-ready output.

        Args:
            spec: Chart specification with params
            data: Raw data (dict, list, or JSON string)

        Returns:
            ChartDataResult with transformed data
        """
        df = self._load_data(data)
        
        # Normalize data types (handle currency strings, string numbers, etc.)
        df = self._normalize_dataframe(df)
        
        original_count = len(df)
        
        df = self._apply_filters(df, spec.params)
        
        df = self._apply_time_filter(df, spec.params)
        
        df = self._apply_grouping(df, spec)

        if spec.params.sort:
            df = self._apply_sort(df, spec.params.sort, spec)

        if spec.params.limit:
            df = df.head(spec.params.limit)

        result_data = self._to_chart_format(df, spec)

        warnings = []
        if original_count > 0 and len(result_data) == 0:
            warnings.append("Filter resulted in empty dataset")
        if len(result_data) < 3 and spec.chart_type.value == "line":
            warnings.append("Line chart with less than 3 data points may not be meaningful")

        return ChartDataResult(
            data=result_data,
            metadata={
                "chartType": spec.chart_type,
                "xAxis": {"field": spec.x_axis.field, "label": spec.x_axis.label or spec.x_axis.field},
                "yAxis": {
                    "field": spec.y_axis.field, 
                    "label": self._format_label(spec.y_axis.field, spec.y_axis.label or spec.y_axis.field)
                },
                "series": (
                    {"field": spec.series.field, "label": spec.series.label or spec.series.field}
                    if spec.series
                    else None
                ),
                "warnings": warnings if warnings else None,
                "originalCount": original_count,
                "filteredCount": len(df) if len(df) > 0 else 0,
                "currency": self._field_metadata.get("currency", {}),
            },
        )

    def _load_data(self, data: Any) -> pl.DataFrame:
        """Load data into Polars DataFrame, flattening if needed."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return pl.DataFrame()

        if isinstance(data, dict):
            flat_data = self._flattener.process(data, sample_size=999999999)
            if flat_data:
                return pl.DataFrame(flat_data)
            for key, value in data.items():
                if isinstance(value, list):
                    flat_items = []
                    for item in value:
                        flat = self._flattener.flatten(item, key)
                        if flat:
                            flat_items.append(flat)
                    if flat_items:
                        return pl.DataFrame(flat_items)

        if isinstance(data, list):
            flat_data = []
            for idx, item in enumerate(data):
                flat = self._flattener.flatten(item, "", idx)
                if flat:
                    flat_data.append(flat)
            if flat_data:
                return pl.DataFrame(flat_data)
            return pl.DataFrame(data)

        return pl.DataFrame()

    def _normalize_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalize data types in DataFrame.
        
        Handles:
        - Currency strings (e.g., "$1,000" -> 1000.0)
        - String numbers (e.g., "123" -> 123)
        - Various date formats
        """
        if df.is_empty():
            return df
        
        # Convert to dict for normalizer, then back
        records = df.to_dicts()
        normalized_records, field_metadata = normalize_data(records)
        self._field_metadata = field_metadata
        
        return pl.DataFrame(normalized_records)

    def _format_label(self, field: str, default_label: str | None) -> str:
        """Format label with currency marker if detected."""
        if default_label is None:
            default_label = field
        if field in self._field_metadata.get("currency", {}):
            return f"{default_label} (Currency)"
        return default_label

    def _apply_filters(self, df: pl.DataFrame, params: Any) -> pl.DataFrame:
        """Apply filters from params with case-insensitive string matching."""
        if not params.filters:
            return df

        for filter_def in params.filters:
            field = filter_def.field
            operator = filter_def.operator
            value = filter_def.value

            resolved_field = self._resolve_field(df, field)
            if not resolved_field:
                continue

            col_dtype = df.schema[resolved_field] if resolved_field in df.columns else None
            
            try:
                if operator == FilterOperator.EQ:
                    if col_dtype == pl.Utf8 and isinstance(value, str):
                        df = df.filter(pl.col(resolved_field).str.to_lowercase() == value.lower())
                    else:
                        df = df.filter(pl.col(resolved_field) == value)
                        
                elif operator == FilterOperator.NE:
                    if col_dtype == pl.Utf8 and isinstance(value, str):
                        df = df.filter(pl.col(resolved_field).str.to_lowercase() != value.lower())
                    else:
                        df = df.filter(pl.col(resolved_field) != value)
                        
                elif operator == FilterOperator.GT:
                    df = df.filter(pl.col(resolved_field) > value)
                elif operator == FilterOperator.GTE:
                    df = df.filter(pl.col(resolved_field) >= value)
                elif operator == FilterOperator.LT:
                    df = df.filter(pl.col(resolved_field) < value)
                elif operator == FilterOperator.LTE:
                    df = df.filter(pl.col(resolved_field) <= value)
                    
                elif operator == FilterOperator.IN:
                    if isinstance(value, list):
                        if col_dtype == pl.Utf8:
                            value_lower = [v.lower() if isinstance(v, str) else v for v in value]
                            df = df.filter(pl.col(resolved_field).str.to_lowercase().is_in(value_lower))
                        else:
                            df = df.filter(pl.col(resolved_field).is_in(value))
                            
                elif operator == FilterOperator.NOT_IN:
                    if isinstance(value, list):
                        if col_dtype == pl.Utf8:
                            value_lower = [v.lower() if isinstance(v, str) else v for v in value]
                            df = df.filter(~pl.col(resolved_field).str.to_lowercase().is_in(value_lower))
                        else:
                            df = df.filter(~pl.col(resolved_field).is_in(value))
                            
                elif operator == FilterOperator.CONTAINS:
                    if isinstance(value, str):
                        df = df.filter(pl.col(resolved_field).cast(str).str.to_lowercase().str.contains(value.lower()))
                        
            except Exception:
                continue

        return df

    def _apply_time_filter(self, df: pl.DataFrame, params: Any) -> pl.DataFrame:
        """Apply time range filter with multiple format support."""
        if not params.time_field or not params.time_range:
            return df

        time_field = params.time_field
        time_range = params.time_range

        resolved_field = self._resolve_field(df, time_field)
        if not resolved_field:
            return df

        time_col_parsed = None
        for fmt in DATE_FORMATS:
            try:
                time_col_parsed = pl.col(resolved_field).str.to_datetime(format=fmt, strict=False)
                break
            except Exception:
                continue
        
        if time_col_parsed is None:
            return df
        
        try:
            if time_range.type == "relative" and time_range.value and time_range.unit:
                now = datetime.now()

                if time_range.unit == TimeRangeUnit.MINUTES:
                    delta = timedelta(minutes=time_range.value)
                elif time_range.unit == TimeRangeUnit.HOURS:
                    delta = timedelta(hours=time_range.value)
                elif time_range.unit == TimeRangeUnit.DAYS:
                    delta = timedelta(days=time_range.value)
                elif time_range.unit == TimeRangeUnit.WEEKS:
                    delta = timedelta(weeks=time_range.value)
                elif time_range.unit == TimeRangeUnit.MONTHS:
                    delta = timedelta(days=time_range.value * 30)
                elif time_range.unit == TimeRangeUnit.YEARS:
                    delta = timedelta(days=time_range.value * 365)
                else:
                    return df

                cutoff = now - delta
                df_filtered = df.filter(time_col_parsed >= cutoff)
                if df_filtered.height == 0 and df.height > 0:
                    import logging
                    logging.warning(f"Time filter returned empty - time_field: {time_field}, cutoff: {cutoff}")
                    return df
                df = df_filtered

            elif time_range.type == "absolute":
                if time_range.start:
                    try:
                        start_dt = datetime.fromisoformat(time_range.start.replace(" ", "T"))
                        df = df.filter(time_col_parsed >= start_dt)
                    except Exception:
                        pass
                if time_range.end:
                    try:
                        end_dt = datetime.fromisoformat(time_range.end.replace(" ", "T"))
                        df = df.filter(time_col_parsed <= end_dt)
                    except Exception:
                        pass
        except Exception:
            pass

        return df

    def _resolve_field(self, df: pl.DataFrame, field: str) -> str | None:
        """Resolve field name - try exact match first, then try without prefix."""
        if field in df.columns:
            return field
        if "." in field:
            simple = field.split(".")[-1]
            if simple in df.columns:
                return simple
        return None

    def _apply_grouping(self, df: pl.DataFrame, spec: ChartSpec) -> pl.DataFrame:
        """Apply grouping and aggregation."""
        x_field = self._resolve_field(df, spec.x_axis.field) or spec.x_axis.field
        y_field = spec.y_axis.field
        y_agg = spec.y_axis.aggregation or AggregationType.COUNT
        
        series_field = None
        if spec.series:
            series_field = self._resolve_field(df, spec.series.field) or spec.series.field

        group_by_cols = [x_field]
        if series_field and series_field in df.columns:
            group_by_cols.append(series_field)

        available_cols = [c for c in group_by_cols if c in df.columns]

        if not available_cols:
            return df

        resolved_y_field = y_field
        if y_field and y_field != "count":
            resolved_y_field = self._resolve_field(df, y_field) or y_field
            if resolved_y_field and resolved_y_field in df.columns:
                agg_expr = self._get_aggregation_expr(resolved_y_field, y_agg, df)
            else:
                agg_expr = self._get_aggregation_expr("count", AggregationType.COUNT, df)
        else:
            agg_expr = self._get_aggregation_expr("count", AggregationType.COUNT, df)

        df = df.group_by(available_cols).agg(agg_expr)

        new_columns = list(available_cols)
        resolved_y = self._resolve_field(df, resolved_y_field) if resolved_y_field else None
        
        if y_agg == AggregationType.COUNT:
            if "count" not in new_columns:
                new_columns.append("count")
        elif resolved_y and resolved_y != "count" and resolved_y not in new_columns:
            new_columns.append(resolved_y)

        if series_field and series_field not in new_columns:
            new_columns.append(series_field)

        return df.select(new_columns)

    def _get_aggregation_expr(
        self, field: str, aggregation: AggregationType, df: pl.DataFrame
    ) -> pl.Expr:
        """Get aggregation expression."""
        if aggregation == AggregationType.COUNT:
            return pl.len().alias("count")
        elif aggregation == AggregationType.SUM:
            return pl.col(field).sum().alias(field)
        elif aggregation == AggregationType.AVG:
            return pl.col(field).mean().alias(field)
        elif aggregation == AggregationType.MIN:
            return pl.col(field).min().alias(field)
        elif aggregation == AggregationType.MAX:
            return pl.col(field).max().alias(field)
        else:
            return pl.len().alias("count")

    def _apply_sort(self, df: pl.DataFrame, sort_config: Any, spec: ChartSpec) -> pl.DataFrame:
        """Apply sorting."""
        field = sort_config.field
        direction = sort_config.direction

        if field == "y" and spec.y_axis.aggregation == AggregationType.COUNT:
            field = "count"
        elif field == "x":
            field = spec.x_axis.field

        if field not in df.columns:
            return df

        if direction == SortDirection.ASC:
            return df.sort(field)
        else:
            return df.sort(field, descending=True)

    def _to_chart_format(self, df: pl.DataFrame, spec: ChartSpec) -> list[dict]:
        """Convert Polars DataFrame to chart-ready format."""
        records = df.to_dicts()
        
        x_field = self._resolve_field(df, spec.x_axis.field) or spec.x_axis.field
        y_field = spec.y_axis.field
        series_field = self._resolve_field(df, spec.series.field) if spec.series else None

        result = []
        for record in records:
            new_record: dict[str, Any] = {}

            new_record["x"] = record.get(x_field)
            new_record["label_x"] = spec.x_axis.label

            if spec.y_axis.aggregation == AggregationType.COUNT:
                new_record["y"] = record.get("count", 0)
            else:
                y_value = record.get(y_field, 0)
                # Round avg to 2 decimal places
                if spec.y_axis.aggregation == AggregationType.AVG:
                    y_value = round(y_value, 2) if y_value else 0
                new_record["y"] = y_value
            new_record["label_y"] = spec.y_axis.label

            if spec.series and series_field:
                new_record["series"] = record.get(series_field)
                new_record["label_series"] = spec.series.label

            result.append(new_record)

        return result


class AsyncPolarsExecutor(PolarsExecutor):
    """Async variant of Polars executor for large datasets."""

    async def execute_stream(
        self,
        spec: ChartSpec,
        data: Any,
        batch_size: int = 10000,
    ) -> AsyncIterator[list[dict]]:
        """Execute spec on data in streaming batches.

        Args:
            spec: Chart specification
            data: Raw data
            batch_size: Number of rows per batch

        Yields:
            Batches of chart-ready data
        """
        df = self._load_data(data)
        total_rows = len(df)

        df = self._apply_filters(df, spec.params)
        df = self._apply_time_filter(df, spec.params)

        df = self._apply_grouping(df, spec)

        if spec.params.sort:
            df = self._apply_sort(df, spec.params.sort, spec)

        result_data = self._to_chart_format(df, spec)

        for i in range(0, len(result_data), batch_size):
            yield result_data[i : i + batch_size]
