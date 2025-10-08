"""init schema

Revision ID: 7e5cd6b0196e
Revises: 
Create Date: 2025-09-28 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '7e5cd6b0196e'
down_revision = None
branch_labels = None
depends_on = None

# Define ENUM without creating it (assume it exists)
role_enum = postgresql.ENUM("admin", "editor", "viewer", name="roleenum", create_type=False)


def upgrade():
    # Ensure ENUM exists
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'roleenum') THEN
            CREATE TYPE roleenum AS ENUM ('admin', 'editor', 'viewer');
        END IF;
    END$$;
    """)

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String, nullable=False, unique=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("role", role_enum, nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
        sa.Column("reset_token", sa.String, nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
    )

    # Folders table
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )

    # Files table
    op.create_table(
        "files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("folder_id", sa.Integer, sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.String, nullable=True),
        sa.Column("uploaded_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("storage_type", sa.String, server_default="s3"),
        sa.Column("storage_key", sa.String, nullable=True),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Folder Permissions table
    op.create_table(
        "folder_permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("folder_id", sa.Integer, sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission", role_enum, nullable=False),
    )


def downgrade():
    op.drop_table("folder_permissions")
    op.drop_table("files")
    op.drop_table("folders")
    op.drop_table("users")
    
    # Drop ENUM only if exists
    op.execute("DROP TYPE IF EXISTS roleenum;")
