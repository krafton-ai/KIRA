from __future__ import annotations

import base64
import json

from kiraclaw_agentd.files_mcp_tools import read_file_as_base64, save_base64_image


def _payload(result: dict) -> dict:
    return json.loads(result["content"][0]["text"])


def test_files_tools_roundtrip_base64_image(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KIRACLAW_WORKSPACE_DIR", str(tmp_path))

    binary = b"not-really-a-png"
    saved = _payload(
        save_base64_image(
            {
                "file_path": "files/C123/example.png",
                "base64_data": base64.b64encode(binary).decode("utf-8"),
            }
        )
    )

    assert saved["success"] is True
    assert saved["path"].endswith("files/C123/example.png")

    loaded = _payload(read_file_as_base64({"file_path": "files/C123/example.png"}))
    assert loaded["success"] is True
    assert loaded["mime_type"] == "image/png"
    assert base64.b64decode(loaded["base64_data"]) == binary
