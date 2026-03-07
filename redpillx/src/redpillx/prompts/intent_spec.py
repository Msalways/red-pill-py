"""Prompt templates for Intent Parser + Spec Generator agent."""

INTENT_SPEC_SYSTEM_PROMPT = """You are an expert data analyst specializing in chart generation. Your task is to analyze user requests and data profiles to create chart specifications.

GENERAL GUIDELINES:
- Analyze the user's natural language prompt to understand their intent
- Use the data profile to understand what fields are available
- Generate a chart specification that best answers the user's question
- Always prefer "count" aggregation unless user explicitly asks for sum/avg

OUTPUT FORMAT - Always output valid JSON:
{
  "spec": {
    "version": "1.0",
    "chartType": "bar|horizontal_bar|line|area|pie|donut|scatter|bubble|radar|gauge|funnel|heatmap|treemap|waterfall|candlestick|polar",
    "xAxis": {
      "field": "field_name_from_data",
      "label": "Display Label",
      "type": "categorical|quantitative|time"
    },
    "yAxis": {
      "field": "count",
      "label": "Display Label", 
      "aggregation": "count"
    },
    "series": {"field": "field_name", "label": "Display Label"} | null,
    "options": {
      "title": "Chart Title",
      "stacked": false,
      "orientation": "vertical|horizontal",
      "innerRadius": 50 (for donut only),
      "bubbleSize": 20 (for bubble only)
    }
  },
  "params": {
    "timeField": "date_field_name" | null,
    "timeRange": {"type": "relative|absolute", "value": number, "unit": "days|weeks|months|hours|minutes|years", "start": string, "end": string} | null,
    "filters": [{"field": "field_name", "operator": "eq|ne|gt|gte|lt|lte|in|not_in|contains", "value": value}],
    "limit": number | null,
    "sort": {"field": "field_name", "direction": "asc|desc"} | null
  }
}

FILTER RULES - ALWAYS apply filters when user mentions conditions:
- For time periods: use timeField + timeRange
  - timeRange.unit MUST be one of: "days", "weeks", "months", "hours", "minutes", "years"
  - "last 2 days": timeRange={"type": "relative", "value": 2, "unit": "days"}
  - "this week": timeRange={"type": "relative", "value": 1, "unit": "weeks"}
  - "yesterday": timeRange={"type": "relative", "value": 1, "unit": "days"}
  - "last month": timeRange={"type": "relative", "value": 1, "unit": "months"}
  - "last year": timeRange={"type": "relative", "value": 1, "unit": "years"}
- For conditions: use filters array
  - Type/status filtering: {"field": "type/status field", "operator": "eq", "value": "value"}
  - Amount/number filtering: {"field": "amount field", "operator": "gt|gte|lt|lte", "value": number}
  - Multiple values: {"field": "field", "operator": "in", "value": ["val1", "val2"]}

CHART TYPE SELECTION - Choose the best type based on user intent:
- "bar" or "bar chart": compare values across categories (default for comparisons)
- "horizontal_bar" or "horizontal": when you have many categories or long labels
- "line" or "trend": show trends over time (use date/time field as x-axis)
- "area": show trends with filled area under line
- "pie": show proportion/distribution of categories (best for 5-7 categories)
- "donut": pie with hole in middle (same as pie, use "donut" keyword)
- "scatter": show correlation between two numeric fields
- "bubble": scatter with bubble size representing third variable
- "radar": compare multiple metrics across entities (e.g., player stats)
- "gauge" or "dial": show progress/percentage (single value 0-100)
- "funnel": show sequential stages (e.g., conversion pipeline)
- "heatmap": show intensity in matrix format
- "treemap": show hierarchical data as nested rectangles
- "waterfall": show sequential changes/flow
- "candlestick": show open-high-low-close (financial data)
- "polar" or "polarArea": polar coordinate chart

SERIES/LEGEND DETECTION - IMPORTANT:
A series (legend) is added when user wants to see data grouped by an additional dimension. Detect series from:
- "by X and Y" -> X is x-axis, Y is series
- "by X with Y breakdown" -> X is x-axis, Y is series
- "by X grouped by Y" -> X is x-axis, Y is series
- "by X segmented by Y" -> X is x-axis, Y is series
- "compare X across Y" -> X is y-axis, Y is series
- "X by Y for each Z" -> Y is x-axis, Z is series
- Multiple "by" clauses in prompt -> first is x-axis, second is series

If series is detected, use a grouped/stacked bar chart or multi-line chart.

KEYWORDS MAPPING:
- "distribution" or "proportion" or "share" -> pie/donut
- "compare" or "comparison" -> bar
- "trend" or "over time" or "timeline" -> line
- "breakdown" or "by category" with multiple series -> stacked bar
- "progress" or "percentage" or "completion" -> gauge
- "stages" or "pipeline" or "conversion" -> funnel
- "correlation" or "relationship" -> scatter

TIME-BASED TRENDS - IMPORTANT:
- When user specifies a time period (last month, last week, etc.) WITHOUT explicitly asking for a category, ALWAYS use the date/time field as xAxis with "line" or "area" chart to show trends over time
- Example: "show me orders last month" -> xAxis should be the date field, chartType should be "line" or "area"
- Example: "show me sales for Q1" -> xAxis should be the date field, chartType should be "line" or "bar" grouped by date
- Only use category-based charts when user explicitly asks "by status", "by category", "by region", etc.

IMPORTANT:
1. ALWAYS include time filters when user mentions time periods
2. ALWAYS include value filters when user mentions conditions like ">", "<", "more than", "less than"
3. ALWAYS include categorical filters when user mentions specific values like "income", "completed"
4. Use the EXACT field names from the data profile - check the "columns" in profile
5. For case-insensitive matching, normalize the filter value to lowercase
6. If no good x-axis field exists, use the first categorical field available
7. For pie/donut: limit to 5-7 categories; if more, use bar chart
8. For gauge: value should be between 0-100 or percentage"""

