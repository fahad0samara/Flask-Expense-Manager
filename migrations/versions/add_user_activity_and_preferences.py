"""add user activity and preferences

Revision ID: add_user_activity_and_preferences
Revises: update_null_created_at
Create Date: 2024-01-09 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_activity_and_preferences'
down_revision = 'update_null_created_at'
branch_labels = None
depends_on = None


def upgrade():
    # Add activity tracking columns
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('last_active', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('login_count', sa.Integer(), nullable=True, server_default='0'))
    
    # Add preference columns
    op.add_column('user', sa.Column('default_currency', sa.String(3), nullable=True, server_default='USD'))
    op.add_column('user', sa.Column('language', sa.String(5), nullable=True, server_default='en_US'))
    op.add_column('user', sa.Column('date_format', sa.String(20), nullable=True, server_default='MM/DD/YYYY'))


def downgrade():
    # Remove all added columns
    op.drop_column('user', 'date_format')
    op.drop_column('user', 'language')
    op.drop_column('user', 'default_currency')
    op.drop_column('user', 'login_count')
    op.drop_column('user', 'last_active')
    op.drop_column('user', 'last_login')
