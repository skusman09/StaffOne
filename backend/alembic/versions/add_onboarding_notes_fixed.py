"""Add onboarding notes table and notification types - Fixed

Revision ID: add_onboarding_notes_fixed
Revises: 8ae4723bf709
Create Date: 2024-03-18 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_onboarding_notes_fixed'
down_revision = '8ae4723bf709'
branch_labels = None
depends_on = None


def upgrade():
    # Create onboarding_notes table
    op.create_table(
        'onboarding_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_onboarding_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], 'users.id', ),
        sa.ForeignKeyConstraint(['employee_onboarding_id'], 'employee_onboardings.id', ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_onboarding_notes_id'), 'onboarding_notes', ['id'], unique=False)
    
    # Update notification type enum (this would need manual handling in production)
    # For now, we'll add new types as strings in existing records


def downgrade():
    # Drop onboarding_notes table
    op.drop_index(op.f('ix_onboarding_notes_id'), table_name='onboarding_notes')
    op.drop_table('onboarding_notes')
