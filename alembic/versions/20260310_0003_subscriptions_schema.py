"""subscriptions schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260310_0003"
down_revision = "20260309_0002"
branch_labels = None
depends_on = None


subscription_status_enum = postgresql.ENUM(
    "active",
    "overdue",
    "paused",
    "cancelled",
    name="subscription_status",
)

subscription_status_column_enum = postgresql.ENUM(
    "active",
    "overdue",
    "paused",
    "cancelled",
    name="subscription_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    subscription_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("payment_method_id", sa.Integer(), nullable=True),
        sa.Column("last_donation_id", sa.Integer(), nullable=True),
        sa.Column("quran_amount", sa.Integer(), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", subscription_status_column_enum, nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_payment_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["last_donation_id"], ["donations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO subscriptions (
                user_id,
                payment_method_id,
                last_donation_id,
                quran_amount,
                monthly_amount,
                status,
                started_at,
                next_payment_due_at,
                last_paid_at
            )
            SELECT
                latest.user_id,
                latest.payment_method_id,
                latest.id,
                latest.quran_amount,
                latest.total_amount,
                CASE
                    WHEN latest.created_at + interval '30 days' < now() THEN 'overdue'::subscription_status
                    ELSE 'active'::subscription_status
                END,
                latest.created_at,
                latest.created_at + interval '30 days',
                latest.created_at
            FROM (
                SELECT
                    d.*,
                    ROW_NUMBER() OVER (PARTITION BY d.user_id ORDER BY d.created_at DESC) AS rn
                FROM donations d
                WHERE d.status = 'approved'
            ) AS latest
            WHERE latest.rn = 1
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    subscription_status_enum.drop(op.get_bind(), checkfirst=True)
