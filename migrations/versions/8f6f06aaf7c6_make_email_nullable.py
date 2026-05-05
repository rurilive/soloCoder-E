"""make email nullable

Revision ID: 8f6f06aaf7c6
Revises: 
Create Date: 2026-05-04 18:48:24.100206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '8f6f06aaf7c6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'email',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=120),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'email',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=120),
               nullable=False)
