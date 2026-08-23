"""Creates DB tables and seeds the default leadership title taxonomy.

Run manually (`python scripts/init_db.py`) or let `app.main`'s lifespan handler
do the same thing automatically on server startup.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_models
from app.taxonomy import seed_default_taxonomy


async def main() -> None:
    await init_models()
    async with SessionLocal() as session:
        await seed_default_taxonomy(session)
    print("Database initialized and taxonomy seeded.")


if __name__ == "__main__":
    asyncio.run(main())
