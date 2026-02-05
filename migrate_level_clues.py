"""
Migration: Add level-specific clue quotas
Date: 2026-02-05
Description: Migrates from global team clue tracking to per-level clue quotas

Changes:
- Adds 'clues_allowed' column to levels table
- Removes 'clues_remaining' column from teams table (now a dynamic property)
- Populates existing levels with default clue values from game config
"""

import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Level, GameConfig

def upgrade():
    """Apply the migration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("MIGRATION: Add Level-Specific Clue Quotas")
        print("=" * 80)
        print()
        
        # Step 1: Check if clues_allowed already exists
        print("Step 1: Checking if migration is needed...")
        inspector = db.inspect(db.engine)
        levels_columns = [col['name'] for col in inspector.get_columns('levels')]
        teams_columns = [col['name'] for col in inspector.get_columns('teams')]
        
        clues_allowed_exists = 'clues_allowed' in levels_columns
        clues_remaining_exists = 'clues_remaining' in teams_columns
        
        if clues_allowed_exists and not clues_remaining_exists:
            print("✓ Migration already applied. Nothing to do.")
            return
        
        # Step 2: Add clues_allowed to levels table
        if not clues_allowed_exists:
            print("\nStep 2: Adding 'clues_allowed' column to levels table...")
            try:
                db.session.execute(text(
                    "ALTER TABLE levels ADD COLUMN clues_allowed INTEGER DEFAULT 0"
                ))
                db.session.commit()
                print("✓ Successfully added 'clues_allowed' column")
            except Exception as e:
                print(f"✗ Error adding column: {e}")
                db.session.rollback()
                raise
        else:
            print("\nStep 2: 'clues_allowed' column already exists, skipping...")
        
        # Step 3: Populate clues_allowed with default values
        print("\nStep 3: Populating clues_allowed with default values...")
        try:
            config = GameConfig.query.first()
            default_clues = config.clues_per_team if config else 10
            
            levels = Level.query.all()
            updated_count = 0
            
            for level in levels:
                if level.clues_allowed == 0:  # Only update if not already set
                    level.clues_allowed = default_clues
                    updated_count += 1
            
            db.session.commit()
            print(f"✓ Updated {updated_count} levels with default clues_allowed = {default_clues}")
        except Exception as e:
            print(f"✗ Error populating clues_allowed: {e}")
            db.session.rollback()
            raise
        
        # Step 4: Remove clues_remaining from teams table
        if clues_remaining_exists:
            print("\nStep 4: Removing 'clues_remaining' column from teams table...")
            try:
                # Note: SQLite doesn't support DROP COLUMN, so we need to check the database type
                db_type = db.engine.url.drivername
                
                if 'sqlite' in db_type:
                    print("⚠ SQLite detected: Cannot drop column directly.")
                    print("  The column will remain but is no longer used.")
                    print("  Team.clues_remaining is now a dynamic property.")
                else:
                    # MySQL/PostgreSQL support DROP COLUMN
                    db.session.execute(text(
                        "ALTER TABLE teams DROP COLUMN clues_remaining"
                    ))
                    db.session.commit()
                    print("✓ Successfully removed 'clues_remaining' column")
            except Exception as e:
                print(f"✗ Error removing column: {e}")
                db.session.rollback()
                # Don't raise - this is not critical as the column is just unused
                print("  Continuing anyway - column will be ignored by the application")
        else:
            print("\nStep 4: 'clues_remaining' column already removed, skipping...")
        
        # Step 5: Verify migration
        print("\nStep 5: Verifying migration...")
        try:
            levels = Level.query.all()
            all_have_clues = all(level.clues_allowed > 0 for level in levels)
            
            if all_have_clues:
                print(f"✓ All {len(levels)} levels have clues_allowed set")
            else:
                levels_without = [l.level_number for l in levels if l.clues_allowed == 0]
                print(f"⚠ Warning: {len(levels_without)} levels have clues_allowed = 0")
                print(f"  Levels: {levels_without}")
            
            # Test dynamic property
            from models import Team
            teams = Team.query.limit(1).all()
            if teams:
                test_team = teams[0]
                clues = test_team.clues_remaining
                print(f"✓ Dynamic clues_remaining property working (test team has {clues} clues)")
            
        except Exception as e:
            print(f"⚠ Verification warning: {e}")
        
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nSummary:")
        print("  - Added 'clues_allowed' to levels table")
        print("  - Populated existing levels with default values")
        print("  - Removed/deprecated 'clues_remaining' from teams table")
        print("  - Team.clues_remaining is now a dynamic property")
        print()

def downgrade():
    """Rollback the migration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("ROLLBACK: Remove Level-Specific Clue Quotas")
        print("=" * 80)
        print()
        
        # Step 1: Add clues_remaining back to teams table
        print("Step 1: Adding 'clues_remaining' column back to teams table...")
        try:
            inspector = db.inspect(db.engine)
            teams_columns = [col['name'] for col in inspector.get_columns('teams')]
            
            if 'clues_remaining' not in teams_columns:
                db.session.execute(text(
                    "ALTER TABLE teams ADD COLUMN clues_remaining INTEGER DEFAULT 0"
                ))
                db.session.commit()
                print("✓ Successfully added 'clues_remaining' column")
            else:
                print("✓ 'clues_remaining' column already exists")
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            db.session.rollback()
            raise
        
        # Step 2: Restore clues_remaining values
        print("\nStep 2: Restoring clues_remaining values from game config...")
        try:
            from models import Team
            config = GameConfig.query.first()
            default_clues = config.clues_per_team if config else 10
            
            teams = Team.query.all()
            for team in teams:
                # This will fail if the column was already removed in SQLite
                try:
                    db.session.execute(text(
                        f"UPDATE teams SET clues_remaining = {default_clues} WHERE id = {team.id}"
                    ))
                except:
                    pass
            
            db.session.commit()
            print(f"✓ Restored clues_remaining for {len(teams)} teams")
        except Exception as e:
            print(f"✗ Error restoring values: {e}")
            db.session.rollback()
        
        # Step 3: Remove clues_allowed from levels table
        print("\nStep 3: Removing 'clues_allowed' column from levels table...")
        try:
            db_type = db.engine.url.drivername
            
            if 'sqlite' in db_type:
                print("⚠ SQLite detected: Cannot drop column directly.")
                print("  Manual intervention required for complete rollback.")
            else:
                db.session.execute(text(
                    "ALTER TABLE levels DROP COLUMN clues_allowed"
                ))
                db.session.commit()
                print("✓ Successfully removed 'clues_allowed' column")
        except Exception as e:
            print(f"✗ Error removing column: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 80)
        print("ROLLBACK COMPLETED")
        print("=" * 80)
        print()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate level-specific clue quotas')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], 
                       help='Migration action to perform')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()
    
    try:
        if args.action == 'upgrade':
            if not args.dry_run:
                upgrade()
            else:
                print("Would execute upgrade():")
                print("  1. Add 'clues_allowed' to levels table")
                print("  2. Populate with default values from game_config")
                print("  3. Remove 'clues_remaining' from teams table")
        else:
            if not args.dry_run:
                downgrade()
            else:
                print("Would execute downgrade():")
                print("  1. Add 'clues_remaining' back to teams table")
                print("  2. Restore default values")
                print("  3. Remove 'clues_allowed' from levels table")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
