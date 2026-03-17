from __future__ import annotations

import uvicorn

from kiraclaw_agentd.api import create_app
from kiraclaw_agentd.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
