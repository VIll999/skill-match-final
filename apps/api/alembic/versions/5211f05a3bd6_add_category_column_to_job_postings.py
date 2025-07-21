"""add_category_column_to_job_postings

Revision ID: 5211f05a3bd6
Revises: 5a874c6f39b9
Create Date: 2025-07-19 21:04:49.111411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5211f05a3bd6'
down_revision = '5a874c6f39b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category column to job_postings table
    op.add_column('job_postings', sa.Column('category', sa.String(length=100), nullable=True))
    op.create_index('ix_job_postings_category', 'job_postings', ['category'])


def downgrade() -> None:
    # Remove category column and index
    op.drop_index('ix_job_postings_category', table_name='job_postings')
    op.drop_column('job_postings', 'category')