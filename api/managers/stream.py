from asyncio import create_task
from datetime import datetime, timezone

from api.models.league import StandingsDocument
from api.models.match import MatchDocument


class ChangeStreamManager:
    def __init__(self, db):
        self.db = db
        self.connections = {}  # Maps connection_id to a list of active websocket connections

    async def watch_changes(self):
        collection = self.db["matches"]
        async with collection.watch(full_document="updateLookup") as stream:
            async for change in stream:
                operation_type = change["operationType"]
                if operation_type in {"insert", "replace"}:
                    # Get the current date and time in UTC
                    now = datetime.now(tz=timezone.utc)

                    # Create a new datetime object for the first day of the current month at midnight
                    first_day_of_month = datetime(year=now.year, month=now.month, day=1, tzinfo=timezone.utc)
                    standings = await StandingsDocument.get_standings_by_date(start_date=first_day_of_month)
                    match = MatchDocument(**change["fullDocument"])
                    if not standings:
                        standings = StandingsDocument(
                            players=[],
                            start_date=first_day_of_month,
                            end_date=None,
                            matches=[],
                        )
                    await standings.refresh(match)

    async def start(self):
        create_task(self.watch_changes())  # Run watch_changes as a background task
