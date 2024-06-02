"""add_ch

Revision ID: bc8c6dd266e8
Revises: 61cd58709387
Create Date: 2024-06-02 12:22:29.134318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc8c6dd266e8'
down_revision: Union[str, None] = '61cd58709387'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('progress_asks', sa.Column('ask_channel_id', sa.BigInteger(), nullable=False))
    op.add_column('progress_asks', sa.Column('summary_channel_id', sa.BigInteger(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('progress_asks', 'summary_channel_id')
    op.drop_column('progress_asks', 'ask_channel_id')
    # ### end Alembic commands ###