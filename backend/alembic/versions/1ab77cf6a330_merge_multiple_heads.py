"""Merge multiple heads

Revision ID: 1ab77cf6a330
Revises: add_new_features_v2, fe7d69513d1e
Create Date: 2025-12-21 22:07:31.039754

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ab77cf6a330'
down_revision = ('add_new_features_v2', 'fe7d69513d1e')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

