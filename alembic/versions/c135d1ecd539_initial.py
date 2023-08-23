"""initial

Revision ID: c135d1ecd539
Revises: 
Create Date: 2023-08-20 17:37:34.044829

"""
import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c135d1ecd539'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, index=True),
        sa.Column("email", sa.String(), index=True, unique=True),
        sa.Column("username", sa.String(), index=True, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, index=True),
        sa.Column("check_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
    )
    op.create_table(
        "checks",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("payment_type", sa.String(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("payment_amount", sa.Float(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("rest", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.datetime.utcnow()),
    )
    op.create_foreign_key("products_checks_fk", source_table="products", referent_table="checks",
                          local_cols=["check_id"], remote_cols=["id"], ondelete="CASCADE")
    op.create_foreign_key("checks_users_fk", source_table="checks", referent_table="users",
                          local_cols=["user_id"], remote_cols=["id"], ondelete="CASCADE")


def downgrade():
    op.drop_table("products")
    op.drop_table("checks")
    op.drop_table("users")
