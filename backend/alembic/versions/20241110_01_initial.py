"""Initial migration - create base tables

Revision ID: 20241110_01
Revises: 
Create Date: 2024-11-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241110_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create bots table
    if not inspector.has_table("bots"):
        op.create_table(
            "bots",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column("telegram_bot_token_encrypted", sa.LargeBinary(), nullable=True),
            sa.Column("webhook_url", sa.String(length=512), nullable=True),
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Moscow"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # Create users table
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("telegram_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("first_name", sa.String(length=255), nullable=True),
            sa.Column("last_name", sa.String(length=255), nullable=True),
            sa.Column("language_code", sa.String(length=10), nullable=True),
            sa.Column("is_bot", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("bot_id", "telegram_id", name="uq_users_bot_telegram_id"),
        )

    # Create channels table  
    if not inspector.has_table("channels"):
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
        )

    # Create payment_provider_credentials table
    if not inspector.has_table("payment_provider_credentials"):
        op.create_table(
            "payment_provider_credentials",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("provider", sa.String(length=64), nullable=False),
            sa.Column("shop_id_encrypted", sa.LargeBinary(), nullable=True),
            sa.Column("secret_key_encrypted", sa.LargeBinary(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("bot_id", "provider", name="uq_payment_provider_credentials_bot_provider"),
        )

    # Create payments table
    if not inspector.has_table("payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("external_id", sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column("provider", sa.String(length=64), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("payment_url", sa.String(length=512), nullable=True),
            sa.Column("confirmation_token", sa.String(length=255), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # Create subscriptions table
    if not inspector.has_table("subscriptions"):
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
            sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "channel_id", name="uq_subscriptions_user_channel"),
        )

    # Create promo_codes table
    if not inspector.has_table("promo_codes"):
        op.create_table(
            "promo_codes",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("code", sa.String(length=100), nullable=False, unique=True, index=True),
            sa.Column("discount_type", sa.String(length=20), nullable=False),
            sa.Column("discount_value", sa.Numeric(12, 2), nullable=False),
            sa.Column("max_uses", sa.Integer(), nullable=True),
            sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # Create bot_messages table
    if not inspector.has_table("bot_messages"):
        op.create_table(
            "bot_messages",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("message_key", sa.String(length=100), nullable=False),
            sa.Column("message_text", sa.Text(), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=False, server_default="ru"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("bot_id", "message_key", "language", name="uq_bot_messages_bot_key_lang"),
        )

    # Create scheduled_broadcasts table
    if not inspector.has_table("scheduled_broadcasts"):
        op.create_table(
            "scheduled_broadcasts",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("message_text", sa.Text(), nullable=False),
            sa.Column("audience", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("total_recipients", sa.Integer(), nullable=True),
            sa.Column("successful_sends", sa.Integer(), nullable=True),
            sa.Column("failed_sends", sa.Integer(), nullable=True),
            sa.Column("parse_mode", sa.String(length=20), nullable=True),
            sa.Column("disable_preview", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # Create access_logs table
    if not inspector.has_table("access_logs"):
        op.create_table(
            "access_logs",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("result", sa.String(length=50), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # Create admins table
    if not inspector.has_table("admins"):
        op.create_table(
            "admins",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("username", sa.String(length=150), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("telegram_id", sa.Integer(), nullable=True),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop tables in reverse order (respecting foreign key constraints)
    tables = [
        "admins",
        "access_logs",
        "scheduled_broadcasts",
        "bot_messages",
        "promo_codes",
        "subscriptions",
        "payments",
        "payment_provider_credentials",
        "channels",
        "users",
        "bots",
    ]

    for table in tables:
        if inspector.has_table(table):
            op.drop_table(table)
