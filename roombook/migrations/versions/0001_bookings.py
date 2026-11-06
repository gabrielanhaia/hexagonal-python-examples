"""Rooms, bookings with no double booking, outbox, inbox."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TSTZRANGE

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "rooms",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False),
        sa.Column("hourly_rate", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("opens", sa.Time, nullable=False),
        sa.Column("closes", sa.Time, nullable=False),
        sa.Column("timezone", sa.Text, nullable=False),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "room_id",
            sa.Text,
            sa.ForeignKey("rooms.id"),
            nullable=False,
        ),
        sa.Column("member_id", sa.Text, nullable=False),
        sa.Column("slot", TSTZRANGE, nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "held_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("payment_id", sa.Text),
    )
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_no_overlap
        EXCLUDE USING gist (room_id WITH =, slot WITH &&)
        WHERE (status IN ('HELD', 'CONFIRMED'))
        """
    )
    op.create_table(
        "outbox",
        sa.Column(
            "id", sa.BigInteger, sa.Identity(), primary_key=True
        ),
        sa.Column("topic", sa.Text, nullable=False),
        sa.Column("key", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "outbox_unpublished",
        "outbox",
        ["id"],
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_table(
        "processed_messages",
        sa.Column("message_id", sa.Text, primary_key=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("processed_messages")
    op.drop_table("outbox")
    op.drop_table("bookings")
    op.drop_table("rooms")
