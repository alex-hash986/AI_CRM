"""Create the initial CRM tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_crm"
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "pipeline_stages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("pipeline_id", sa.Integer, sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("color", sa.String(32), nullable=False),
        sa.Column("is_won", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("is_lost", sa.Boolean, server_default=sa.false(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("pipeline_id", "order", name="uq_pipeline_stages_pipeline_order"),
        sa.CheckConstraint('"order" >= 0', name="ck_pipeline_stages_order"),
        sa.CheckConstraint("NOT (is_won AND is_lost)", name="ck_pipeline_stages_outcome"),
    )
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255)),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(64)),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("custom_fields", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("budget", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("stage_id", sa.Integer, sa.ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ai_score", sa.Integer),
        sa.Column("ai_win_probability", sa.Float),
        sa.Column("ai_next_step", sa.Text),
        sa.Column("ai_risk_assessment", sa.Text),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.CheckConstraint("ai_score BETWEEN 0 AND 100", name="ck_deals_ai_score"),
        sa.CheckConstraint("ai_win_probability BETWEEN 0 AND 1", name="ck_deals_ai_win_probability"),
    )
    op.create_index("ix_deals_stage_id", "deals", ["stage_id"])
    op.create_index("ix_deals_client_id", "deals", ["client_id"])
    op.create_table(
        "communication_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("deal_id", sa.Integer, sa.ForeignKey("deals.id", ondelete="SET NULL")),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("ai_summary", sa.Text),
        *timestamps(),
        sa.CheckConstraint(
            "channel IN ('email', 'telegram', 'call', 'note')",
            name="ck_communication_logs_channel",
        ),
        sa.CheckConstraint(
            "direction IN ('inbound', 'outbound')", name="ck_communication_logs_direction"
        ),
    )
    op.create_index("ix_communication_logs_deal_id", "communication_logs", ["deal_id"])
    op.create_index("ix_communication_logs_client_id", "communication_logs", ["client_id"])


def downgrade() -> None:
    op.drop_table("communication_logs")
    op.drop_table("deals")
    op.drop_table("clients")
    op.drop_table("pipeline_stages")
    op.drop_table("pipelines")
