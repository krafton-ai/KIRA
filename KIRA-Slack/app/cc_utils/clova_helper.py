"""
Clova Speech Recognition Client
For converting meeting audio to text in the web interface
"""

import httpx
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from app.config.settings import get_settings

settings = get_settings()

class ClovaSpeechClient:
    """Clova Speech Recognition API Client"""

    def __init__(self):
        self.invoke_url = settings.CLOVA_INVOKE_URL
        self.secret_key = settings.CLOVA_SECRET_KEY

    async def recognize_file(
        self,
        file_path: str,
        completion: str = "sync",
        diarization: Optional[Dict[str, Any]] = None,
        word_alignment: bool = True,
        full_text: bool = True
    ) -> Dict[str, Any]:
        """
        Convert audio file to text

        Args:
            file_path: Audio file path
            completion: 'sync' (synchronous) or 'async' (asynchronous)
            diarization: Speaker diarization settings {"enable": True, "speakerCountMin": 2, "speakerCountMax": 5}
            word_alignment: Include word-level timestamps
            full_text: Return full text

        Returns:
            Clova API response (JSON)
        """
        # Request parameters
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            'wordAlignment': word_alignment,
            'fullText': full_text,
        }

        # Speaker diarization option
        if diarization:
            request_body['diarization'] = diarization

        # Headers
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret_key
        }

        # Read file
        file = Path(file_path)
        if not file.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logging.info(f"[CLOVA] Uploading file: {file.name} ({file.stat().st_size} bytes)")

        # Prepare multipart form-data
        with open(file_path, 'rb') as f:
            files = {
                'media': (file.name, f, 'audio/mpeg'),
                'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
            }

            # API call
            async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout
                response = await client.post(
                    url=f"{self.invoke_url}/recognizer/upload",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()

                result = response.json()
                logging.info(f"[CLOVA] Recognition completed")

                return result


async def convert_speech_to_text(
    audio_file: str,
    enable_diarization: bool = False
) -> Dict[str, Any]:
    """
    Convert audio file to text (convenience function)

    Args:
        audio_file: Audio file path
        enable_diarization: Enable speaker diarization

    Returns:
        {
            'text': 'Full text',
            'segments': [...],  # When diarization is enabled
        }
    """
    client = ClovaSpeechClient()

    # Speaker diarization settings
    diarization = None
    if enable_diarization:
        diarization = {
            "enable": True,
            "speakerCountMin": 1,
            "speakerCountMax": 10
        }

    result = await client.recognize_file(
        file_path=audio_file,
        completion='sync',
        diarization=diarization,
        word_alignment=True,
        full_text=True
    )

    # Parse result
    text = result.get('text', '')
    segments = result.get('segments', [])

    return {
        'text': text,
        'segments': segments
    }


async def convert_speech_to_text_with_speakers(audio_file: str) -> str:
    """
    Generate meeting transcript with speaker identification

    Args:
        audio_file: Audio file path

    Returns:
        "[00:00] [Speaker1]: Hello\n[00:05] [Speaker2]: Nice to meet you\n..."
    """
    result = await convert_speech_to_text(audio_file, enable_diarization=True)

    if not result.get('segments'):
        # Return full text only if diarization failed
        return result.get('text', '')

    # Organize by speaker
    transcript = []
    for segment in result['segments']:
        speaker = segment.get('speaker', {}).get('label', 'Unknown')
        text = segment.get('text', '')
        start_time = segment.get('start', 0) // 1000  # ms -> s

        # Timestamp format (00:00)
        minutes = start_time // 60
        seconds = start_time % 60
        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        transcript.append(f"{timestamp} [Speaker{speaker}]: {text}")

    return "\n".join(transcript)
