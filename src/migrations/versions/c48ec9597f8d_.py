"""empty message

Revision ID: c48ec9597f8d
Revises: 9dfd2228f643
Create Date: 2023-01-30 19:44:14.321901

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c48ec9597f8d'
down_revision = '9dfd2228f643'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('celery_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_username', sa.String(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_celery_task_owner_username_user'), 'user', ['owner_username'], ['username'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('celery_task', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_celery_task_owner_username_user'), type_='foreignkey')
        batch_op.drop_column('owner_username')

    # ### end Alembic commands ###
