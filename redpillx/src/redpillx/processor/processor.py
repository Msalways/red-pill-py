"""Data processor combining flattener and profiler."""

from typing import Any

from redpillx.processor.flattener import DataFlattener
from redpillx.processor.profiler import DataProfiler


class DataProcessor:
    """Combines flattening and profiling for data preparation."""

    def __init__(self) -> None:
        self.flattener = DataFlattener()
        self.profiler = DataProfiler()

    def process(
        self, data: Any, sample_size: int = 100
    ) -> dict[str, Any]:
        """Process raw data into flat sample + profile.

        Args:
            data: Raw JSON data (dict, list, or nested)
            sample_size: Number of rows to sample for LLM

        Returns:
            Dictionary with flat_data and profile
        """
        if isinstance(data, str):
            import json
            data = json.loads(data)

        flat_data = self.flattener.process(data, sample_size)
        profile = self.profiler.profile(flat_data)

        time_fields = self.profiler.infer_time_fields(profile)
        categorical_fields = self.profiler.infer_categorical_fields(profile)

        profile["inferred"] = {
            "time_fields": time_fields,
            "categorical_fields": categorical_fields,
        }

        return {
            "flat_data": flat_data,
            "profile": profile,
        }
