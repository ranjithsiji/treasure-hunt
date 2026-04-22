"""
Migration: Add site_content, pages, and menu_items tables.
Run with: python migrate_cms.py
"""
import sys
import os

# Add the project root to sys.path so models/app can be imported
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from models import SiteContent, Page, MenuItem
import sqlalchemy as sa


def run_migration():
    app = create_app()
    with app.app_context():
        inspector = sa.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        tables_created = []

        if 'site_content' not in existing_tables:
            SiteContent.__table__.create(db.engine)
            tables_created.append('site_content')
            print("✅  Created table: site_content")
        else:
            print("⏭️  Table already exists: site_content")

        if 'pages' not in existing_tables:
            Page.__table__.create(db.engine)
            tables_created.append('pages')
            print("✅  Created table: pages")
        else:
            print("⏭️  Table already exists: pages")

        if 'menu_items' not in existing_tables:
            MenuItem.__table__.create(db.engine)
            tables_created.append('menu_items')
            print("✅  Created table: menu_items")
        else:
            print("⏭️  Table already exists: menu_items")

        if tables_created:
            print(f"\n🎉  Migration complete. Created: {', '.join(tables_created)}")
        else:
            print("\n✅  No migrations needed — all tables already exist.")


if __name__ == '__main__':
    run_migration()
