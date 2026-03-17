from __future__ import annotations

import asyncio
import inspect
import json
import sys
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

JSON = dict[str, Any]
ToolHandler = Callable[[dict[str, Any]], Awaitable[JSON] | JSON]


@dataclass(frozen=True)
class McpToolSpec:
    name: str
    description: str
    input_schema: JSON
    handler: ToolHandler


def mcp_text_result(payload: JSON, *, is_error: bool = False) -> JSON:
    result: JSON = {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ]
    }
    if is_error:
        result["isError"] = True
    return result


async def _invoke(handler: ToolHandler, args: dict[str, Any]) -> JSON:
    result = handler(args)
    if inspect.isawaitable(result):
        result = await result
    return result


async def serve_mcp_stdio(name: str, version: str, tools: list[McpToolSpec]) -> int:
    tool_map = {tool.name: tool for tool in tools}

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            sys.stdout.flush()
            continue

        method = message.get("method")
        message_id = message.get("id")

        if method == "notifications/initialized":
            continue

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": name, "version": version},
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.input_schema,
                        }
                        for tool in tools
                    ]
                },
            }
        elif method == "tools/call":
            params = message.get("params") or {}
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            tool = tool_map.get(tool_name)
            if tool is None:
                response = {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                }
            else:
                try:
                    result = await _invoke(tool.handler, arguments)
                except Exception as exc:
                    result = mcp_text_result({"success": False, "error": str(exc)}, is_error=True)
                response = {"jsonrpc": "2.0", "id": message_id, "result": result}
        else:
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }

        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    return 0


def run_mcp_stdio(name: str, version: str, tools: list[McpToolSpec]) -> int:
    return asyncio.run(serve_mcp_stdio(name=name, version=version, tools=tools))
