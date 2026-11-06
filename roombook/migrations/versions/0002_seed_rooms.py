"""Three demo rooms, so a fresh database can take bookings."""

from datetime import time

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"

rooms = sa.table(
    "rooms",
    sa.column("id", sa.Text),
    sa.column("name", sa.Text),
    sa.column("capacity", sa.Integer),
    sa.column("hourly_rate", sa.Integer),
    sa.column("currency", sa.String),
    sa.column("opens", sa.Time),
    sa.column("closes", sa.Time),
    sa.column("timezone", sa.Text),
)

EVERY_ROOM = {
    "currency": "EUR",
    "opens": time(8, 0),
    "closes": time(20, 0),
    "timezone": "Europe/Lisbon",
}


def upgrade() -> None:
    op.bulk_insert(
        rooms,
        [
            {
                "id": "atlas",
                "name": "Atlas",
                "capacity": 8,
                "hourly_rate": 4000,
                **EVERY_ROOM,
            },
            {
                "id": "borealis",
                "name": "Borealis",
                "capacity": 4,
                "hourly_rate": 2400,
                **EVERY_ROOM,
            },
            {
                "id": "cove",
                "name": "Cove",
                "capacity": 12,
                "hourly_rate": 6000,
                **EVERY_ROOM,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        rooms.delete().where(
            rooms.c.id.in_(["atlas", "borealis", "cove"])
        )
    )
