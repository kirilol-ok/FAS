"""store images in db

Revision ID: e610b6c8c50a
Revises: a28b7c79a6b4
Create Date: 2025-12-12 14:20:25.502294

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e610b6c8c50a"
down_revision: Union[str, Sequence[str], None] = "a28b7c79a6b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
