"""Adds a Repo.chacra_modified field

Revision ID: a1f3c9d2e4b5
Revises: ccb19795cbdc
Create Date: 2026-10-28 19:20:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a1f3c9d2e4b5'
down_revision = 'ccb19795cbdc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('repos', sa.Column('chacra_modified', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('repos', 'chacra_modified')
