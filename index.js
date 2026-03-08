#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "sample_data",
  version: "0.1.0"
});

const BASE_ROWS = [
  { id: 1, school: "Duke", conference: "ACC", wins: 27, losses: 6 },
  { id: 2, school: "UConn", conference: "Big East", wins: 30, losses: 4 },
  { id: 3, school: "Kansas", conference: "Big 12", wins: 25, losses: 8 },
  { id: 4, school: "Purdue", conference: "Big Ten", wins: 29, losses: 5 },
  { id: 5, school: "Houston", conference: "Big 12", wins: 28, losses: 6 },
  { id: 6, school: "Arizona", conference: "Big 12", wins: 24, losses: 9 },
  { id: 7, school: "Gonzaga", conference: "WCC", wins: 26, losses: 7 },
  { id: 8, school: "Tennessee", conference: "SEC", wins: 23, losses: 10 },
  { id: 9, school: "Alabama", conference: "SEC", wins: 22, losses: 11 },
  { id: 10, school: "Baylor", conference: "Big 12", wins: 21, losses: 12 }
];

server.tool(
  "get_sample_data",
  "Return sample NCAA-like records.",
  {
    count: z.number().int().min(1).max(100).default(5)
  },
  async ({ count = 5 }) => {
    const rows = Array.from({ length: count }, (_, index) => {
      const row = BASE_ROWS[index % BASE_ROWS.length];
      return { ...row, row_number: index + 1 };
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            dataset: "ncaa_sample",
            count,
            rows
          })
        }
      ]
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
