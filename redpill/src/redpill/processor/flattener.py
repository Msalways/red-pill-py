"""Data flattener for nested JSON structures."""

from typing import Any


class DataFlattener:
    """Flattens nested JSON data into flat records with dot-notation keys."""

    def flatten(self, data: Any, prefix: str = "", max_depth: int = 10) -> dict | None:
        """Flatten a single record.

        Args:
            data: The data to flatten
            prefix: Key prefix for nested fields
            max_depth: Maximum nesting depth

        Returns:
            Flattened dictionary or None if data is null/empty
        """
        if data is None:
            return None

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict) and max_depth > 0:
                    nested = self.flatten(value, new_key, max_depth - 1)
                    if nested:
                        result.update(nested)
                elif isinstance(value, list):
                    continue
                else:
                    result[new_key] = value
            return result

        if isinstance(data, list):
            return None

        return {prefix: data} if prefix else data

    def flatten_array_item(
        self, item: Any, prefix: str = "", row_index: int = 0, max_depth: int = 10
    ) -> dict | None:
        """Flatten a single item from an array.

        Args:
            item: The array item to flatten
            prefix: Key prefix
            row_index: Index in the original array
            max_depth: Maximum nesting depth

        Returns:
            Flattened dictionary with _row_index
        """
        flat = self.flatten(item, prefix, max_depth)
        if flat is None:
            return None

        flat["_row_index"] = row_index

        exploded_items = []
        flat, arrays = self._extract_arrays(flat, prefix)

        for array_key, array_items in arrays.items():
            for idx, arr_item in enumerate(array_items):
                exploded = flat.copy()
                if isinstance(arr_item, dict):
                    arr_flat = self.flatten(arr_item, array_key, max_depth - 1)
                    if arr_flat:
                        exploded.update(arr_flat)
                else:
                    exploded[array_key] = arr_item
                exploded["_array_index"] = idx
                exploded_items.append(exploded)

        if exploded_items:
            return exploded_items

        return flat

    def _extract_arrays(
        self, data: dict, prefix: str
    ) -> tuple[dict, dict[str, list]]:
        """Extract arrays from flattened data."""
        arrays = {}
        clean_data = {}

        for key, value in data.items():
            if isinstance(value, list):
                if value and isinstance(value[0], (dict, list)):
                    arrays[key] = value
                else:
                    clean_data[key] = ",".join(str(v) for v in value) if value else None
            else:
                clean_data[key] = value

        return clean_data, arrays

    def process(
        self, data: Any, sample_size: int = 100
    ) -> list[dict[str, Any]]:
        """Process the entire data structure.

        Args:
            data: Raw JSON data (dict, list, or nested)
            sample_size: Maximum number of sample rows to return

        Returns:
            List of flattened records
        """
        if isinstance(data, dict):
            records = []
            for key, value in data.items():
                if isinstance(value, list):
                    for idx, item in enumerate(value[:sample_size]):
                        flat = self.flatten_array_item(item, key, idx)
                        if flat:
                            records.append(flat)
                else:
                    flat = self.flatten({key: value})
                    if flat:
                        records.append(flat)
            return records[:sample_size]

        if isinstance(data, list):
            records = []
            for idx, item in enumerate(data[:sample_size]):
                flat = self.flatten_array_item(item, "", idx)
                if flat:
                    if isinstance(flat, list):
                        records.extend(flat)
                    else:
                        records.append(flat)
            return records[:sample_size]

        return []
