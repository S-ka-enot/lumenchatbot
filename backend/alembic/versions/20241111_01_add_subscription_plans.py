"""add subscription plans and links

Revision ID: 20241111_01_add_subscription_plans
Revises:
Create Date: 2025-11-11 15:55:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


def _table_has_column(inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


# revision identifiers, used by Alembic.
revision = "20241111_01_add_subscription_plans"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("subscription_plans"):
        op.create_table(
            "subscription_plans",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("price_currency", sa.String(length=10), nullable=False, server_default="RUB"),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("bot_id", "slug", name="uq_subscription_plan_bot_slug"),
        )

    if not inspector.has_table("subscription_plan_channels"):
        op.create_table(
            "subscription_plan_channels",
            sa.Column(
                "plan_id",
                sa.Integer(),
                sa.ForeignKey("subscription_plans.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "channel_id",
                sa.Integer(),
                sa.ForeignKey("channels.id", ondelete="CASCADE"),
                primary_key=True,
            ),
        )

    if inspector.has_table("payments") and not _table_has_column(inspector, "payments", "plan_id"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.add_column(sa.Column("plan_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_payments_plan_id",
                "subscription_plans",
                ["plan_id"],
                ["id"],
                ondelete="SET NULL",
            )

    if inspector.has_table("subscriptions") and not _table_has_column(inspector, "subscriptions", "plan_id"):
        with op.batch_alter_table("subscriptions", schema=None) as batch_op:
            batch_op.add_column(sa.Column("plan_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_subscriptions_plan_id",
                "subscription_plans",
                ["plan_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("subscriptions") and _table_has_column(inspector, "subscriptions", "plan_id"):
        with op.batch_alter_table("subscriptions", schema=None) as batch_op:
            batch_op.drop_constraint("fk_subscriptions_plan_id", type_="foreignkey")
            batch_op.drop_column("plan_id")

    if inspector.has_table("payments") and _table_has_column(inspector, "payments", "plan_id"):
        with op.batch_alter_table("payments", schema=None) as batch_op:
            batch_op.drop_constraint("fk_payments_plan_id", type_="foreignkey")
            batch_op.drop_column("plan_id")

    if inspector.has_table("subscription_plan_channels"):
        op.drop_table("subscription_plan_channels")

    if inspector.has_table("subscription_plans"):
        op.drop_table("subscription_plans")


