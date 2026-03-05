"""initial migration

Revision ID: initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'wallets',
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('balance', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('uuid')
    )
    op.create_index(op.f('ix_wallets_uuid'), 'wallets', ['uuid'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_wallets_uuid'), table_name='wallets')
    op.drop_table('wallets')