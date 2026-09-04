import asyncio
from datetime import datetime, timezone

from .database import SessionLocal
from .models import Node


HEARTBEAT_TIMEOUT = 30


async def monitor_nodes():

    while True:

        db = SessionLocal()

        try:

            nodes = db.query(Node).all()

            now = datetime.now(timezone.utc)

            for node in nodes:

                if node.last_heartbeat is None:
                    continue

                elapsed = (
                    now - node.last_heartbeat
                ).total_seconds()

                if elapsed > HEARTBEAT_TIMEOUT:

                    if node.status != "offline":

                        node.status = "offline"

                        print(
                            f"Node {node.id} "
                            f"marked OFFLINE"
                        )

            db.commit()

        finally:

            db.close()

        await asyncio.sleep(5)