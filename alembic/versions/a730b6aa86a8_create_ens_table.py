"""Create ens table
Revision ID: a730b6aa86a8
Revises: ee91ea007d13
Create Date: 2022-03-11 18:40:59.038326

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a730b6aa86a8"
down_revision = "ee91ea007d13"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ens",
        sa.Column("ens_name", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(256), nullable=True),
        sa.Column("address", sa.String(256), nullable=True),
        sa.Column("twitter", sa.Text(), nullable=True),
        sa.Column("twitter_handle", sa.String(1024), nullable=True),
        sa.Column("github", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("discord", sa.Text(), nullable=True),
        sa.Column("reddit", sa.Text(), nullable=True),
        sa.Column("telegram", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("ens_name"),
    )


def downgrade():
    op.drop_table("ens")
