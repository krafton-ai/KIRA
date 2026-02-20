"""
Meeting Tools for Claude Code SDK
Tools for managing meeting audio files and transcription
"""

import json
from typing import Any, Dict
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

from app.cc_utils.clova_helper import convert_speech_to_text_with_speakers
from app.config.settings import get_settings


@tool(
    "list_meeting_files",
    "Lists meeting/audio files for a specific date. Used for creating meeting minutes.",
    {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date to query (YYYYMMDD format, e.g., 20250128)"
            }
        },
        "required": ["date"]
    }
)
async def list_meeting_files(args: Dict[str, Any]) -> Dict[str, Any]:
    """List meeting files for a specific date"""
    date = args["date"]

    try:
        settings = get_settings()

        # Date folder path
        meetings_dir = Path(settings.FILESYSTEM_BASE_DIR) / "meetings" / date

        if not meetings_dir.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": True,
                        "date": date,
                        "files": [],
                        "message": f"No meeting files for date {date}."
                    }, ensure_ascii=False, indent=2)
                }]
            }

        # Get all file list
        files = []
        for file_path in sorted(meetings_dir.iterdir()):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "path": f"meetings/{date}/{file_path.name}",
                    "size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                    "extension": file_path.suffix
                })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "date": date,
                    "folder_path": str(meetings_dir),
                    "total_files": len(files),
                    "files": files,
                    "message": f"Retrieved {len(files)} meeting files for date {date}"
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Error occurred while retrieving file list: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


@tool(
    "transcribe_meeting",
    "Extracts text with speaker diarization from meeting/audio files. Used for creating meeting minutes.",
    {
        "type": "object",
        "properties": {
            "audio_file_path": {
                "type": "string",
                "description": "Path to audio file to transcribe (absolute or relative path, e.g., meetings/20250128/meeting_20250128_120000.webm)"
            }
        },
        "required": ["audio_file_path"]
    }
)
async def transcribe_meeting(args: Dict[str, Any]) -> Dict[str, Any]:
    """Transcribe meeting audio file to text (with speaker diarization)"""
    audio_file_path = args["audio_file_path"]

    try:
        settings = get_settings()

        # Process file path (convert relative path to FILESYSTEM_BASE_DIR based)
        file_path = Path(audio_file_path)
        if not file_path.is_absolute():
            file_path = Path(settings.FILESYSTEM_BASE_DIR) / audio_file_path

        # Check if file exists
        if not file_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": True,
                        "message": f"File not found: {audio_file_path}"
                    }, ensure_ascii=False, indent=2)
                }],
                "error": True
            }

        # Transcribe audio with Clova
        transcript = await convert_speech_to_text_with_speakers(str(file_path))

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "file_path": str(file_path),
                    "transcript": transcript,
                    "message": "Meeting audio transcription completed"
                }, ensure_ascii=False, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": True,
                    "message": f"Error occurred during audio transcription: {str(e)}"
                }, ensure_ascii=False, indent=2)
            }],
            "error": True
        }


# Create MCP Server
meetings_tools = [
    list_meeting_files,
    transcribe_meeting,
]


def create_meetings_mcp_server():
    """Meeting transcription MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(
        name="meeting_transcription",
        version="1.0.0",
        tools=meetings_tools
    )
