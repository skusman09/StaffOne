"""Add new features - timezone, shifts, locations, leaves, notifications

Revision ID: add_new_features_v2
Revises: 7d79bced2664
Create Date: 2024-12-21

This migration adds:
- timezone column to users
- New columns to checkinouts (shift_type, shift_id, hours_worked, geofencing, admin controls)
- locations table for geofencing
- leaves table for leave management
- notification_preferences table
- notifications table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_new_features_v2'
down_revision = '7d79bced2664'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timezone to users table
    op.add_column('users', sa.Column('timezone', sa.String(), nullable=True, server_default='Asia/Kolkata'))
    op.execute("UPDATE users SET timezone = 'Asia/Kolkata' WHERE timezone IS NULL")
    op.alter_column('users', 'timezone', nullable=False)
    
    # Add new columns to checkinouts table
    op.add_column('checkinouts', sa.Column('shift_type', sa.String(), nullable=True, server_default='regular'))
    op.add_column('checkinouts', sa.Column('shift_id', sa.String(), nullable=True))
    op.add_column('checkinouts', sa.Column('checkout_latitude', sa.Float(), nullable=True))
    op.add_column('checkinouts', sa.Column('checkout_longitude', sa.Float(), nullable=True))
    op.add_column('checkinouts', sa.Column('is_location_valid', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('checkinouts', sa.Column('location_flag_reason', sa.String(), nullable=True))
    op.add_column('checkinouts', sa.Column('hours_worked', sa.Float(), nullable=True))
    op.add_column('checkinouts', sa.Column('is_auto_checkout', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('checkinouts', sa.Column('admin_notes', sa.String(), nullable=True))
    op.add_column('checkinouts', sa.Column('modified_by_admin_id', sa.Integer(), nullable=True))
    
    # Update existing records with defaults
    op.execute("UPDATE checkinouts SET shift_type = 'regular' WHERE shift_type IS NULL")
    op.execute("UPDATE checkinouts SET is_location_valid = true WHERE is_location_valid IS NULL")
    op.execute("UPDATE checkinouts SET is_auto_checkout = false WHERE is_auto_checkout IS NULL")
    
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    
    # Create leaves table
    op.create_table('leaves',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('leave_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('admin_remarks', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leaves_id'), 'leaves', ['id'], unique=False)
    op.create_index(op.f('ix_leaves_user_id'), 'leaves', ['user_id'], unique=False)
    op.create_index(op.f('ix_leaves_start_date'), 'leaves', ['start_date'], unique=False)
    
    # Create notification_preferences table
    op.create_table('notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('email_forgot_checkin', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('email_forgot_checkout', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('email_leave_updates', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_forgot_checkin', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_forgot_checkout', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_leave_updates', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('checkin_reminder_time', sa.String(), nullable=True, server_default="'09:00'"),
        sa.Column('checkout_reminder_time', sa.String(), nullable=True, server_default="'18:00'"),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='unread'),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('link', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop notifications table
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    # Drop notification_preferences table
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    
    # Drop leaves table
    op.drop_index(op.f('ix_leaves_start_date'), table_name='leaves')
    op.drop_index(op.f('ix_leaves_user_id'), table_name='leaves')
    op.drop_index(op.f('ix_leaves_id'), table_name='leaves')
    op.drop_table('leaves')
    
    # Drop locations table
    op.drop_index(op.f('ix_locations_name'), table_name='locations')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    op.drop_table('locations')
    
    # Remove columns from checkinouts
    op.drop_column('checkinouts', 'modified_by_admin_id')
    op.drop_column('checkinouts', 'admin_notes')
    op.drop_column('checkinouts', 'is_auto_checkout')
    op.drop_column('checkinouts', 'hours_worked')
    op.drop_column('checkinouts', 'location_flag_reason')
    op.drop_column('checkinouts', 'is_location_valid')
    op.drop_column('checkinouts', 'checkout_longitude')
    op.drop_column('checkinouts', 'checkout_latitude')
    op.drop_column('checkinouts', 'shift_id')
    op.drop_column('checkinouts', 'shift_type')
    
    # Remove timezone from users
    op.drop_column('users', 'timezone')
