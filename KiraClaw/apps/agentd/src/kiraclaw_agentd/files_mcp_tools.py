from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from kiraclaw_agentd.mcp_stdio import McpToolSpec, mcp_text_result


def _workspace_dir() -> Path:
    value = os.environ.get("KIRACLAW_WORKSPACE_DIR", "")
    if value:
        return Path(value).expanduser()
    return Path.cwd()


def _resolve_path(file_path: str) -> Path:
    path = Path(file_path).expanduser()
    if path.is_absolute():
        return path
    return _workspace_dir() / path


def save_base64_image(args: dict[str, Any]) -> dict[str, Any]:
    file_path = args["file_path"]
    base64_data = args["base64_data"]

    try:
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        binary = base64.b64decode(base64_data)
        target = _resolve_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(binary)
        return mcp_text_result(
            {
                "success": True,
                "message": "Image saved successfully",
                "path": str(target),
                "size_bytes": len(binary),
            }
        )
    except base64.binascii.Error as exc:
        return mcp_text_result({"success": False, "error": f"Base64 decoding failed: {exc}"}, is_error=True)
    except Exception as exc:
        return mcp_text_result({"success": False, "error": f"File save failed: {exc}"}, is_error=True)


def read_file_as_base64(args: dict[str, Any]) -> dict[str, Any]:
    file_path = args["file_path"]

    try:
        target = _resolve_path(file_path)
        if not target.exists():
            return mcp_text_result({"success": False, "error": f"File not found: {target}"}, is_error=True)

        binary = target.read_bytes()
        base64_data = base64.b64encode(binary).decode("utf-8")
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        return mcp_text_result(
            {
                "success": True,
                "path": str(target),
                "size_bytes": len(binary),
                "mime_type": mime_types.get(target.suffix.lower(), "application/octet-stream"),
                "base64_data": base64_data,
            }
        )
    except Exception as exc:
        return mcp_text_result({"success": False, "error": f"File read failed: {exc}"}, is_error=True)


def build_files_tool_specs() -> list[McpToolSpec]:
    return [
        McpToolSpec(
            name="save_base64_image",
            description="Saves base64-encoded image data to a file. Use this when saving images received from Tableau, etc.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path to save (e.g., files/C12345/dashboard.png). Relative path from FILESYSTEM_BASE_DIR or absolute path",
                    },
                    "base64_data": {
                        "type": "string",
                        "description": "Base64-encoded image data (with or without data:image/png;base64, prefix)",
                    },
                },
                "required": ["file_path", "base64_data"],
            },
            handler=save_base64_image,
        ),
        McpToolSpec(
            name="read_file_as_base64",
            description="Reads a file and encodes it as base64. Use this before uploading image files to Slack, etc.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path to read. Relative path from FILESYSTEM_BASE_DIR or absolute path",
                    }
                },
                "required": ["file_path"],
            },
            handler=read_file_as_base64,
        ),
    ]
