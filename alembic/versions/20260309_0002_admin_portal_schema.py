"""admin portal schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260309_0002"
down_revision = "20260308_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="super_admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=False)

    op.create_table(
        "broadcast_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "portal_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_name", sa.String(length=255), nullable=False, server_default="Quran Donation"),
        sa.Column("support_contact", sa.String(length=255), nullable=False, server_default="support@qurandonation.org"),
        sa.Column("telegram_channel_link", sa.String(length=255), nullable=True),
        sa.Column("default_language", sa.String(length=50), nullable=False, server_default="English"),
        sa.Column(
            "system_timezone",
            sa.String(length=100),
            nullable=False,
            server_default="(GMT+03:00) East Africa Time - Addis Ababa",
        ),
        sa.Column("price_per_quran_birr", sa.Integer(), nullable=False, server_default="450"),
        sa.Column("default_donation_amount", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("minimum_donation_amount", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("monthly_subscriptions_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notify_new_donations", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_late_payments", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_pending_approvals", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("portal_settings")
    op.drop_table("broadcast_messages")
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
