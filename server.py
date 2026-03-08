"""
sample_data_mcp - MCP server for querying sample.csv customer data.
"""

import json
import csv
import os
from typing import Optional, List, Dict, Any
from enum import Enum
from urllib.parse import unquote

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

# ── Constants ────────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(os.path.dirname(__file__), "sample.csv")

NUMERIC_FIELDS = {"id", "age", "salary", "purchase_amount", "loyalty_points", "rating"}
ALL_FIELDS = [
    "id", "first_name", "last_name", "email", "age", "department",
    "city", "salary", "status", "join_date", "last_purchase_date",
    "product", "purchase_amount", "loyalty_points", "rating",
]

# ── Server ────────────────────────────────────────────────────────────────────

mcp = FastMCP("sample_data_mcp")

# ── Data helpers ──────────────────────────────────────────────────────────────

def _load_data() -> List[Dict[str, Any]]:
    """Load and type-cast all rows from the CSV."""
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cast: Dict[str, Any] = {}
            for k, v in row.items():
                if k in NUMERIC_FIELDS:
                    try:
                        cast[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        cast[k] = v
                else:
                    cast[k] = v
            rows.append(cast)
    return rows


def _apply_filters(
    rows: List[Dict[str, Any]],
    department: Optional[str],
    city: Optional[str],
    status: Optional[str],
    min_salary: Optional[float],
    max_salary: Optional[float],
    min_age: Optional[int],
    max_age: Optional[int],
    product: Optional[str],
) -> List[Dict[str, Any]]:
    """Apply optional filter parameters to a row list."""
    if department:
        rows = [r for r in rows if r["department"].lower() == department.lower()]
    if city:
        rows = [r for r in rows if r["city"].lower() == city.lower()]
    if status:
        rows = [r for r in rows if r["status"].lower() == status.lower()]
    if min_salary is not None:
        rows = [r for r in rows if r["salary"] >= min_salary]
    if max_salary is not None:
        rows = [r for r in rows if r["salary"] <= max_salary]
    if min_age is not None:
        rows = [r for r in rows if r["age"] >= min_age]
    if max_age is not None:
        rows = [r for r in rows if r["age"] <= max_age]
    if product:
        rows = [r for r in rows if r["product"].lower() == product.lower()]
    return rows


def _paginate(rows: List[Any], limit: int, offset: int) -> Dict[str, Any]:
    """Slice rows and return a pagination envelope."""
    total = len(rows)
    page = rows[offset: offset + limit]
    return {
        "total": total,
        "count": len(page),
        "offset": offset,
        "has_more": total > offset + len(page),
        "next_offset": offset + len(page) if total > offset + len(page) else None,
        "items": page,
    }


def _build_prompt_text(prompt_name: str, **kwargs: Any) -> str:
    """Create a compact instruction string agents can run directly."""
    args = ", ".join(f"{k}={v!r}" for k, v in kwargs.items() if v is not None)
    if args:
        return f"Use {prompt_name}({args}) and return a concise answer with key numbers."
    return f"Use {prompt_name}() and return a concise answer with key numbers."

# ── Input models ──────────────────────────────────────────────────────────────

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class CommonFilters(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    department: Optional[str] = Field(None, description="Filter by department name (e.g. 'Engineering')")
    city: Optional[str] = Field(None, description="Filter by city (e.g. 'Austin')")
    status: Optional[str] = Field(None, description="Filter by status: Active | Inactive | Pending | Suspended")
    min_salary: Optional[float] = Field(None, description="Minimum salary filter", ge=0)
    max_salary: Optional[float] = Field(None, description="Maximum salary filter", ge=0)
    min_age: Optional[int] = Field(None, description="Minimum age filter", ge=0, le=120)
    max_age: Optional[int] = Field(None, description="Maximum age filter", ge=0, le=120)
    product: Optional[str] = Field(None, description="Filter by product purchased")
    limit: int = Field(20, description="Max records to return (1-100)", ge=1, le=100)
    offset: int = Field(0, description="Pagination offset", ge=0)


class SearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., description="Text to search across first_name, last_name, email, city, department, product", min_length=1)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class GetRecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: int = Field(..., description="The numeric id of the record to retrieve", ge=1)


class AggregateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    group_by: str = Field(..., description="Field to group by: department | city | status | product")
    metric: str = Field("count", description="Metric: count | avg_salary | total_purchase | avg_rating | avg_loyalty")
    department: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    min_salary: Optional[float] = Field(None, ge=0)
    max_salary: Optional[float] = Field(None, ge=0)
    product: Optional[str] = Field(None)


class SortInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sort_by: str = Field(..., description="Field to sort by (e.g. salary, age, rating, loyalty_points)")
    order: SortOrder = Field(SortOrder.DESC, description="asc or desc")
    department: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    min_salary: Optional[float] = Field(None, ge=0)
    max_salary: Optional[float] = Field(None, ge=0)
    min_age: Optional[int] = Field(None, ge=0, le=120)
    max_age: Optional[int] = Field(None, ge=0, le=120)
    product: Optional[str] = Field(None)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(
    name="sample_data_list_records",
    annotations={
        "title": "Data | List / Filter Records",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_list_records(params: CommonFilters) -> str:
    """List customer records with optional filters and pagination.

    Returns a paginated list of records. Apply any combination of filters
    (department, city, status, salary range, age range, product).

    Args:
        params (CommonFilters): Filter and pagination parameters.

    Returns:
        str: JSON object with keys:
            - total (int): total matching records
            - count (int): records in this page
            - offset (int): current offset
            - has_more (bool): whether more pages exist
            - next_offset (int | null): offset for next page
            - items (list[dict]): matching records
    """
    rows = _load_data()
    rows = _apply_filters(
        rows, params.department, params.city, params.status,
        params.min_salary, params.max_salary, params.min_age, params.max_age, params.product,
    )
    return json.dumps(_paginate(rows, params.limit, params.offset), indent=2)


@mcp.tool(
    name="sample_data_get_record",
    annotations={
        "title": "Data | Get Record by ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_get_record(params: GetRecordInput) -> str:
    """Retrieve a single customer record by its numeric ID.

    Args:
        params (GetRecordInput): Contains record_id (int).

    Returns:
        str: JSON object of the record, or an error message if not found.
    """
    rows = _load_data()
    for r in rows:
        if r["id"] == params.record_id:
            return json.dumps(r, indent=2)
    return json.dumps({"error": f"No record found with id={params.record_id}"})


@mcp.tool(
    name="sample_data_search",
    annotations={
        "title": "Data | Full-Text Search Records",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_search(params: SearchInput) -> str:
    """Search records by text across name, email, city, department, and product fields.

    Case-insensitive substring match against:
    first_name, last_name, email, city, department, product.

    Args:
        params (SearchInput): query (str), limit (int), offset (int).

    Returns:
        str: JSON paginated result with matching records.
    """
    q = params.query.lower()
    search_fields = ["first_name", "last_name", "email", "city", "department", "product"]
    rows = _load_data()
    matches = [r for r in rows if any(q in str(r.get(f, "")).lower() for f in search_fields)]
    return json.dumps(_paginate(matches, params.limit, params.offset), indent=2)


@mcp.tool(
    name="sample_data_aggregate",
    annotations={
        "title": "Analytics | Aggregate / Group Records",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_aggregate(params: AggregateInput) -> str:
    """Group records and compute a metric per group.

    group_by options : department | city | status | product
    metric options   : count | avg_salary | total_purchase | avg_rating | avg_loyalty

    Args:
        params (AggregateInput): group_by, metric, and optional filters.

    Returns:
        str: JSON list of {group, value} objects sorted descending by value.
             Schema: [{"group": str, "value": number}, ...]
    """
    valid_group = {"department", "city", "status", "product"}
    valid_metric = {"count", "avg_salary", "total_purchase", "avg_rating", "avg_loyalty"}

    if params.group_by not in valid_group:
        return json.dumps({"error": f"group_by must be one of {sorted(valid_group)}"})
    if params.metric not in valid_metric:
        return json.dumps({"error": f"metric must be one of {sorted(valid_metric)}"})

    rows = _load_data()
    rows = _apply_filters(
        rows, params.department, params.city, params.status,
        None, None, None, None, params.product,
    )

    buckets: Dict[str, List[Any]] = {}
    for r in rows:
        key = str(r.get(params.group_by, "unknown"))
        buckets.setdefault(key, []).append(r)

    results = []
    for group, members in buckets.items():
        if params.metric == "count":
            value = len(members)
        elif params.metric == "avg_salary":
            value = round(sum(m["salary"] for m in members) / len(members), 2)
        elif params.metric == "total_purchase":
            value = round(sum(m["purchase_amount"] for m in members), 2)
        elif params.metric == "avg_rating":
            value = round(sum(m["rating"] for m in members) / len(members), 2)
        else:  # avg_loyalty
            value = round(sum(m["loyalty_points"] for m in members) / len(members), 2)
        results.append({"group": group, "value": value})

    results.sort(key=lambda x: x["value"], reverse=True)
    return json.dumps(results, indent=2)


@mcp.tool(
    name="sample_data_sort",
    annotations={
        "title": "Data | Sort Records",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_sort(params: SortInput) -> str:
    """Return records sorted by any field, with optional filters and pagination.

    Useful for top-N queries (e.g. highest salaries, best ratings).

    Args:
        params (SortInput): sort_by field, order (asc|desc), filters, limit, offset.

    Returns:
        str: JSON paginated result with sorted records.
    """
    if params.sort_by not in ALL_FIELDS:
        return json.dumps({"error": f"sort_by must be one of {ALL_FIELDS}"})

    rows = _load_data()
    rows = _apply_filters(
        rows, params.department, params.city, params.status,
        params.min_salary, params.max_salary, params.min_age, params.max_age, params.product,
    )

    reverse = params.order == SortOrder.DESC
    try:
        rows.sort(key=lambda r: (r[params.sort_by] is None, r[params.sort_by]), reverse=reverse)
    except TypeError:
        rows.sort(key=lambda r: str(r.get(params.sort_by, "")), reverse=reverse)

    return json.dumps(_paginate(rows, params.limit, params.offset), indent=2)


@mcp.tool(
    name="sample_data_schema",
    annotations={
        "title": "Schema | Get Dataset Schema",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_schema() -> str:
    """Return the schema, field types, and distinct values for categorical fields.

    Use this first to understand what data is available before querying.

    Returns:
        str: JSON object with:
            - fields: list of {name, type}
            - total_records: int
            - categorical_values: dict of field -> list of unique values
    """
    rows = _load_data()
    cat_fields = ["department", "city", "status", "product"]
    categorical: Dict[str, List[str]] = {
        f: sorted({str(r[f]) for r in rows}) for f in cat_fields
    }
    schema = {
        "fields": [
            {"name": f, "type": "number" if f in NUMERIC_FIELDS else "string"}
            for f in ALL_FIELDS
        ],
        "total_records": len(rows),
        "categorical_values": categorical,
    }
    return json.dumps(schema, indent=2)


@mcp.tool(
    name="sample_data_open_dashboard",
    title="Apps | Open Sample Data Dashboard",
    description="App entry tool for Inspector Apps tab",
    meta={
        "ui/resourceUri": "ui://sample-data/dashboard",
        "ui": {"resourceUri": "ui://sample-data/dashboard"},
        "category": "app",
        "version": "1.0",
    },
    annotations={
        "title": "Apps | Open Sample Data Dashboard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def sample_data_open_dashboard() -> str:
    """Return app bootstrap data for UI-capable MCP clients."""
    return json.dumps(
        {
            "message": "Sample Data dashboard is available.",
            "resource_uri": "ui://sample-data/dashboard",
            "recommended_start": "sample_data_schema",
        },
        indent=2,
    )


# ── Resources ────────────────────────────────────────────────────────────────

@mcp.resource(
    "sample-data://schema",
    name="sample_data_schema_resource",
    title="Dataset Schema Resource",
    description="Structured schema and categorical values for sample.csv",
    mime_type="application/json",
    meta={
        "category": "schema",
        "version": "1.0",
        "tags": ["dataset", "discovery"],
    },
)
def sample_data_schema_resource() -> str:
    """Resource view of dataset schema for MCP Inspector Resource tab."""
    rows = _load_data()
    cat_fields = ["department", "city", "status", "product"]
    categorical: Dict[str, List[str]] = {
        f: sorted({str(r[f]) for r in rows}) for f in cat_fields
    }
    payload = {
        "fields": [
            {"name": f, "type": "number" if f in NUMERIC_FIELDS else "string"}
            for f in ALL_FIELDS
        ],
        "total_records": len(rows),
        "categorical_values": categorical,
    }
    return json.dumps(payload, indent=2)


@mcp.resource(
    "ui://sample-data/dashboard",
        name="sample_data_ui_dashboard",
        title="Sample Data Dashboard UI",
        description="Simple HTML UI resource for MCP app discovery",
    mime_type="text/html;profile=mcp-app",
)
def sample_data_ui_dashboard() -> str:
        """Static UI resource that can be referenced by app-aware clients."""
        return """<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Sample Data MCP Dashboard</title>
    <style>
        :root { color-scheme: light; font-family: Segoe UI, sans-serif; }
        body { margin: 0; padding: 24px; background: #f6f8fb; color: #1f2937; }
        .card { max-width: 720px; background: #fff; border: 1px solid #dbe2ea; border-radius: 12px; padding: 20px; }
        h1 { margin-top: 0; font-size: 1.3rem; }
        code { background: #eef3f8; padding: 2px 6px; border-radius: 4px; }
        ul { margin-bottom: 0; }
    </style>
</head>
<body>
    <div class=\"card\">
        <h1>Sample Data MCP</h1>
        <p>This UI resource is linked from a tool via <code>_meta.ui.resourceUri</code>.</p>
        <p>Try these tools:</p>
        <ul>
            <li><code>sample_data_schema</code></li>
            <li><code>sample_data_sort</code></li>
            <li><code>sample_data_aggregate</code></li>
        </ul>
    </div>
</body>
</html>"""


@mcp.resource(
    "sample-data://record/{record_id}",
    name="sample_data_record_resource",
    title="Record by ID Resource",
    description="Get a single record by ID through a resource URI template",
    mime_type="application/json",
    meta={
        "category": "records",
        "version": "1.0",
        "tags": ["lookup", "template"],
    },
)
def sample_data_record_resource(record_id: str) -> str:
    """Template resource that returns one record or an error payload."""
    try:
        target_id = int(record_id)
    except ValueError:
        return json.dumps({"error": "record_id must be an integer"}, indent=2)

    for row in _load_data():
        if row["id"] == target_id:
            return json.dumps(row, indent=2)

    return json.dumps({"error": f"No record found with id={target_id}"}, indent=2)


@mcp.resource(
    "sample-data://product/{product_name}/price",
    name="sample_data_product_price_resource",
    title="Product Price Lookup Resource",
    description="Lookup purchase amount details for a product name",
    mime_type="application/json",
    meta={
        "category": "pricing",
        "version": "1.0",
        "tags": ["product", "template", "analytics"],
    },
)
def sample_data_product_price_resource(product_name: str) -> str:
    """Template resource that returns purchase amount stats for a product."""
    target = unquote(product_name).strip().lower()
    matches = [r for r in _load_data() if str(r.get("product", "")).lower() == target]

    if not matches:
        return json.dumps(
            {
                "error": f"No records found for product='{unquote(product_name)}'",
                "hint": "Use sample-data://schema to view valid product values.",
            },
            indent=2,
        )

    prices = [float(r["purchase_amount"]) for r in matches]
    payload = {
        "product": matches[0]["product"],
        "match_count": len(matches),
        "price_stats": {
            "min": round(min(prices), 2),
            "max": round(max(prices), 2),
            "avg": round(sum(prices) / len(prices), 2),
            "total": round(sum(prices), 2),
        },
        "sample_records": [
            {
                "id": r["id"],
                "customer": f"{r['first_name']} {r['last_name']}",
                "last_purchase_date": r["last_purchase_date"],
                "purchase_amount": r["purchase_amount"],
            }
            for r in matches[:10]
        ],
    }
    return json.dumps(payload, indent=2)


# ── Prompts ──────────────────────────────────────────────────────────────────

@mcp.prompt(
    name="sample_data_prompt_library",
    title="Prompts | Sample Data Prompt Library",
    description="Ten ready-to-use prompts (tags: starter, examples, dataset)",
)
def sample_data_prompt_library() -> list[dict[str, str]]:
    """Provide a reusable prompt pack visible in MCP Inspector."""
    prompts = [
        "Show the top 10 highest salaries across all departments.",
        "Which city has the most Active users?",
        "List 5 Engineering records in Seattle, sorted by rating descending.",
        "Find everyone with age between 30 and 40 and salary over 90,000.",
        "What is the total purchase amount by product?",
        "Compare average salary by department and show highest to lowest.",
        "Search for records containing 'Garcia' and return the first 20.",
        "Get record with id 42 and summarize key details.",
        "Which status group has the highest average loyalty points?",
        "Show me the 10 most recent purchasers by last_purchase_date.",
    ]
    prompt_text = "Sample prompts:\n" + "\n".join(f"{i + 1}. {p}" for i, p in enumerate(prompts))
    return [{"role": "user", "content": prompt_text}]


@mcp.prompt(
    name="sample_data_prompt_top_salaries",
    title="Prompts | Top Salaries Prompt Builder",
    description="Parameterized salary-analysis prompt (tags: salary, ranking, analytics)",
)
def sample_data_prompt_top_salaries(limit: int = 10, city: Optional[str] = None) -> list[dict[str, str]]:
    """Parameterized prompt to guide an agent toward a top-salary query."""
    instruction = _build_prompt_text(
        "sample_data_sort",
        sort_by="salary",
        order="desc",
        city=city,
        limit=limit,
    )
    return [{"role": "user", "content": instruction}]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
