"""Validator agent for chart spec validation with edge case warnings."""

from typing import Any

from redpillx.agents.base import BaseAgent
from redpillx.config.builder import RedpillConfig
from redpillx.providers import LLMProvider
from redpillx.spec.schema import ChartSpec, ChartType


class ValidationResult:
    """Result of spec validation."""

    def __init__(
        self,
        is_valid: bool,
        error: str | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.is_valid = is_valid
        self.error = error
        self.warnings = warnings or []


class ValidatorAgent(BaseAgent):
    """Agent that validates chart spec against data schema."""

    def __init__(self, provider: LLMProvider, config: RedpillConfig) -> None:
        super().__init__(provider, config)

    def run(
        self,
        spec: ChartSpec,
        profile: dict[str, Any],
        retry_callback: Any = None,
    ) -> ValidationResult:
        """Validate chart spec against data profile.

        Args:
            spec: Chart specification to validate
            profile: Data profile with available fields
            retry_callback: Optional callback to regenerate spec

        Returns:
            ValidationResult with is_valid status and warnings
        """
        warnings = []
        available_fields = set(profile.get("columns", {}).keys())
        row_count = profile.get("row_count", 0)
        
        x_field = spec.x_axis.field
        y_field = spec.y_axis.field
        
        simple_x = x_field.split(".")[-1] if "." in x_field else x_field
        simple_y = y_field.split(".")[-1] if "." in y_field else y_field
        
        if x_field not in available_fields and simple_x not in available_fields:
            return ValidationResult(
                is_valid=False, 
                error=f"X-axis field '{x_field}' not found in data. Available: {available_fields}"
            )
        
        if spec.y_axis.aggregation and spec.y_axis.aggregation.value == "count":
            pass
        else:
            if y_field not in available_fields and simple_y not in available_fields:
                return ValidationResult(
                    is_valid=False,
                    error=f"Y-axis field '{y_field}' not found in data"
                )
        
        if spec.params.time_field:
            time_field = spec.params.time_field
            simple_time = time_field.split(".")[-1] if "." in time_field else time_field
            if time_field not in available_fields and simple_time not in available_fields:
                warnings.append(f"Time field '{time_field}' not found in data - time filter will be ignored")
        
        for f in spec.params.filters or []:
            filter_field = f.field
            simple_filter = filter_field.split(".")[-1] if "." in filter_field else filter_field
            if filter_field not in available_fields and simple_filter not in available_fields:
                warnings.append(f"Filter field '{filter_field}' not found in data - filter will be ignored")
        
        if spec.chart_type == ChartType.PIE:
            unique_x = profile.get("columns", {}).get(x_field, {}).get("unique_count", 0)
            if unique_x > 20:
                warnings.append(f"Pie chart with {unique_x} categories may be hard to read - consider using bar chart")
        
        if spec.chart_type == ChartType.LINE:
            unique_x = profile.get("columns", {}).get(x_field, {}).get("unique_count", 0)
            if unique_x < 3:
                warnings.append(f"Line chart with only {unique_x} data points may not show meaningful trend")
        
        if row_count == 0:
            warnings.append("Dataset is empty - no chart can be generated")
        
        return ValidationResult(is_valid=True, warnings=warnings if warnings else None)
