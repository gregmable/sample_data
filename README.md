# sample_data_mcp

An MCP server that lets any MCP-compatible agent query **sample.csv** — 200 customer records with 15 fields.

---

## Setup

```bash
# 1. Install dependencies
pip install "mcp[cli]" pydantic

# 2. Place sample.csv in the same directory as server.py

# 3. Run the server (stdio transport — default for local use)
python server.py
```

### Claude Desktop / claude_desktop_config.json

```json
{
  "mcpServers": {
    "sample_data": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

---

## Tools

| Tool | Description |
|---|---|
| `sample_data_schema` | Get field names, types, total records, and all distinct values for categorical fields. **Start here.** |
| `sample_data_list_records` | List/filter records. Supports department, city, status, salary range, age range, product. Paginated. |
| `sample_data_get_record` | Fetch a single record by numeric `id`. |
| `sample_data_search` | Full-text substring search across name, email, city, department, product. |
| `sample_data_aggregate` | Group by a field (department/city/status/product) and compute count, avg_salary, total_purchase, avg_rating, or avg_loyalty. |
| `sample_data_sort` | Sort records by any field (asc/desc) with optional filters. Great for top-N queries. |

---

## Example Queries an Agent Can Answer

- *"Which department has the highest average salary?"* → `sample_data_aggregate(group_by="department", metric="avg_salary")`
- *"Show me the top 5 highest-paid employees in Austin"* → `sample_data_sort(sort_by="salary", city="Austin", limit=5)`
- *"How many active users are there per city?"* → `sample_data_aggregate(group_by="city", metric="count", status="Active")`
- *"Find all records mentioning 'Garcia'"* → `sample_data_search(query="Garcia")`
- *"What products are available in the dataset?"* → `sample_data_schema()`

## 10 Prompt Ideas

- "Show the top 10 highest salaries across all departments."
- "Which city has the most Active users?"
- "List 5 Engineering records in Seattle, sorted by rating descending."
- "Find everyone with age between 30 and 40 and salary over 90,000."
- "What is the total purchase amount by product?"
- "Compare average salary by department and show highest to lowest."
- "Search for records containing 'Garcia' and return the first 20."
- "Get record with id 42 and summarize key details."
- "Which status group has the highest average loyalty points?"
- "Show me the 10 most recent purchasers by last_purchase_date."

---

## Dataset Fields

| Field | Type |
|---|---|
| id | number |
| first_name, last_name, email | string |
| age | number |
| department, city | string |
| salary | number |
| status | string (Active/Inactive/Pending/Suspended) |
| join_date, last_purchase_date | string (YYYY-MM-DD) |
| product | string |
| purchase_amount, loyalty_points, rating | number |
