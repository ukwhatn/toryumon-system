"""fix_fk

Revision ID: 38cafa5eafd1
Revises: c48ef6ba999d
Create Date: 2024-06-02 12:12:11.206897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38cafa5eafd1'
down_revision: Union[str, None] = 'c48ef6ba999d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('progress_ask_contents', 'progress_ask_id')
    op.drop_column('progress_ask_roles', 'progress_ask_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('progress_ask_roles', sa.Column('progress_ask_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('progress_ask_contents', sa.Column('progress_ask_id', sa.INTEGER(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###