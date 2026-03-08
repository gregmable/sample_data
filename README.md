# sample_data MCP scaffold

This folder is a minimal MCP server package that can be run with `npx`.

## What it provides

- Server name: `sample_data`
- Tool: `get_sample_data`
- Input: `count` (1-100, default 5)
- Output: JSON payload with `dataset`, `count`, and `rows`

## Publish/use on GitHub

1. Copy these files into your `gregmable/sample_data` repo root.
2. Push to GitHub.
3. Keep your VS Code config as:

```json
{
  "servers": {
    "sample_data": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:gregmable/sample_data"]
    }
  }
}
```

4. In VS Code run: `MCP: List Servers` -> start/restart `sample_data`.
5. In chat, request: "Use sample_data get_sample_data with count 5".