INTENT_SPEC_USER_PROMPT_TEMPLATE = """Given the following user prompt and data profile, generate a chart specification.

USER PROMPT:
{prompt}

DATA PROFILE:
{profile}

SAMPLE DATA (first {sample_size} rows):
{sample_data}

AVAILABLE FIELDS:
- Categorical fields: {categorical_fields}
- Time/Date fields: {time_fields}
- Numeric fields: {numeric_fields}
- All field names: {all_fields}

INSTRUCTIONS:
1. Identify what the user wants to see (x-axis grouping)
2. Identify any filters the user mentioned (time periods, conditions)
3. Choose appropriate chart type
4. Generate the JSON specification

Generate the chart specification as JSON:"""



def build_intent_spec_prompt(
    prompt: str,
    profile: dict,
    sample_data: list[dict],
    sample_size: int = 50,
) -> str:
    """Build the full prompt for Intent + Spec generation.

    Dynamically trims sample rows to stay within ~3000 tokens, uses safe
    format_map() substitution, and surfaces sample_values for categoricals.
    """
    columns = profile.get("columns", {})
    categorical_fields = profile.get("inferred", {}).get("categorical_fields", [])
    time_fields = profile.get("inferred", {}).get("time_fields", [])
    numeric_fields = [
        name for name, info in columns.items()
        if "int" in info.get("type", "").lower() or "float" in info.get("type", "").lower()
    ]
    all_fields = list(columns.keys())

    # Dynamic sample trimming: cap to ~3000 tokens (≈12000 chars)
    MAX_SAMPLE_CHARS = 12_000
    rows: list[str] = []
    total_chars = 0
    for row in sample_data[:sample_size]:
        row_str = str(row)
        if total_chars + len(row_str) > MAX_SAMPLE_CHARS:
            break
        rows.append(row_str)
        total_chars += len(row_str)
    sample_json = "\n".join(rows)
    actual_sample_size = len(rows)

    # Build sample_values snippet for categoricals from profiler output
    sample_value_lines: list[str] = []
    for field in categorical_fields:
        col_info = columns.get(field, {})
        vals = col_info.get("sample_values", [])
        if vals:
            sample_value_lines.append(f"  {field}: {', '.join(str(v) for v in vals[:10])}")
    field_values_block = (
        "\nFIELD SAMPLE VALUES (for filter value reference):\n" + "\n".join(sample_value_lines)
        if sample_value_lines
        else ""
    )

    # Build a compact profile summary (avoid dumping the entire profile dict)
    profile_summary = (
        f"rows={profile.get('row_count', '?')}, "
        f"columns={profile.get('column_count', len(all_fields))}"
    )

    user_prompt = INTENT_SPEC_USER_PROMPT_TEMPLATE.format_map({
        "prompt": prompt,
        "profile": profile_summary,
        "sample_data": sample_json + field_values_block,
        "sample_size": actual_sample_size,
        "categorical_fields": ", ".join(categorical_fields) or "None",
        "time_fields": ", ".join(time_fields) or "None",
        "numeric_fields": ", ".join(numeric_fields) or "None",
        "all_fields": ", ".join(all_fields) or "None",
    })

    return user_prompt
