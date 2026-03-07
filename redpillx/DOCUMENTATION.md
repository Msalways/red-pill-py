# Redpill SDK Documentation

## Overview
Redpill is an AI-powered SDK for dynamic chart generation from JSON data. It uses LLMs to interpret natural language prompts and generate chart specifications that can be executed on data.

## Architecture

### Core Components

#### 1. Client (`redpill.client`)
- **Main interface**: `Redpill` class
- **Configuration**: Fluent builder pattern
- **Providers**: OpenAI, Anthropic, and custom providers
- **Agents**: Intent spec agent, validator agent, LangGraph agent

#### 2. Data Processing (`redpill.processor`)
- **Flattener**: Converts nested JSON to flat records with dot-notation
- **Profiler**: Analyzes data structure and infers field types
- **Processor**: Combines flattening and profiling

#### 3. Chart Specification (`redpill.spec`)
- **Schema**: Pydantic models for chart specs
- **Types**: Bar, line, pie, scatter, area charts
- **Configuration**: Axis, series, filters, sorting, options

#### 4. Execution (`redpill.executor`)
- **Polars-based**: High-performance data processing
- **Async support**: Streaming for large datasets
- **Transformations**: Filtering, grouping, aggregation, sorting

## Quick Start

### Installation
```bash
pip install redpill
```

### Basic Usage
```python
from redpill import Redpill

# Initialize client
rp = (
    Redpill()
    .provider("openai")
    .api_key("your-api-key")
    .model("gpt-4o")
    .build()
)

# Generate spec from data and prompt
sample_data = {
    "tickets": [
        {"id": 1, "status": "open", "priority": "high", "created_at": "2026-02-23T10:00:00"},
        {"id": 2, "status": "closed", "priority": "low", "created_at": "2026-02-22T15:00:00"},
    ]
}

result = rp.generate_spec(
    data=sample_data,
    prompt="show me tickets by status with priority breakdown"
)

# Execute with full data
full_data = {"tickets": [...]}  # Your complete dataset
chart_data = rp.execute(spec=result.spec, data=full_data)

print(chart_data.data)  # Chart-ready data
print(chart_data.metadata)  # Chart metadata
```

## Configuration

### Client Configuration
```python
rp = (
    Redpill()
    .provider("openai")  # or "anthropic"
    .api_key("sk-...")
    .base_url("https://api.openai.com/v1")  # optional
    .model("gpt-4o")  # optional
    .temperature(0.7)  # optional
    .max_tokens(4000)  # optional
    .timeout(30)  # optional
    .max_retries(3)  # optional
    .sample_size(100)  # optional
    .build()
)
```

### Provider Configuration
```python
# OpenAI
rp = Redpill().provider("openai").api_key("sk-...").build()

# Anthropic
rp = Redpill().provider("anthropic").api_key("sk-...").build()

# Custom provider
rp = Redpill().provider("custom").base_url("https://api.example.com").api_key("sk-...").build()
```

## Data Processing

### Input Formats
Redpill accepts:
- **Dict**: `{"key": "value"}`
- **List**: `[{"key": "value"}, ...]`
- **JSON string**: `'{"key": "value"}'`

### Data Flattening
Nested JSON is automatically flattened:
```json
{
  "user": {
    "name": "John",
    "address": {
      "city": "NYC"
    }
  },
  "orders": [
    {"id": 1, "amount": 100}
  ]
}
```

Becomes:
```json
[
  {
    "user.name": "John",
    "user.address.city": "NYC",
    "orders.id": 1,
    "orders.amount": 100
  }
]
```

### Data Profiling
Redpill automatically profiles data to:
- Identify field types (categorical, quantitative, time)
- Detect time fields
- Infer data distributions
- Suggest appropriate chart types

## Chart Specification

### Chart Types
- **Bar**: Categorical vs quantitative data
- **Line**: Time series and trends
- **Pie**: Proportional data
- **Scatter**: Correlation analysis
- **Area**: Cumulative data

### Axis Configuration
```python
AxisConfig(
    field="tickets.status",  # Dot-notation for nested fields
    label="Status",
    type=AxisType.CATEGORICAL,
    aggregation=AggregationType.COUNT
)
```

### Series Configuration
```python
SeriesConfig(
    field="tickets.priority",
    label="Priority"
)
```

### Runtime Parameters
```python
RuntimeParams(
    time_field="created_at",
    time_range={
        "type": "relative",
        "value": 30,
        "unit": "days"
    },
    filters=[
        Filter(field="status", operator="eq", value="open")
    ],
    limit=10,
    sort=SortConfig(field="amount", direction="desc")
)
```

## LLM Integration

### Agent Types

#### 1. Intent Spec Agent
- **Purpose**: Parse user intent and generate chart spec
- **Workflow**: Process data → Generate spec → Validate spec
- **Retry**: Automatic retry on validation failure

#### 2. LangGraph Agent
- **Purpose**: Advanced workflow with built-in validation
- **Features**: State management, conditional edges, retry logic
- **Use case**: Complex chart generation with validation

### Prompt Processing
LLM receives:
- **User prompt**: Natural language request
- **Data profile**: Field types, distributions, time fields
- **Sample data**: Example records for context

### Validation
Generated specs are validated against:
- **Field existence**: Check if fields exist in data
- **Type compatibility**: Ensure field types match chart requirements
- **Aggregation validity**: Validate aggregation operations

## Execution

### Basic Execution
```python
chart_data = rp.execute(spec=spec, data=full_data)
```

