"""Add average_sol_score to accommodations

Revision ID: 004
Revises: 003
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add average_sol_score column to accommodations table
    op.add_column('accommodations',
                  sa.Column('average_sol_score', sa.Float(), nullable=True))


def downgrade():
    # Remove average_sol_score column from accommodations table
    op.drop_column('accommodations', 'average_sol_score')
