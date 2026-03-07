"""Chart specification schemas using Pydantic."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChartType(str, Enum):
    """Supported chart types."""

    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    AREA = "area"
    RADAR = "radar"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    WATERFALL = "waterfall"
    CANDLESTICK = "candlestick"
    POLAR = "polar"


class AxisType(str, Enum):
    """Axis data types."""

    CATEGORICAL = "categorical"
    QUANTITATIVE = "quantitative"
    TIME = "time"


class AggregationType(str, Enum):
    """Aggregation types for y-axis."""

    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    NONE = "none"


class FilterOperator(str, Enum):
    """Filter operators."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"


class TimeRangeUnit(str, Enum):
    """Time range units."""

    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class SortDirection(str, Enum):
    """Sort directions."""

    ASC = "asc"
    DESC = "desc"


class AxisConfig(BaseModel):
    """Configuration for chart axis."""

    field: str = Field(description="Field name from the data")
    label: str | None = Field(default=None, description="Display label for axis")
    type: AxisType = Field(default=AxisType.CATEGORICAL, description="Axis data type")
    aggregation: AggregationType | None = Field(
        default=None, description="Aggregation to apply"
    )
    aggregation_field: str | None = Field(
        default=None, description="Field to aggregate (for count)"
    )


class SeriesConfig(BaseModel):
    """Configuration for series/grouping (legend)."""

    field: str = Field(description="Field name for grouping")
    label: str | None = Field(default=None, description="Display label")


class TimeRange(BaseModel):
    """Relative or absolute time range."""

    type: str = Field(description="Type: 'relative' or 'absolute'")
    value: int | None = Field(default=None, description="Value for relative range")
    unit: TimeRangeUnit | None = Field(default=None, description="Unit for relative")
    start: str | None = Field(default=None, description="Start for absolute (ISO)")
    end: str | None = Field(default=None, description="End for absolute (ISO)")


class Filter(BaseModel):
    """Filter configuration."""

    field: str = Field(description="Field to filter on")
    operator: FilterOperator = Field(description="Filter operator")
    value: Any = Field(description="Filter value")


class SortConfig(BaseModel):
    """Sort configuration."""

    field: str = Field(description="Field to sort by")
    direction: SortDirection = Field(default=SortDirection.DESC)


class ChartOptions(BaseModel):
    """Chart rendering options."""

    title: str | None = Field(default=None, description="Chart title")
    stacked: bool = Field(default=False, description="Stack series")
    orientation: str = Field(default="vertical", description="Orientation")
    colors: list[str] | None = Field(default=None, description="Color hex codes")
    innerRadius: int | None = Field(default=None, description="Inner radius for donut chart (0-100)")
    bubbleSize: int | None = Field(default=None, description="Bubble size multiplier for bubble chart")
    showLegend: bool = Field(default=True, description="Show legend")
    showGrid: bool = Field(default=True, description="Show grid lines")


class RuntimeParams(BaseModel):
    """Runtime parameters for data filtering."""

    time_field: str | None = Field(
        default=None, alias="timeField", description="Time field for filtering"
    )
    time_range: TimeRange | None = Field(
        default=None, alias="timeRange", description="Time range filter"
    )
    filters: list[Filter] = Field(default_factory=list, description="Additional filters")
    limit: int | None = Field(default=None, description="Limit results")
    sort: SortConfig | None = Field(default=None, description="Sort configuration")

    model_config = {"populate_by_name": True}


class ChartSpec(BaseModel):
    """Complete chart specification."""

    version: str = Field(default="1.0", description="Spec version")
    chart_type: ChartType = Field(alias="chartType", description="Chart type")
    x_axis: AxisConfig = Field(alias="xAxis", description="X-axis configuration")
    y_axis: AxisConfig = Field(alias="yAxis", description="Y-axis configuration")
    series: SeriesConfig | None = Field(default=None, description="Series configuration")
    options: ChartOptions | None = Field(default=None, description="Chart options")
    params: RuntimeParams = Field(
        default_factory=RuntimeParams, description="Runtime parameters"
    )

    model_config = {"populate_by_name": True}


class ChartDataResult(BaseModel):
    """Result from executing a chart spec."""

    data: list[dict[str, Any]] = Field(description="Chart-ready data")
    metadata: dict[str, Any] = Field(description="Chart metadata")


class GenerateSpecResult(BaseModel):
    """Result from generating a spec."""

    spec: ChartSpec = Field(description="Generated chart spec")
    profile: dict[str, Any] = Field(description="Data profile used")
