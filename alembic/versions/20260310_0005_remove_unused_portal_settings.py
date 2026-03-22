"""remove unused portal settings"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_0005"
down_revision = "20260310_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("portal_settings", "monthly_subscriptions_enabled")
    op.drop_column("portal_settings", "default_donation_amount")


def downgrade() -> None:
    op.add_column(
        "portal_settings",
        sa.Column("default_donation_amount", sa.Integer(), nullable=False, server_default="900"),
    )
    op.add_column(
        "portal_settings",
        sa.Column("monthly_subscriptions_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
