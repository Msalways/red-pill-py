# Redpill Python SDK

> AI-powered SDK for dynamic chart generation from any JSON data — **BYOLLM** (Bring Your Own LLM)

The Redpill Python SDK lets you point a natural-language prompt + raw JSON at any LLM of your choice and get back chart-ready, structured data. You supply the LLM callable; Redpill handles data flattening, type normalisation, spec generation, validation, filtering, grouping, and aggregation via **[Polars](https://pola.rs/)**.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [API Reference](#api-reference)
   - [Redpill (Main Client)](#redpill-main-client)
   - [RedpillConfigBuilder](#redpillconfigbuilder)
   - [ChartSpec (Pydantic Models)](#chartspec-pydantic-models)
   - [PolarsExecutor](#polarsexecutor)
   - [AsyncPolarsExecutor](#asyncpolarsexecutor)
   - [IntentSpecAgent](#intentspecagent)
   - [ValidatorAgent](#validatoragent)
   - [LangGraphAgent](#langgraphagent)
5. [LLM Integration Examples](#llm-integration-examples)
6. [ChartSpec Fields Reference](#chartspec-fields-reference)
7. [Filter Operators](#filter-operators)
8. [Chart Types](#chart-types)
9. [Data Formats Supported](#data-formats-supported)
10. [Known Gaps & Edge Cases](#known-gaps--edge-cases)
11. [Development Setup](#development-setup)

---

## Installation

```bash
pip install redpill
```

### Install with optional extras

```bash
# All LLM providers (Gemini, Cohere, etc.)
pip install "redpill[all]"

# Development tools (pytest, ruff, mypy)
pip install "redpill[dev]"
```

> **Requires:** Python ≥ 3.10, Polars ≥ 0.20, Pydantic ≥ 2.0

---

## Quick Start

```python
from redpill import Redpill
from openai import OpenAI

client = OpenAI(api_key="sk-...")

def my_llm(messages, options=None):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=options.get("temperature", 0.7) if options else 0.7,
        max_tokens=options.get("max_tokens", 4000) if options else 4000,
    )
    return {"content": response.choices[0].message.content}


rp = (
    Redpill()
    .llm(my_llm)
    .temperature(0.3)
    .max_tokens(2000)
    .sample_size(50)
    .build()
)

data = {
    "tickets": [
        {"id": 1, "status": "open",   "priority": "high",   "amount": 350},
        {"id": 2, "status": "closed", "priority": "low",    "amount": 120},
        {"id": 3, "status": "open",   "priority": "medium", "amount": 200},
    ]
}

# 1. Generate a chart specification
result = rp.generate_spec(data=data, prompt="show me ticket count by status")

print(result.spec.chart_type)   # ChartType.BAR
print(result.spec.x_axis.field) # "status"

# 2. Execute the spec against the raw data
chart_data = rp.execute(spec=result.spec, data=data)

print(chart_data.data)
# [{"x": "open", "y": 2, "label_x": "Status", "label_y": "Count"}, ...]

print(chart_data.metadata)
# {"chartType": "bar", "xAxis": {...}, "yAxis": {...}, "warnings": None, ...}
```

---

## How It Works

```
Raw JSON data (dict / list / JSON string)
    │
    ▼
DataFlattener          – Flatten nested objects: {user.name: "Alice"}
    │
    ▼
DataNormalizer         – Detect & convert currency strings, date strings, numeric strings
    │
    ▼
DataProfiler           – Infer column types, unique counts, row count
    │
    ▼
IntentSpecAgent  ──────────────────────── Your LLM callable
    │                                     (system prompt + data profile + sample rows)
    ▼
ChartSpec (Pydantic-validated)
    │
    ├──► ValidatorAgent  – Cross-check fields against data profile; surface warnings
    │
    ▼
PolarsExecutor         – Polars DataFrame pipeline:
                         filters → time filter → grouping/aggregation → sort → limit
    │
    ▼
ChartDataResult        – { data: list[dict], metadata: dict }
```

---

## API Reference

### Redpill (Main Client)

```python
from redpill import Redpill
```

#### Constructor

```python
rp = Redpill()
```

Holds a `RedpillConfigBuilder` internally. Defaults: `temperature=0.7`, `max_tokens=4000`, `sample_size=100`, `debug_mode=False`, `max_retries=3`.

#### `.llm(llm_fn) -> Redpill`

Set your LLM callable. **Required before `.build()`.**

```python
def llm_fn(messages: list[dict], options: dict | None = None) -> dict:
    # messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
    # options:  {"temperature": float, "max_tokens": int, "model": str}
    # return:   {"content": str}
    ...
```

#### `.temperature(value: float) -> Redpill`

LLM sampling temperature. Default: `0.7`.

#### `.max_tokens(value: int) -> Redpill`

Maximum LLM output tokens. Default: `4000`.

#### `.sample_size(value: int) -> Redpill`

Rows sampled from your data and sent to the LLM for schema context. Default: `100`.  
Lower this (e.g. `20`) for large datasets or small context windows.

#### `.debug_mode(value: bool) -> Redpill`

Enable debug output. Default: `False`.

#### `.build() -> Redpill`

Validates configuration and initialises the `DataProcessor`, `PolarsExecutor`, and `IntentSpecAgent`.

Raises `ValueError` if `.llm()` was not called.

#### `.generate_spec(data, prompt) -> GenerateSpecOutput`

Generate a `ChartSpec` from raw data and a natural-language prompt.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `Any` | Raw data: `dict`, `list`, or a JSON `str` |
| `prompt` | `str` | Natural language description, e.g. `"show tickets by status"` |

Returns `GenerateSpecOutput`:

```python
output.spec     # ChartSpec (Pydantic model)
output.profile  # dict — data profile used for spec generation
```

#### `.execute(spec, data) -> ChartDataResult`

Execute a spec against raw data.

| Parameter | Type | Description |
|-----------|------|-------------|
| `spec` | `ChartSpec \| dict` | Chart specification |
| `data` | `Any` | Raw data: `dict`, `list`, or a JSON `str` |

Returns `ChartDataResult`:

```python
result.data      # list[dict] — chart-ready rows: {x, y, label_x, label_y, series?, label_series?}
result.metadata  # dict — chart type, axes, warnings, original/filtered counts, currency info
```

---

### RedpillConfigBuilder

Lower-level builder if you want to construct configuration separately:

```python
from redpill.config.builder import RedpillConfigBuilder

config = (
    RedpillConfigBuilder()
    .llm(my_llm_fn)
    .temperature(0.5)
    .max_tokens(1000)
    .sample_size(30)
    .debug_mode(True)
    .build()
)
# config: RedpillConfig dataclass
```

Alternatively, use the helper:

```python
from redpill.config.builder import create_client

builder = create_client(temperature=0.5, sample_size=30)
```

---

### ChartSpec (Pydantic Models)

All schemas live in `redpill.spec.schema` and are backed by **Pydantic v2**.

```python
from redpill.spec.schema import (
    ChartSpec, ChartType, AxisConfig, SeriesConfig,
    ChartOptions, RuntimeParams, TimeRange, Filter,
    SortConfig, ChartDataResult
)
```

You can hand-craft a spec without the LLM:

```python
from redpill.spec.schema import ChartSpec, AxisConfig, AggregationType, ChartType

spec = ChartSpec(
    chartType="bar",
    xAxis=AxisConfig(field="status", label="Status"),
    yAxis=AxisConfig(field="status", label="Count", aggregation=AggregationType.COUNT),
)
chart_data = rp.execute(spec=spec, data=raw_data)
```

> `ChartSpec` uses **camelCase aliases** for JSON interoperability (`chartType`, `xAxis`, `yAxis`, `timeField`, `timeRange`) but **snake_case attribute names** in Python (`chart_type`, `x_axis`, `y_axis`, `time_field`, `time_range`). Enable `populate_by_name=True` by default.

---

### PolarsExecutor

Execute specs with full Polars pipeline support, independently of the `Redpill` client:

```python
from redpill.executor.polars_executor import PolarsExecutor

executor = PolarsExecutor()
result = executor.execute(spec=my_spec, data=raw_data)
```

The executor supports:
- **JSON string input** — auto-parsed via `json.loads`
- **Nested dicts** — auto-flattened
- **Currency string normalisation** — `"$1,200"` → `1200.0`
- **Dot-notation field resolution** — `user.city` resolves to `city` if flattened
- **All filter operators** including `not_in`
- **Multi-format date parsing** — 10 date formats including ISO-8601, `%d/%m/%Y`, `%Y%m%d`, etc.

---

### AsyncPolarsExecutor

For large datasets, stream results in batches:

```python
from redpill.executor.polars_executor import AsyncPolarsExecutor

executor = AsyncPolarsExecutor()

async for batch in executor.execute_stream(spec=my_spec, data=large_data, batch_size=10000):
    process(batch)  # list[dict] per batch
```

---

### IntentSpecAgent

Direct access to the spec-generation agent:

```python
from redpill.agents.intent_spec_agent import IntentSpecAgent
from redpill.config.builder import RedpillConfig

config = RedpillConfig(llm=my_llm_fn, temperature=0.3, max_tokens=2000, sample_size=30)
agent = IntentSpecAgent(config)

result = agent.run(
    prompt="tickets by status",
    profile={"columns": {"status": {"type": "string"}, "amount": {"type": "number"}}},
    sample_data=[{"status": "open", "amount": 100}],
)

spec   = result["spec"]    # ChartSpec
params = result["params"]  # RuntimeParams
```

The agent retries up to **`config.max_retries`** times (default 3). On failure, raises `RuntimeError`.

---

### ValidatorAgent

Validate a spec against a data profile:

```python
from redpill.agents.validator import ValidatorAgent
from redpill.config.builder import RedpillConfig
from redpill.providers import LLMProvider  # your provider instance

validator = ValidatorAgent(provider, config)
result = validator.run(spec=my_spec, profile=data_profile)

result.is_valid   # bool
result.error      # str | None — error message if invalid
result.warnings   # list[str] — non-fatal warnings
```

Checks performed:
- X-axis field exists in data
- Y-axis field exists in data (skip for `count` aggregation)
- Time field exists (warning if missing, not error)
- Filter fields exist in data (warning if missing)
- Pie chart with > 20 categories (warning)
- Line chart with < 3 data points (warning)
- Empty dataset (warning)

---

### LangGraphAgent

Full agentic workflow with **spec generation → validation → auto-retry**:

```python
from redpill.agents.langgraph_agent import LangGraphAgent
from redpill.processor.processor import DataProcessor

agent = LangGraphAgent(provider=my_provider, config=config, processor=DataProcessor())

result = agent.run(data=raw_data, prompt="show revenue by region")

result["spec"]               # ChartSpec
result["profile"]            # dict
result["params"]             # RuntimeParams
result["validation_result"]  # {"is_valid": bool, "error": str|None, "warnings": list}
result["retry_count"]        # int — how many retries were needed
```

The LangGraph workflow:

```
process_data → generate_spec → validate_spec
                    ↑                 │
                    └── retry_spec ←──┘ (if invalid and retries remain)
```

Raises `RuntimeError` if generation fails; raises `ValueError` if validation fails after all retries.

> **Note:** `LangGraphAgent` currently requires a `LLMProvider` instance (from `redpill.providers`), not a plain callable — see [Known Gaps](#known-gaps--edge-cases).

---

## LLM Integration Examples

### OpenAI

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

def llm(messages, options=None):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=options.get("temperature", 0.7) if options else 0.7,
        max_tokens=options.get("max_tokens", 4000) if options else 4000,
    )
    return {"content": response.choices[0].message.content}

rp = Redpill().llm(llm).build()
```

### OpenRouter (any model)

```python
from openai import OpenAI

client = OpenAI(api_key="sk-or-...", base_url="https://openrouter.ai/api/v1")

def llm(messages, options=None):
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",  # any OpenRouter model
        messages=messages,
        temperature=(options or {}).get("temperature", 0.7),
    )
    return {"content": response.choices[0].message.content}

rp = Redpill().llm(llm).build()
```

### Anthropic Claude

```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

def llm(messages, options=None):
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=(options or {}).get("max_tokens", 4000),
        messages=[{"role": m["role"], "content": m["content"]} for m in messages
                  if m["role"] != "system"],
        system=next((m["content"] for m in messages if m["role"] == "system"), ""),
    )
    return {"content": response.content[0].text}

rp = Redpill().llm(llm).build()
```

### Ollama (local)

```python
import requests

def llm(messages, options=None):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.1",
            "messages": messages,
            "stream": False,
            "options": {"temperature": (options or {}).get("temperature", 0.7)},
        },
    )
    return {"content": response.json()["message"]["content"]}

rp = Redpill().llm(llm).build()
```

### Google Gemini (via OpenAI compat)

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)

def llm(messages, options=None):
    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=messages,
        temperature=(options or {}).get("temperature", 0.7),
    )
    return {"content": response.choices[0].message.content}

rp = Redpill().llm(llm).build()
```

---

## ChartSpec Fields Reference

```python
ChartSpec(
    version="1.0",                     # optional, informational

    chartType="bar",                   # see Chart Types below (alias for chart_type)

    xAxis=AxisConfig(                  # alias: x_axis
        field="status",                # data field (dot notation supported: "user.city")
        label="Status",                # optional display label
        type=AxisType.CATEGORICAL,     # CATEGORICAL | QUANTITATIVE | TIME (default: CATEGORICAL)
        aggregation=None,              # AggregationType or None
        aggregation_field=None,        # field for aggregation (optional)
    ),

    yAxis=AxisConfig(                  # alias: y_axis
        field="amount",
        label="Total Amount",
        aggregation=AggregationType.SUM,  # COUNT|SUM|AVG|MIN|MAX|NONE
    ),

    series=SeriesConfig(               # optional — adds legend/breakdown
        field="priority",
        label="Priority",
    ),

    options=ChartOptions(
        title="Ticket Revenue by Status",
        stacked=False,
        orientation="vertical",        # or "horizontal"
        colors=["#FF6B6B", "#4ECDC4"],
        innerRadius=60,                # donut chart inner radius 0-100
        bubbleSize=10,                 # bubble size multiplier
        showLegend=True,
        showGrid=True,
    ),

    params=RuntimeParams(
        timeField="created_at",        # alias: time_field
        timeRange=TimeRange(           # alias: time_range
            type="relative",           # or "absolute"
            value=3,
            unit=TimeRangeUnit.MONTHS, # MINUTES|HOURS|DAYS|WEEKS|MONTHS|YEARS
            # For absolute:
            # start="2024-01-01T00:00:00",
            # end="2024-12-31T23:59:59",
        ),
        filters=[
            Filter(field="priority", operator=FilterOperator.EQ, value="high"),
            Filter(field="amount",   operator=FilterOperator.GTE, value=500),
        ],
        limit=20,
        sort=SortConfig(field="y", direction=SortDirection.DESC),
    ),
)
```

---

## Filter Operators

| Operator (`FilterOperator`) | Description |
|-----------------------------|-------------|
| `EQ` / `"eq"` | Equal (case-insensitive for strings) |
| `NE` / `"ne"` | Not equal (case-insensitive for strings) |
| `GT` / `"gt"` | Greater than |
| `GTE` / `"gte"` | Greater than or equal |
| `LT` / `"lt"` | Less than |
| `LTE` / `"lte"` | Less than or equal |
| `IN` / `"in"` | Value in list (case-insensitive for strings) |
| `NOT_IN` / `"not_in"` | Value not in list (case-insensitive for strings) |
| `CONTAINS` / `"contains"` | Substring match (case-insensitive) |

---

## Chart Types

| `ChartType` | Value | Description |
|-------------|-------|-------------|
| `BAR` | `"bar"` | Vertical bar chart |
| `HORIZONTAL_BAR` | `"horizontal_bar"` | Horizontal bar chart |
| `LINE` | `"line"` | Line chart |
| `AREA` | `"area"` | Area chart |
| `PIE` | `"pie"` | Pie chart |
| `DONUT` | `"donut"` | Donut chart |
| `SCATTER` | `"scatter"` | Scatter plot |
| `BUBBLE` | `"bubble"` | Bubble chart |
| `RADAR` | `"radar"` | Radar/spider chart |
| `GAUGE` | `"gauge"` | Gauge chart |
| `FUNNEL` | `"funnel"` | Funnel chart |
| `HEATMAP` | `"heatmap"` | Heatmap |
| `TREEMAP` | `"treemap"` | Treemap |
| `WATERFALL` | `"waterfall"` | Waterfall chart |
| `CANDLESTICK` | `"candlestick"` | Candlestick (OHLC) |
| `POLAR` | `"polar"` | Polar chart |

---

## Data Formats Supported

```python
# 1. Array of flat records
data = [{"status": "open", "amount": 100}, {"status": "closed", "amount": 50}]

# 2. Object with one array property (most common API shape)
data = {"tickets": [{"id": 1, "status": "open"}, ...]}

# 3. JSON string (auto-parsed)
data = '{"tickets": [{"id": 1, "status": "open"}]}'

# 4. Nested objects (auto-flattened with dot notation)
data = [{"user": {"name": "Alice", "city": "NY"}, "amount": 100}]
# Becomes: [{"user.name": "Alice", "user.city": "NY", "amount": 100}]

# ⚠️  Arrays inside records are handled with index prefix, NOT dropped
# (Python SDK differs from JS here — uses the row index as prefix)
```

---

## Known Gaps & Edge Cases

These are areas where the SDK does not currently handle all cases:

### Data Handling
| Gap | Details |
|-----|---------|
| **Arrays inside records use index prefix** | Nested arrays are flattened using an index: `items.0.name`. This may produce unexpected column names in the LLM context. |
| **Months approximated as 30 days** | The time filter uses `timedelta(days=value * 30)` for months. This does not align with calendar months. |
| **Date format tried sequentially** | `_apply_time_filter` tries 10 formats in order and stops at the first parse success. If your date field has mixed formats, only one will be used. |
| **Normaliser samples 50 rows only** | Type inference and currency detection examine only the first 50 rows. A field that contains currency values after row 50 will not be detected. |

### Spec Generation
| Gap | Details |
|-----|---------|
| **`IntentSpecAgent` always passes `model` in options** | The agent includes `model: getattr(config, 'model', 'openai/gpt-4o-mini')` in the options dict, but `RedpillConfig` has no `model` field. The `getattr` fallback silently returns the default every time. |
| **`[DEBUG]` always printed** | Line 60 of `intent_spec_agent.py` always prints to `stderr` regardless of `config.debug_mode`. |
| **No fallback spec** | Unlike the JS SDK, the Python `IntentSpecAgent` raises `RuntimeError` after `max_retries` failures with no heuristic fallback. |
| **`IntentSpecAgent.run` returns extra `params` key** | The method returns `{"spec": ChartSpec, "params": RuntimeParams}` but `Redpill.generate_spec` only exposes `spec` on `GenerateSpecOutput`. The `params` from the agent response is silently discarded. |

### LangGraph Agent
| Gap | Details |
|-----|---------|
| **`LangGraphAgent` is not wired into `Redpill` client** | It requires a `LLMProvider` from `redpill.providers` instead of the plain callable used by the rest of the SDK. Cannot be used via `.build()`. |
| **`langgraph_agent.py` imports `redpill.providers`** | This module is not shipped in the default package (only `core` dependencies). Using `LangGraphAgent` requires the `[all]` extra to be installed. |
| **State mutation anti-pattern** | `retry_spec_node` mutates the prompt in `AgentState` directly. After retry, the original prompt is lost. |

### Executor
| Gap | Details |
|-----|---------|
| **`filteredCount` reports DataFrame height after grouping** | `filteredCount` in metadata reflects the grouped row count, not the filtered-before-grouping row count. |
| **`aggregation_field` on `AxisConfig` is unused** | The field is defined in the schema but `_apply_grouping()` always aggregates on `y_axis.field`. |
| **`none` aggregation defaults to `count`** | `AggregationType.NONE` falls through to the `else` branch which returns `pl.len().alias("count")`. |
| **`_resolve_field` only tries last dot segment** | `user.city` resolves to `city`. If two nested paths share the same leaf name (e.g. `a.name` and `b.name`), only the first match is found. |
| **`series` grouping with duplicate x-values** | When `series_field` is set, fields containing the group separator in values may produce incorrect group keys in some configurations. |
| **Pie/donut percentage not calculated** | Chart data for pie/donut charts does not include a percentage column. Downstream renderers must compute this themselves. |
| **`AsyncPolarsExecutor.execute_stream` is not truly async** | The underlying Polars operations are synchronous. The method is `async def` and uses `yield`, but each batch is produced synchronously inside the generator. |

### Other
| Gap | Details |
|-----|---------|
| **`ValidatorAgent` depends on provider pattern** | `ValidatorAgent` extends `BaseAgent` which expects an `LLMProvider`. It cannot be used with a plain callable like the rest of the SDK. |
| **No built-in spec caching** | Every `generate_spec` call hits the LLM. There is no memoisation or spec cache. |
| **No streaming LLM support** | The `call_llm` function expects a fully-resolved `{"content": str}` response. Streaming responses must be aggregated by the caller before passing to the SDK. |
| **`pyproject.toml` lists heavy LangChain deps as required** | `langchain-core`, `langchain-openai`, `langchain-anthropic`, `langchain-aws`, `langchain-ollama`, and `langgraph` are all listed as main `dependencies`, not optional extras. Every install pulls these in even if LangGraph is never used. |

---

## Development Setup

```bash
# Clone and enter the package directory
cd packages/python/redpill

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install with dev extras
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type-check
mypy src/
```

### Build & Publish

```bash
python -m build
twine upload dist/*
```

---

## Chart Library Integration

The Python SDK returns the same `ChartDataResult` shape as the JS SDK, making it trivially consumable by any frontend chart library (via an API) or Python plotting library directly.

📖 **[CHART_INTEGRATION.md](./CHART_INTEGRATION.md)**

The guide covers:
- Recharts, Chart.js, ECharts, ApexCharts, Plotly.js (JS/React)
- Matplotlib and Plotly (Python)
- Adapter functions, React components, and end-to-end examples for every chart type
- Series/grouped data handling, currency formatting, and warnings display

---

## License

MIT
