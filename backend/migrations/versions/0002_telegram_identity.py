"""Track Telegram chats and webhook updates."""

from alembic import op
import sqlalchemy as sa

revision = "0002_telegram_identity"
down_revision = "0001_initial_crm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("telegram_chat_id", sa.BigInteger()))
    op.create_unique_constraint("uq_clients_telegram_chat_id", "clients", ["telegram_chat_id"])
    op.add_column("communication_logs", sa.Column("telegram_update_id", sa.BigInteger()))
    op.create_unique_constraint(
        "uq_communication_logs_telegram_update_id", "communication_logs", ["telegram_update_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_communication_logs_telegram_update_id", "communication_logs", type_="unique")
    op.drop_column("communication_logs", "telegram_update_id")
    op.drop_constraint("uq_clients_telegram_chat_id", "clients", type_="unique")
    op.drop_column("clients", "telegram_chat_id")
