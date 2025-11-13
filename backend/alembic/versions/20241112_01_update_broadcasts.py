"""update broadcasts table with new fields

Revision ID: 20241112_01
Revises: 20241111_02
Create Date: 2024-11-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def _get_columns(inspector, table_name: str) -> set[str]:
    if not inspector.has_table(table_name):
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}

# revision identifiers, used by Alembic.
revision: str = '20241112_01'
down_revision: Union[str, None] = '20241111_02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind else None
    inspector = sa.inspect(bind)
    columns = _get_columns(inspector, 'scheduled_broadcasts')

    if 'channel_id' not in columns:
        op.add_column('scheduled_broadcasts', sa.Column('channel_id', sa.Integer(), nullable=True))
        if dialect_name != 'sqlite':
            op.create_foreign_key(
                'fk_scheduled_broadcasts_channel_id',
                'scheduled_broadcasts',
                'channels',
                ['channel_id'],
                ['id'],
                ondelete='SET NULL'
            )

    if 'message_title' not in columns:
        op.add_column('scheduled_broadcasts', sa.Column('message_title', sa.String(length=255), nullable=True))

    if 'parse_mode' not in columns:
        op.add_column('scheduled_broadcasts', sa.Column('parse_mode', sa.String(length=32), nullable=True, server_default='None'))
        op.execute("UPDATE scheduled_broadcasts SET parse_mode = 'None' WHERE parse_mode IS NULL")

    if 'user_ids' not in columns:
        user_ids_type = sa.JSON()
        if dialect_name == 'postgresql':
            user_ids_type = postgresql.JSONB(astext_type=sa.Text())
        op.add_column('scheduled_broadcasts', sa.Column('user_ids', user_ids_type, nullable=True))

    if 'birthday_only' not in columns:
        op.add_column('scheduled_broadcasts', sa.Column('birthday_only', sa.Boolean(), nullable=False, server_default='false'))

    if 'media_files' not in columns:
        media_type = sa.JSON()
        if dialect_name == 'postgresql':
            media_type = postgresql.JSONB(astext_type=sa.Text())
        op.add_column('scheduled_broadcasts', sa.Column('media_files', media_type, nullable=True))

    if 'status' in columns:
        op.execute("UPDATE scheduled_broadcasts SET status = 'draft' WHERE status = 'pending'")
        if dialect_name != 'sqlite':
            op.alter_column('scheduled_broadcasts', 'status', server_default='draft')


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind else None
    inspector = sa.inspect(bind)
    columns = _get_columns(inspector, 'scheduled_broadcasts')

    if 'media_files' in columns:
        op.drop_column('scheduled_broadcasts', 'media_files')

    if 'birthday_only' in columns:
        op.drop_column('scheduled_broadcasts', 'birthday_only')

    if 'user_ids' in columns:
        op.drop_column('scheduled_broadcasts', 'user_ids')

    if 'parse_mode' in columns:
        op.drop_column('scheduled_broadcasts', 'parse_mode')

    if 'message_title' in columns:
        op.drop_column('scheduled_broadcasts', 'message_title')

    if 'channel_id' in columns:
        if dialect_name != 'sqlite':
            op.drop_constraint('fk_scheduled_broadcasts_channel_id', 'scheduled_broadcasts', type_='foreignkey')
        op.drop_column('scheduled_broadcasts', 'channel_id')

    if 'status' in columns and dialect_name != 'sqlite':
        op.alter_column('scheduled_broadcasts', 'status', server_default='pending')