### Streaming Execution
```python
async for batch in rp.execute_stream(spec=spec, data=full_data, batch_size=10000):
    process_batch(batch)
```

### Available Operations
- **Filtering**: Custom filters on any field
- **Time filtering**: Relative and absolute time ranges
- **Grouping**: Group by any field(s)
- **Aggregation**: Count, sum, avg, min, max
- **Sorting**: Sort by any field
- **Limiting**: Limit results

## Error Handling

### Common Errors
- **Field not found**: Specified field doesn't exist in data
- **Type mismatch**: Field type incompatible with chart type
- **API errors**: LLM provider errors
- **Validation errors**: Generated spec fails validation

### Error Recovery
- **Retry mechanism**: Automatic retry with enhanced prompts
- **Fallback strategies**: Alternative chart types
- **Detailed messages**: Specific error descriptions

## Best Practices

### Data Preparation
1. **Clean data**: Remove null/invalid values
2. **Consistent types**: Ensure consistent field types
3. **Time formatting**: Use ISO 8601 for time fields
4. **Sampling**: Use appropriate sample size for LLM

### Prompt Design
1. **Be specific**: Clear chart requirements
2. **Include context**: Mention data structure if complex
3. **Specify preferences**: Chart type, colors, labels
4. **Use examples**: Provide example outputs if possible

### Performance Optimization
1. **Sample size**: Balance between context and cost
2. **Batch processing**: Use streaming for large datasets
3. **Caching**: Cache generated specs for repeated use
4. **Preprocessing**: Pre-filter data when possible

## Integration Examples

### Web Application
```python
# API endpoint
@app.post("/api/chart")
def generate_chart(request: Request):
    data = request.json().get("data")
    prompt = request.json().get("prompt")
    
    rp = Redpill().provider("openai").api_key(API_KEY).build()
    result = rp.generate_spec(data=data, prompt=prompt)
    chart_data = rp.execute(spec=result.spec, data=data)
    
    return {
        "chartData": chart_data.data,
        "metadata": chart_data.metadata
    }
```

### Data Pipeline
```python
# Batch processing
for dataset in data_sources:
    spec = generate_spec_for_dataset(dataset)
    cache_spec(dataset.id, spec)
    
# Real-time processing
def process_event(event):
    spec = get_cached_spec(event.dataset_id)
    chart_data = execute_spec(spec, event.data)
    send_to_dashboard(chart_data)
```

## Troubleshooting

### Common Issues

#### 1. "Field not found" error
**Cause**: Field name mismatch or nested field not flattened
**Solution**: Check data structure, use dot-notation for nested fields

#### 2. "Invalid aggregation" error
**Cause**: Aggregation not supported for field type
**Solution**: Use appropriate aggregation (COUNT for categorical, SUM for numeric)

#### 3. LLM errors
**Cause**: API key issues, model errors, context limits
**Solution**: Check API credentials, reduce sample size, retry

#### 4. Performance issues
**Cause**: Large datasets, complex operations
**Solution**: Use streaming, reduce sample size, pre-filter data

### Debug Mode
```python
rp = Redpill().debug_mode(True).build()
```

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Features

### Custom Providers
```python
class CustomProvider(BaseProvider):
    def generate(self, prompt, system_prompt, **kwargs):
        # Custom implementation
        pass
```

### Custom Agents
```python
class CustomAgent(BaseAgent):
    def run(self, prompt, profile, sample_data):
        # Custom logic
        pass
```

### Template System
```python
# Predefined chart templates
templates = {
    "sales_dashboard": {
        "default_chart": "bar",
        "default_aggregation": "sum",
        "default_time_field": "created_at"
    }
}
```

## API Reference

### Redpill Class
```python
class Redpill:
    def __init__(self, config=None)
    def provider(self, provider: str) -> Redpill
    def api_key(self, api_key: str) -> Redpill
    def base_url(self, base_url: str) -> Redpill
    def model(self, model: str) -> Redpill
    def temperature(self, temperature: float) -> Redpill
    def max_tokens(self, max_tokens: int) -> Redpill
    def timeout(self, timeout: int) -> Redpill
    def max_retries(self, max_retries: int) -> Redpill
    def sample_size(self, sample_size: int) -> Redpill
    def build(self) -> Redpill
    def generate_spec(self, data, prompt) -> GenerateSpecOutput
    def generate_spec_with_agent(self, data, prompt) -> GenerateSpecOutput
    def execute(self, spec, data) -> ChartDataResult
    def execute_stream(self, spec, data, batch_size=10000) -> AsyncIterator
    def validate_spec(self, spec, profile) -> ValidationResult
```

### DataProcessor Class
```python
class DataProcessor:
    def process(self, data, sample_size=100) -> dict
```

### ChartSpec Model
```python
class ChartSpec(BaseModel):
    version: str
    chart_type: ChartType
    x_axis: AxisConfig
    y_axis: AxisConfig
    series: SeriesConfig | None
    options: ChartOptions | None
    params: RuntimeParams
```

## Version History

### v0.1.0 (Current)
- Initial release
- Core chart generation functionality
- OpenAI and Anthropic providers
- Basic chart types (bar, line, pie, scatter, area)
- Data processing and validation

### Planned Features
- Additional chart types (heatmap, treemap, etc.)
- Interactive chart support
- Export functionality
- Template system
- Custom visualization libraries

## Support

### Resources
- **Documentation**: This document
- **Examples**: Example scripts in repository
- **Tests**: End-to-end test cases

### Community
- **GitHub**: Issues and discussions
- **Discord**: Community chat
- **Email**: Support team

## License

MIT License - see LICENSE file for details.