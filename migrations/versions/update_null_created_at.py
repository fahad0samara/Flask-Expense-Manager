"""update null created_at

Revision ID: update_null_created_at
Revises: 98e4b53e0cf9
Create Date: 2024-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'update_null_created_at'
down_revision = '98e4b53e0cf9'  # Set to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Get connection
    conn = op.get_bind()
    
    # Update users with NULL created_at
    conn.execute(sa.text(
        "UPDATE user SET created_at = :now WHERE created_at IS NULL"
    ), {"now": datetime.utcnow()})


def downgrade():
    # No downgrade necessary
    pass
