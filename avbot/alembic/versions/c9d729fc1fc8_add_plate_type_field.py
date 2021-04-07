"""add_plate_type_field

Revision ID: c9d729fc1fc8
Revises: f91610c45c9e
Create Date: 2021-04-08 00:32:56.844725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d729fc1fc8'
down_revision = 'f91610c45c9e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('search_query', sa.Column('num_type', sa.String(length=32), nullable=True))
    op.execute("UPDATE search_query SET num_type = 'ru'")
    op.alter_column('search_query', 'num_type', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('search_query', 'num_type')
    # ### end Alembic commands ###
