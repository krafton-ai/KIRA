"""
Files Tools for Claude Code SDK
Tools for file saving/conversion
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.config.settings import get_settings


def get_base_dir() -> Path:
    """Return base directory for file storage"""
    settings = get_settings()
    base_dir = settings.FILESYSTEM_BASE_DIR
    if not base_dir:
        base_dir = os.path.expanduser("~/Documents/KIRA")
    return Path(base_dir)


@tool(
    "save_base64_image",
    "Saves base64-encoded image data to a file. Use this when saving images received from Tableau, etc.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "File path to save (e.g., files/C12345/dashboard.png). Relative path from FILESYSTEM_BASE_DIR or absolute path"
            },
            "base64_data": {
                "type": "string",
                "description": "Base64-encoded image data (with or without data:image/png;base64, prefix)"
            }
        },
        "required": ["file_path", "base64_data"]
    }
)
async def save_base64_image(args: Dict[str, Any]) -> Dict[str, Any]:
    """Save base64 image to file"""
    file_path = args["file_path"]
    base64_data = args["base64_data"]

    try:
        # Remove data:image/png;base64, prefix
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        # Base64 decoding
        image_data = base64.b64decode(base64_data)

        # Path processing
        if not os.path.isabs(file_path):
            full_path = get_base_dir() / file_path
        else:
            full_path = Path(file_path)

        # Create directory
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        with open(full_path, "wb") as f:
            f.write(image_data)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Image saved successfully",
                    "path": str(full_path),
                    "size_bytes": len(image_data)
                }, ensure_ascii=False, indent=2)
            }]
        }

    except base64.binascii.Error as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": f"Base64 decoding failed: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": f"File save failed: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "isError": True
        }


@tool(
    "read_file_as_base64",
    "Reads a file and encodes it as base64. Use this before uploading image files to Slack, etc.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "File path to read. Relative path from FILESYSTEM_BASE_DIR or absolute path"
            }
        },
        "required": ["file_path"]
    }
)
async def read_file_as_base64(args: Dict[str, Any]) -> Dict[str, Any]:
    """Read file as base64"""
    file_path = args["file_path"]

    try:
        # Path processing
        if not os.path.isabs(file_path):
            full_path = get_base_dir() / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": f"File not found: {full_path}"
                    }, ensure_ascii=False, indent=2)
                }],
                "isError": True
            }

        # Read file and encode as base64
        with open(full_path, "rb") as f:
            file_data = f.read()

        base64_data = base64.b64encode(file_data).decode("utf-8")

        # Estimate MIME type
        suffix = full_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        mime_type = mime_types.get(suffix, "application/octet-stream")

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "path": str(full_path),
                    "size_bytes": len(file_data),
                    "mime_type": mime_type,
                    "base64_data": base64_data
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": f"File read failed: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "isError": True
        }


# Register tools
files_tools = [save_base64_image, read_file_as_base64]


def create_files_mcp_server():
    """Claude Code SDK Files MCP server"""
    return create_sdk_mcp_server(name="files-tools", version="1.0.0", tools=files_tools)
