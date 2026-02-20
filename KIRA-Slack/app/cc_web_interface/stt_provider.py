"""
STT (Speech-to-Text) Provider Abstraction
Designed for easy switching between Web Speech API and Deepgram
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class STTProvider(ABC):
    """STT Provider abstract class"""

    @abstractmethod
    def get_provider_type(self) -> str:
        """Return provider type (webspeech / deepgram)"""
        pass

    @abstractmethod
    def get_client_config(self) -> Optional[Dict[str, Any]]:
        """Return configuration for client use"""
        pass


class WebSpeechProvider(STTProvider):
    """Web Speech API Provider (browser built-in)"""

    def get_provider_type(self) -> str:
        return "webspeech"

    def get_client_config(self) -> Optional[Dict[str, Any]]:
        """Web Speech is handled entirely on client side, minimal config needed"""
        return {
            "type": "webspeech",
            "lang": "ko-KR",  # Korean
            "continuous": False,  # Continuous recognition
            "interimResults": True  # Show interim results
        }


class DeepgramProvider(STTProvider):
    """Deepgram API Provider (for future implementation)"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_provider_type(self) -> str:
        return "deepgram"

    def get_client_config(self) -> Optional[Dict[str, Any]]:
        """Return Deepgram configuration"""
        return {
            "type": "deepgram",
            "api_key": self.api_key,
            "language": "ko",
            "model": "nova-2",  # Latest model
            "smart_format": True  # Auto-add punctuation
        }


# Select current provider
def get_stt_provider() -> STTProvider:
    """Return current STT Provider"""
    # TODO: Make configurable via environment variable or settings
    # Currently using Web Speech API
    return WebSpeechProvider()

    # To switch to Deepgram:
    # from app.config.settings import get_settings
    # settings = get_settings()
    # return DeepgramProvider(api_key=settings.DEEPGRAM_API_KEY)
