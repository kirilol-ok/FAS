"""Initial schema for PostgreSQL.

Revision ID: 0001_init
Revises: 
Create Date: 2026-01-05 00:00:00.000000

This revision creates the initial schema for the FAS project on a
PostgreSQL backend.  It defines tables for administrators, employees,
stored image files, and reports.  The corresponding SQLite migration can
be found in ``versions_sqlite/0001_init.py``.
"""

from typing import Sequence, Union
from sqlalchemy.dialects import postgresql

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
REPORT_STATUS_ENUM = postgresql.ENUM("OK", "Error", name="report_status", create_type=False)


def upgrade() -> None:
    """Create initial tables and constraints."""
    # Create enumeration type for report status
    report_status_enum = sa.Enum('OK', 'Error', name='report_status')
    report_status_enum.create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("OK", "Error", name="report_status").create(op.get_bind(), checkfirst=True)

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
    op.create_index(op.f('ix_Admins_first_name'), 'Admins', ['first_name'], unique=False)
    op.create_index(op.f('ix_Admins_last_name'), 'Admins', ['last_name'], unique=False)
    op.create_index(op.f('ix_Admins_email'), 'Admins', ['email'], unique=True)
    op.create_index(op.f('ix_Admins_qr_value'), 'Admins', ['qr_value'], unique=True)

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
    op.create_index(op.f('ix_ImageFiles_hash'), 'ImageFiles', ['hash'], unique=False)

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
    op.create_index(op.f('ix_Employees_first_name'), 'Employees', ['first_name'], unique=False)
    op.create_index(op.f('ix_Employees_last_name'), 'Employees', ['last_name'], unique=False)
    op.create_index(op.f('ix_Employees_email'), 'Employees', ['email'], unique=True)
    op.create_index(op.f('ix_Employees_qr_value'), 'Employees', ['qr_value'], unique=True)

    # Reports table
    op.create_table(
        'Reports',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('retention_until', sa.DateTime(), nullable=False),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('Employees.id'), nullable=True),
        sa.Column("status", REPORT_STATUS_ENUM, nullable=True),
        sa.Column('denial_reason', sa.String(), nullable=True),
    )
    op.create_index(op.f('ix_Reports_created_at'), 'Reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_Reports_employee_id'), 'Reports', ['employee_id'], unique=False)
    op.create_index(op.f('ix_Reports_status'), 'Reports', ['status'], unique=False)


def downgrade() -> None:
    """Drop all tables and the enumeration type."""
    # Drop indexes and tables in reverse order of creation
    op.drop_index(op.f('ix_Reports_status'), table_name='Reports')
    op.drop_index(op.f('ix_Reports_employee_id'), table_name='Reports')
    op.drop_index(op.f('ix_Reports_created_at'), table_name='Reports')
    op.drop_table('Reports')

    op.drop_index(op.f('ix_Employees_qr_value'), table_name='Employees')
    op.drop_index(op.f('ix_Employees_email'), table_name='Employees')
    op.drop_index(op.f('ix_Employees_last_name'), table_name='Employees')
    op.drop_index(op.f('ix_Employees_first_name'), table_name='Employees')
    op.drop_table('Employees')

    op.drop_index(op.f('ix_ImageFiles_hash'), table_name='ImageFiles')
    op.drop_table('ImageFiles')

    op.drop_index(op.f('ix_Admins_qr_value'), table_name='Admins')
    op.drop_index(op.f('ix_Admins_email'), table_name='Admins')
    op.drop_index(op.f('ix_Admins_last_name'), table_name='Admins')
    op.drop_index(op.f('ix_Admins_first_name'), table_name='Admins')
    op.drop_table('Admins')

    # Drop enumeration type
    postgresql.ENUM("OK", "Error", name="report_status").drop(op.get_bind(), checkfirst=True)
