"""Add sol_score to accommodation_dates and today_accommodation_info

Revision ID: 003
Revises: 002
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add sol_score column to accommodation_dates table
    op.add_column('accommodation_dates',
                  sa.Column('sol_score', sa.Float(), nullable=True))

    # Add sol_score column to today_accommodation_info table
    op.add_column('today_accommodation_info',
                  sa.Column('sol_score', sa.Float(), nullable=True))


def downgrade():
    # Remove sol_score column from today_accommodation_info table
    op.drop_column('today_accommodation_info', 'sol_score')

    # Remove sol_score column from accommodation_dates table
    op.drop_column('accommodation_dates', 'sol_score')
