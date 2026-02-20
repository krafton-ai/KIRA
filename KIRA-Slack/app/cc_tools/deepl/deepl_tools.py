"""
DeepL Document Translation Tools for Claude Code SDK
Claude can translate documents using DeepL API
"""

import json
from typing import Any, Dict

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

from app.config.settings import get_settings


def get_deepl_key() -> str:
    """Get DeepL API key from settings"""
    settings = get_settings()
    key = settings.DEEPL_API_KEY
    if not key:
        raise ValueError("DEEPL_API_KEY is not set in settings")
    return key


def get_deepl_base_url() -> str:
    """Get DeepL API base URL (Pro or Free)"""
    # You can add DEEPL_API_TYPE to settings if needed to switch between pro/free
    return "https://api.deepl.com/v2"


@tool(
    "deepl_upload_document",
    "Upload a document to DeepL for translation. Returns document_id and document_key for tracking.",
    {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to translate (e.g., '/path/to/document.pdf')",
            },
            "target_lang": {
                "type": "string",
                "description": "Target language code. Examples: 'EN-US', 'EN-GB', 'KO', 'JA', 'DE', 'FR', 'ES', 'ZH' (Chinese), 'PT-BR', 'PT-PT'. See DeepL docs for full list.",
            },
            "source_lang": {
                "type": "string",
                "description": "Source language code (optional, auto-detected if omitted)",
            },
            "output_format": {
                "type": "string",
                "description": "Desired output file extension (e.g., 'docx', 'pdf', 'pptx'). Optional - defaults to input format.",
            },
            "formality": {
                "type": "string",
                "description": "Formality level: 'default', 'formal', or 'informal'. Only supported for: DE, FR, IT, ES, NL, PL, PT-BR, PT-PT, RU. DO NOT use for JA, EN, ZH, KO. (optional)",
            },
            "glossary_id": {
                "type": "string",
                "description": "Custom glossary ID (optional)",
            },
        },
        "required": ["file_path", "target_lang"],
    },
)
async def deepl_upload_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """Upload a document to DeepL for translation"""
    api_key = get_deepl_key()
    base_url = get_deepl_base_url()

    file_path = args["file_path"]
    target_lang = args["target_lang"]
    source_lang = args.get("source_lang")
    output_format = args.get("output_format")
    formality = args.get("formality")
    glossary_id = args.get("glossary_id")

    try:
        # Read file from path
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        filename = os.path.basename(file_path)

        # Prepare form data
        files = {"file": (filename, file_bytes)}

        data = {"target_lang": target_lang}

        if source_lang:
            data["source_lang"] = source_lang
        if output_format:
            data["output_format"] = output_format
        if formality:
            data["formality"] = formality
        if glossary_id:
            data["glossary_id"] = glossary_id

        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/document", headers=headers, files=files, data=data
            )
            response.raise_for_status()

            result = response.json()

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "document_id": result.get("document_id"),
                                "document_key": result.get("document_key"),
                                "message": "Document uploaded successfully for translation",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

    except httpx.HTTPStatusError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"HTTP {e.response.status_code}: {e.response.text}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Error: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "deepl_check_status",
    "Check the translation status of a document. Returns status: 'queued', 'translating', 'done', or 'error'.",
    {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "Document ID returned from upload",
            },
            "document_key": {
                "type": "string",
                "description": "Document key returned from upload",
            },
        },
        "required": ["document_id", "document_key"],
    },
)
async def deepl_check_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check the translation status of a document"""
    api_key = get_deepl_key()
    base_url = get_deepl_base_url()

    document_id = args["document_id"]
    document_key = args["document_key"]

    try:
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            "Content-Type": "application/json",
        }

        data = {"document_key": document_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/document/{document_id}", headers=headers, json=data
            )
            response.raise_for_status()

            result = response.json()

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "document_id": result.get("document_id"),
                                "status": result.get("status"),
                                "seconds_remaining": result.get("seconds_remaining"),
                                "billed_characters": result.get("billed_characters"),
                                "error_message": result.get("error_message"),
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

    except httpx.HTTPStatusError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"HTTP {e.response.status_code}: {e.response.text}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Error: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "deepl_download_document",
    "Download the translated document and save to specified path.",
    {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "Document ID returned from upload",
            },
            "document_key": {
                "type": "string",
                "description": "Document key returned from upload",
            },
            "output_path": {
                "type": "string",
                "description": "Absolute path where the translated file should be saved (e.g., '/path/to/translated_document.pdf')",
            },
        },
        "required": ["document_id", "document_key", "output_path"],
    },
)
async def deepl_download_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """Download the translated document"""
    api_key = get_deepl_key()
    base_url = get_deepl_base_url()

    document_id = args["document_id"]
    document_key = args["document_key"]
    output_path = args["output_path"]

    try:
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            "Content-Type": "application/json",
        }

        data = {"document_key": document_key}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/document/{document_id}/result", headers=headers, json=data
            )
            response.raise_for_status()

            # Response is binary file content
            file_bytes = response.content

            # Save to output path
            import os

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(file_bytes)

            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "output_path": output_path,
                                "content_type": content_type,
                                "size_bytes": len(file_bytes),
                                "message": f"Document downloaded and saved to {output_path}",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

    except httpx.HTTPStatusError as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"HTTP {e.response.status_code}: {e.response.text}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Error: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


# MCP Server
deepl_tools = [
    deepl_upload_document,
    deepl_check_status,
    deepl_download_document,
]


def create_deepl_tools_server():
    """Claude Code SDK DeepL Document Translation MCP server"""
    return create_sdk_mcp_server(name="deepl-tools", version="1.0.0", tools=deepl_tools)
