"""Add buyer_name

Revision ID: f9359f806bff
Revises: c135d1ecd539
Create Date: 2023-08-21 16:19:01.156231

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9359f806bff'
down_revision = 'c135d1ecd539'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("checks", sa.Column("buyer_name", sa.String(), nullable=False, server_default="ФОП Джонсонюк Борис"))


def downgrade() -> None:
    op.drop_column("checks", "buyer_name")
