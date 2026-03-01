"""Prompt templates for Validator agent."""

VALIDATION_SYSTEM_PROMPT = """You are a chart specification validator. Your task is to verify that a chart spec is valid and can be executed against sample data.

You must validate:
1. All specified fields exist in the data
2. The chart type is supported
3. The aggregation is valid for the field type
4. The spec structure is correct JSON

Output a JSON object:
{
  "is_valid": true,
  "error": null,
  "warnings": []
}

If invalid, provide specific error message:
{
  "is_valid": false,
  "error": "Specific error message",
  "warnings": []
}
"""

VALIDATION_USER_PROMPT_TEMPLATE = """Validate the following chart specification against this data.

SPEC TO VALIDATE:
{spec}

DATA SCHEMA (available fields):
{schema}

Validate and return the result as JSON:"""


def build_validation_prompt(spec: dict, schema: dict) -> str:
    """Build the validation prompt."""
    return VALIDATION_USER_PROMPT_TEMPLATE.replace(
        "{spec}", str(spec)
    ).replace(
        "{schema}", str(schema)
    )
