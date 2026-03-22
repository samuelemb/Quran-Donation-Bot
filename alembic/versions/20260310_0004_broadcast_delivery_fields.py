"""broadcast delivery fields"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_0004"
down_revision = "20260310_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("broadcast_messages", sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("broadcast_messages", sa.Column("delivered_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("broadcast_messages", sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("broadcast_messages", sa.Column("failure_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("broadcast_messages", "failure_summary")
    op.drop_column("broadcast_messages", "failed_count")
    op.drop_column("broadcast_messages", "delivered_count")
    op.drop_column("broadcast_messages", "recipient_count")
