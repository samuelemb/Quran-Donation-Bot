"""initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260308_0001"
down_revision = None
branch_labels = None
depends_on = None


donation_status = postgresql.ENUM("pending", "approved", "rejected", name="donation_status", create_type=False)
payment_provider_type = postgresql.ENUM(
    "mobile_money",
    "bank",
    name="payment_provider_type",
    create_type=False,
)
notification_delivery_status = postgresql.ENUM(
    "pending",
    "sent",
    "failed",
    name="notification_delivery_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("pending", "approved", "rejected", name="donation_status").create(bind, checkfirst=True)
    postgresql.ENUM("mobile_money", "bank", name="payment_provider_type").create(bind, checkfirst=True)
    postgresql.ENUM("pending", "sent", "failed", name="notification_delivery_status").create(bind, checkfirst=True)

    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", payment_provider_type, nullable=False, server_default="bank"),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("account_number", sa.String(length=100), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_payment_method_id", sa.Integer(), nullable=True),
        sa.Column("default_quran_amount", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["default_payment_method_id"], ["payment_methods.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=False)

    op.create_table(
        "donations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("payment_method_id", sa.Integer(), nullable=False),
        sa.Column("quran_amount", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("screenshot_file_id", sa.String(length=255), nullable=False),
        sa.Column("payment_method_name_snapshot", sa.String(length=100), nullable=False),
        sa.Column("payment_provider_type_snapshot", payment_provider_type, nullable=False),
        sa.Column("account_name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("account_number_snapshot", sa.String(length=100), nullable=False),
        sa.Column("payment_instructions_snapshot", sa.Text(), nullable=True),
        sa.Column("status", donation_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["payment_method_id"], ["payment_methods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_donations_user_id", "donations", ["user_id"], unique=False)

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"], unique=False)

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("donation_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=100), nullable=False),
        sa.Column("delivery_status", notification_delivery_status, nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["donation_id"], ["donations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("notification_logs")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_table("feedback")
    op.drop_index("ix_donations_user_id", table_name="donations")
    op.drop_table("donations")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    op.drop_table("payment_methods")
    notification_delivery_status.drop(bind, checkfirst=True)
    payment_provider_type.drop(bind, checkfirst=True)
    donation_status.drop(bind, checkfirst=True)
