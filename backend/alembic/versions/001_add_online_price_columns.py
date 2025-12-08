"""Add online_price to accommodation_dates and today_accommodation_info

Revision ID: 001
Revises:
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add online_price column to accommodation_dates table
    op.add_column('accommodation_dates',
                  sa.Column('online_price', sa.Float(), nullable=True))

    # Add online_price column to today_accommodation_info table
    op.add_column('today_accommodation_info',
                  sa.Column('online_price', sa.Float(), nullable=True))


def downgrade():
    # Remove online_price column from today_accommodation_info table
    op.drop_column('today_accommodation_info', 'online_price')

    # Remove online_price column from accommodation_dates table
    op.drop_column('accommodation_dates', 'online_price')
