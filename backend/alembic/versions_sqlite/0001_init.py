"""Initial schema for SQLite.

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-05 00:00:00.000000

This revision creates the initial schema for the FAS project on a
SQLite backend.  It defines tables for administrators, employees,
stored image files, and reports.  Because SQLite has limited ALTER TABLE
capabilities, Alembic uses batch operations (see ``env.py``) when
modifying existing tables.  However, for initial creation we can use
standard ``op.create_table`` calls.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables and indices for SQLite."""
    # Admins table
    op.create_table(
        'Admins',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('qr_value', sa.String(), nullable=True),
    )
    with op.batch_alter_table('Admins') as batch_op:
        batch_op.create_index(batch_op.f('ix_Admins_first_name'), ['first_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_Admins_last_name'), ['last_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_Admins_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_Admins_qr_value'), ['qr_value'], unique=True)

    # ImageFiles table
    op.create_table(
        'ImageFiles',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False, server_default='application/octet-stream'),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('hash', name='uq_image_files_hash'),
    )
    with op.batch_alter_table('ImageFiles') as batch_op:
        batch_op.create_index(batch_op.f('ix_ImageFiles_hash'), ['hash'], unique=False)

    # Employees table
    op.create_table(
        'Employees',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('qr_value', sa.String(), nullable=True),
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('dismissal_date', sa.DateTime(), nullable=True),
        sa.Column('image_id', sa.Integer(), sa.ForeignKey('ImageFiles.id'), nullable=True),
    )
    with op.batch_alter_table('Employees') as batch_op:
        batch_op.create_index(batch_op.f('ix_Employees_first_name'), ['first_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_Employees_last_name'), ['last_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_Employees_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_Employees_qr_value'), ['qr_value'], unique=True)

    # Define Enum for report status.  SQLite will represent this as a
    # CHECK‑constrained VARCHAR.
    report_status_enum = sa.Enum('OK', 'Error', name='report_status')

    # Reports table
    op.create_table(
        'Reports',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('retention_until', sa.DateTime(), nullable=False),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('Employees.id'), nullable=True),
        sa.Column('status', report_status_enum, nullable=True),
        sa.Column('denial_reason', sa.String(), nullable=True),
    )
    with op.batch_alter_table('Reports') as batch_op:
        batch_op.create_index(batch_op.f('ix_Reports_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_Reports_employee_id'), ['employee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_Reports_status'), ['status'], unique=False)


def downgrade() -> None:
    """Drop all tables and constraints for SQLite."""
    # Drop indexes and tables in reverse order
    with op.batch_alter_table('Reports') as batch_op:
        batch_op.drop_index(batch_op.f('ix_Reports_status'))
        batch_op.drop_index(batch_op.f('ix_Reports_employee_id'))
        batch_op.drop_index(batch_op.f('ix_Reports_created_at'))
    op.drop_table('Reports')

    with op.batch_alter_table('Employees') as batch_op:
        batch_op.drop_index(batch_op.f('ix_Employees_qr_value'))
        batch_op.drop_index(batch_op.f('ix_Employees_email'))
        batch_op.drop_index(batch_op.f('ix_Employees_last_name'))
        batch_op.drop_index(batch_op.f('ix_Employees_first_name'))
    op.drop_table('Employees')

    with op.batch_alter_table('ImageFiles') as batch_op:
        batch_op.drop_index(batch_op.f('ix_ImageFiles_hash'))
    op.drop_table('ImageFiles')

    with op.batch_alter_table('Admins') as batch_op:
        batch_op.drop_index(batch_op.f('ix_Admins_qr_value'))
        batch_op.drop_index(batch_op.f('ix_Admins_email'))
        batch_op.drop_index(batch_op.f('ix_Admins_last_name'))
        batch_op.drop_index(batch_op.f('ix_Admins_first_name'))
    op.drop_table('Admins')