"""Add transaction_eoa column to swaps

Revision ID: 3b4b1fa3619e
Revises: 09e3347d23e3
Create Date: 2022-03-12 01:04:53.414069

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3b4b1fa3619e"
down_revision = "a730b6aa86a8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("swaps", sa.Column("transaction_eoa", sa.String(256), nullable=True))


def downgrade():
    op.drop_column("swaps", "transaction_eoa")
