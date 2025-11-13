"""create channels table

Revision ID: 20251113_01
Revises: 20241112_01
Create Date: 2025-11-13 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251113_01"
down_revision: Union[str, None] = "20241112_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("channels"):
        return

    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("channel_name", sa.String(length=255), nullable=False),
        sa.Column("channel_username", sa.String(length=255), nullable=True),
        sa.Column("invite_link", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requires_subscription", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("member_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("bot_id", "channel_id", name="uq_channels_bot_channel_id"),
        sa.UniqueConstraint("bot_id", "channel_username", name="uq_channels_bot_username"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("channels"):
        return

    op.drop_table("channels")

