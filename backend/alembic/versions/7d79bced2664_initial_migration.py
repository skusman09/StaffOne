"""Initial migration - Create users and checkinouts tables

Revision ID: 7d79bced2664
Revises: 
Create Date: 2025-12-19 13:07:26.620205

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7d79bced2664'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create Role enum type for PostgreSQL
    op.execute("CREATE TYPE role AS ENUM ('admin', 'employee')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', postgresql.ENUM('admin', 'employee', name='role', create_type=False), nullable=False, server_default='employee'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create checkinouts table
    op.create_table(
        'checkinouts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(), nullable=False),
        sa.Column('check_out_time', sa.DateTime(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('device_info', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for checkinouts table
    op.create_index(op.f('ix_checkinouts_id'), 'checkinouts', ['id'], unique=False)
    op.create_index(op.f('ix_checkinouts_user_id'), 'checkinouts', ['user_id'], unique=False)
    op.create_index(op.f('ix_checkinouts_check_in_time'), 'checkinouts', ['check_in_time'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_checkinouts_check_in_time'), table_name='checkinouts')
    op.drop_index(op.f('ix_checkinouts_user_id'), table_name='checkinouts')
    op.drop_index(op.f('ix_checkinouts_id'), table_name='checkinouts')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    
    # Drop tables
    op.drop_table('checkinouts')
    op.drop_table('users')
    
    # Drop enum type
    op.execute('DROP TYPE role')
