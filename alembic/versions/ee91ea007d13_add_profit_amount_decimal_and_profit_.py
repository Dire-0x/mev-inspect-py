"""Add profit_amount_decimal and profit_amount_usd columns to sandwiches table

Revision ID: ee91ea007d13
Revises: 5c5375de15fd
Create Date: 2022-02-22 17:09:47.428857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee91ea007d13'
down_revision = '5c5375de15fd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sandwiches", sa.Column("profit_amount_decimal", sa.Numeric, nullable=True))
    op.add_column("sandwiches", sa.Column("profit_amount_usd", sa.Numeric, nullable=True))


def downgrade():
    op.drop_column("sandwiches", "profit_amount_decimal")
    op.drop_column("sandwiches", "profit_amount_usd")
