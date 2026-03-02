"""Data normalizer for handling messy real-world data types."""

import re
from datetime import datetime
from typing import Any


class DataNormalizer:
    """Normalizes messy data types for consistent processing."""

    CURRENCY_SYMBOLS = ['$', '€', '£', '¥', '₹', '₽', '₩', 'R$', 'A$', 'C$']
    CURRENCY_PATTERN = re.compile(r'^[' + re.escape(''.join(CURRENCY_SYMBOLS)) + r']?\s*[\d,]+\.?\d*$')
    
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%d %b %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%B %d, %Y',
    ]

    def is_numeric_string(self, value: str) -> bool:
        """Check if string looks like a number (possibly with currency symbol)."""
        if not isinstance(value, str):
            return False
        cleaned = self._clean_numeric_string(value)
        if cleaned:
            try:
                float(cleaned)
                return True
            except ValueError:
                return False
        return False

    def _clean_numeric_string(self, value: str) -> str | None:
        """Remove currency symbols, commas, spaces from numeric string."""
        if not isinstance(value, str):
            return None
        
        # Remove currency symbols and spaces
        for symbol in self.CURRENCY_SYMBOLS:
            value = value.replace(symbol, '')
        
        # Remove commas used as thousand separators
        value = value.replace(',', '')
        
        # Remove extra whitespace
        value = value.strip()
        
        if not value:
            return None
            
        return value

    def parse_number(self, value: Any) -> float | None:
        """Parse a value to number, handling various formats."""
        if value is None:
            return None
            
        # Already a number
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            cleaned = self._clean_numeric_string(value)
            if cleaned:
                try:
                    return float(cleaned)
                except ValueError:
                    pass
        
        return None

    def parse_date(self, value: Any) -> datetime | None:
        """Parse a value to datetime, trying multiple formats."""
        if value is None:
            return None
            
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            
            # Try ISO format first
            if 'T' in value or 'Z' in value:
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            # Try other formats
            for fmt in self.DATE_FORMATS:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        return None

    def infer_field_type(self, values: list[Any]) -> str:
        """Infer the type of a field based on its values."""
        non_null = [v for v in values if v is not None]
        
        if not non_null:
            return 'unknown'
        
        # Check for dates
        date_count = 0
        for v in non_null[:10]:  # Sample first 10
            if self.parse_date(v):
                date_count += 1
        
        if date_count >= len(non_null[:10]) * 0.8:
            return 'date'
        
        # Check for numbers
        num_count = 0
        for v in non_null[:10]:
            if self.parse_number(v):
                num_count += 1
        
        if num_count >= len(non_null[:10]) * 0.8:
            return 'number'
        
        return 'string'

    def detect_currency(self, values: list[Any]) -> str | None:
        """Detect if a field has currency/numeric string patterns.
        
        Returns a generic "currency" marker - frontend can format based on locale.
        Only detects if there's an explicit currency symbol or code.
        """
        return self.detect_currency_field(values)

    def detect_currency_field(self, values: list[Any]) -> str | None:
        """Detect if a field has currency/numeric string patterns.
        
        Returns a generic "currency" marker - frontend can format based on locale.
        Only detects if there's an explicit currency symbol or code.
        """
        # Currency symbols that definitely indicate currency
        CURRENCY_SYMBOLS = ['$', '€', '£', '¥', '₹', '₽', '₩']
        
        currency_count = 0
        checked = 0
        
        for v in values[:30]:
            if isinstance(v, str) and v.strip():
                checked += 1
                # Check for currency symbols at start or end
                v_stripped = v.strip()
                if any(v_stripped.startswith(c) or v_stripped.endswith(c) for c in CURRENCY_SYMBOLS):
                    currency_count += 1
                # Check for 3-letter currency codes
                import re
                if re.search(r'\\b(USD|EUR|GBP|JPY|CNY|INR|AUD|CAD|CHF)\\b', v, re.IGNORECASE):
                    currency_count += 1
        
        # Only mark as currency if >50% of checked values have currency markers
        if checked > 0 and currency_count >= checked * 0.5:
            return "currency"
        
        return None

    def normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize all values in a record based on inferred types."""
        # First pass: infer types for each field
        if not record:
            return record
            
        # Get all values for each key
        # Note: This is a simplified version - in production you'd aggregate across records
        normalized = {}
        
        for key, value in record.items():
            # Try to parse as number
            num = self.parse_number(value)
            if num is not None:
                normalized[key] = num
                continue
            
            # Try to parse as date
            dt = self.parse_date(value)
            if dt:
                normalized[key] = dt.isoformat()
                continue
            
            # Keep as is
            normalized[key] = value
        
        return normalized


def normalize_data(data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normalize a list of records.
    
    Returns:
        Tuple of (normalized_data, field_metadata)
        field_metadata: {
            "types": {"field_name": "number|date|string"},
            "currency": {"field_name": "USD|EUR|GBP|..."}
        }
    """
    normalizer = DataNormalizer()
    
    # First pass: infer field types from all records
    if not data:
        return data, {"types": {}, "currency": {}}
    
    field_types: dict[str, str] = {}
    field_currency: dict[str, str] = {}
    
    # Sample first 50 records for type inference
    sample = data[:50]
    keys = set()
    for record in sample:
        keys.update(record.keys())
    
    for key in keys:
        values = [record.get(key) for record in sample]
        field_types[key] = normalizer.infer_field_type(values)
        
        # Check if it's a currency field (only from values, not field name)
        if field_types[key] == 'number':
            currency = normalizer.detect_currency_field(values)
            if currency:
                field_currency[key] = currency
    
    # Second pass: normalize based on inferred types
    normalized_data = []
    for record in data:
        normalized = {}
        for key, value in record.items():
            field_type = field_types.get(key, 'string')
            
            if field_type == 'number':
                num = normalizer.parse_number(value)
                if num is not None:
                    normalized[key] = num
                else:
                    normalized[key] = value
            elif field_type == 'date':
                dt = normalizer.parse_date(value)
                if dt:
                    normalized[key] = dt.isoformat()
                else:
                    normalized[key] = value
            else:
                normalized[key] = value
        
        normalized_data.append(normalized)
    
    field_metadata = {
        "types": field_types,
        "currency": field_currency
    }
    
    return normalized_data, field_metadata
