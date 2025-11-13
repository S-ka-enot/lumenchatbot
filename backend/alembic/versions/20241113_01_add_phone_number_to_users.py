"""add phone_number and birthday to users

Revision ID: 20241113_01
Revises: 20241112_01
Create Date: 2024-11-13 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241113_01"
down_revision: Union[str, None] = "20241112_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add phone_number column to users table
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    
    # Add birthday column to users table
    op.add_column('users', sa.Column('birthday', sa.Date(), nullable=True))
    
    # Add subscription_end column to users table
    op.add_column('users', sa.Column('subscription_end', sa.DateTime(timezone=True), nullable=True))
    
    # Add unique constraint for bot_id + phone_number
    try:
        op.create_unique_constraint('uq_users_bot_phone', 'users', ['bot_id', 'phone_number'])
    except Exception:
        pass  # Constraint might already exist


def downgrade() -> None:
    # Remove unique constraint
    try:
        op.drop_constraint('uq_users_bot_phone', 'users', type_='unique')
    except Exception:
        pass
    
    # Remove columns
    op.drop_column('users', 'subscription_end')
    op.drop_column('users', 'birthday')
    op.drop_column('users', 'phone_number')

