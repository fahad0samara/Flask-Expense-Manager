"""Add notification preferences to User model

Revision ID: 98e4b53e0cf9
Revises: 8ad665ba7ea5
Create Date: 2024-11-24 07:09:59.300241

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98e4b53e0cf9'
down_revision = '8ad665ba7ea5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_notifications', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('expense_reminders', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('settlement_notifications', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('settlement_notifications')
        batch_op.drop_column('expense_reminders')
        batch_op.drop_column('email_notifications')

    # ### end Alembic commands ###
