"""Data profiler for generating column statistics."""

from datetime import datetime
from typing import Any

import polars as pl


class DataProfiler:
    """Generates profile information from flattened data for LLM analysis."""

    def profile(self, flat_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a profile of the flattened data.

        Args:
            flat_data: List of flattened records

        Returns:
            Dictionary containing column profiles and statistics
        """
        if not flat_data:
            return {
                "columns": {},
                "row_count": 0,
                "flattened_row_count": 0,
            }

        df = pl.DataFrame(flat_data)

        columns = {}
        for col_name in df.columns:
            col = df[col_name]
            dtype = col.dtype

            col_info: dict[str, Any] = {
                "type": str(dtype),
                "null_count": col.null_count(),
                "unique_count": col.n_unique(),
            }

            if col.null_count() < len(col):
                if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float64]:
                    col_info["min"] = col.min()
                    col_info["max"] = col.max()
                    col_info["mean"] = col.mean()
                elif dtype == pl.Utf8:
                    col_info["sample_values"] = col.unique().head(10).to_list()

            columns[col_name] = col_info

        return {
            "columns": columns,
            "row_count": len(df),
            "flattened_row_count": len(df),
            "column_count": len(df.columns),
        }

    def infer_time_fields(self, profile: dict[str, Any]) -> list[str]:
        """Infer which fields are likely time-based.

        Args:
            profile: Data profile from profile()

        Returns:
            List of field names that appear to be timestamps
        """
        time_fields = []
        for col_name, col_info in profile.get("columns", {}).items():
            col_type = col_info.get("type", "")
            samples = col_info.get("sample_values", [])

            if "date" in col_name.lower() or "time" in col_name.lower():
                time_fields.append(col_name)
            elif "timestamp" in col_type.lower():
                time_fields.append(col_name)
            elif samples:
                try:
                    for sample in samples[:3]:
                        if sample:
                            datetime.fromisoformat(str(sample))
                    time_fields.append(col_name)
                except (ValueError, TypeError):
                    pass

        return time_fields

    def infer_categorical_fields(self, profile: dict[str, Any]) -> list[str]:
        """Infer which fields are categorical (low unique count).

        Args:
            profile: Data profile from profile()

        Returns:
            List of field names that appear to be categorical
        """
        categorical = []
        total_rows = profile.get("row_count", 1)

        for col_name, col_info in profile.get("columns", {}).items():
            unique = col_info.get("unique_count", 0)
            if unique > 0 and unique <= 50:
                ratio = unique / total_rows
                if ratio < 0.5:
                    categorical.append(col_name)

        return categorical
