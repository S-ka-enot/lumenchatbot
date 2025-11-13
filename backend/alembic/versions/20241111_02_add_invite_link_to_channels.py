"""add invite_link to channels

Revision ID: 20241111_02
Revises: 20241111_01
Create Date: 2024-11-11 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20241111_02'
down_revision: Union[str, None] = '20241111_01_add_subscription_plans'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # If channels table does not exist (fresh DB), skip this migration step.
    if not inspector.has_table("channels"):
        return

    columns = {col["name"] for col in inspector.get_columns("channels")}
    if "invite_link" not in columns:
        op.add_column('channels', sa.Column('invite_link', sa.String(length=512), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # If channels table does not exist, nothing to downgrade here.
    if not inspector.has_table("channels"):
        return

    columns = {col["name"] for col in inspector.get_columns("channels")}
    if "invite_link" in columns:
        op.drop_column('channels', 'invite_link')

