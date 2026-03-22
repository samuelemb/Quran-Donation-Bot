"""donation plans and reminders"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260310_0006"
down_revision = "20260310_0005"
branch_labels = None
depends_on = None


donation_plan_type_enum = postgresql.ENUM(
    "one_time",
    "monthly",
    "three_month",
    name="donation_plan_type",
)

donation_plan_type_column_enum = postgresql.ENUM(
    "one_time",
    "monthly",
    "three_month",
    name="donation_plan_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    donation_plan_type_enum.create(bind, checkfirst=True)

    op.add_column(
        "donations",
        sa.Column("plan_type", donation_plan_type_column_enum, nullable=False, server_default="one_time"),
    )

    op.add_column(
        "subscriptions",
        sa.Column("plan_type", donation_plan_type_column_enum, nullable=False, server_default="monthly"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("billing_interval_days", sa.Integer(), nullable=False, server_default="30"),
    )

    op.execute(
        sa.text(
            """
            UPDATE subscriptions
            SET plan_type = 'monthly'::donation_plan_type,
                billing_interval_days = 30
            """
        )
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "billing_interval_days")
    op.drop_column("subscriptions", "plan_type")
    op.drop_column("donations", "plan_type")
    donation_plan_type_enum.drop(op.get_bind(), checkfirst=True)
