"""add address verification and is_admin

Revision ID: 2a1b3c4d5e6f
Revises: 8f6f06aaf7c6
Create Date: 2026-05-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = '2a1b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '8f6f06aaf7c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
    
    op.create_table('address_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('document_image_url', sa.String(length=255), nullable=True),
        sa.Column('property_address', sa.String(length=255), nullable=True),
        sa.Column('property_owner_name', sa.String(length=100), nullable=True),
        sa.Column('id_card_number', sa.String(length=20), nullable=True),
        sa.Column('id_card_name', sa.String(length=100), nullable=True),
        sa.Column('id_card_address', sa.String(length=255), nullable=True),
        sa.Column('id_card_front_url', sa.String(length=255), nullable=True),
        sa.Column('id_card_back_url', sa.String(length=255), nullable=True),
        sa.Column('additional_documents', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('address_verifications')
    op.drop_column('users', 'is_admin')
