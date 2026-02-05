# Deployment Guide: Level-Specific Clue System
**Version:** 1.0  
**Date:** February 5, 2026  
**Migration Script:** `migrate_level_clues.py`

---

## Pre-Deployment Checklist

### 1. Backup Database
```bash
# MySQL/MariaDB
mysqldump -u username -p treasure_hunt > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use the backup script
./backup_database.sh
```

### 2. Verify Current State
```bash
# Check current database schema
mysql -u username -p treasure_hunt -e "DESCRIBE levels;"
mysql -u username -p treasure_hunt -e "DESCRIBE teams;"

# Verify game config
mysql -u username -p treasure_hunt -e "SELECT * FROM game_config;"
```

### 3. Test Migration (Dry Run)
```bash
# Activate virtual environment
source .venv/bin/activate

# Run dry-run to see what will happen
python migrate_level_clues.py upgrade --dry-run
```

---

## Deployment Steps

### Step 1: Stop Application
```bash
# If using systemd
sudo systemctl stop treasure-hunt

# If using screen/tmux
# Find and stop the process
ps aux | grep "python.*app.py"
kill <PID>

# Or if running with gunicorn
sudo systemctl stop gunicorn-treasure-hunt
```

### Step 2: Pull Latest Code
```bash
cd /path/to/treasure-hunt
git pull origin main

# Verify you have the latest commits
git log --oneline -3
# Should show:
# 195ee04 - Add session summary
# d468f48 - Add comprehensive testing and bug fix report
# d3e3425 - Implement level-specific clue system and add test infrastructure
```

### Step 3: Update Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Run Migration
```bash
# Run the migration
python migrate_level_clues.py upgrade

# Expected output:
# ================================================================================
# MIGRATION: Add Level-Specific Clue Quotas
# ================================================================================
# 
# Step 1: Checking if migration is needed...
# Step 2: Adding 'clues_allowed' column to levels table...
# ✓ Successfully added 'clues_allowed' column
# Step 3: Populating clues_allowed with default values...
# ✓ Updated X levels with default clues_allowed = Y
# Step 4: Removing 'clues_remaining' column from teams table...
# ✓ Successfully removed 'clues_remaining' column
# Step 5: Verifying migration...
# ✓ All X levels have clues_allowed set
# ✓ Dynamic clues_remaining property working
# 
# ================================================================================
# MIGRATION COMPLETED SUCCESSFULLY
# ================================================================================
```

### Step 5: Verify Migration
```bash
# Check database schema
mysql -u username -p treasure_hunt -e "DESCRIBE levels;" | grep clues_allowed
mysql -u username -p treasure_hunt -e "DESCRIBE teams;" | grep clues_remaining

# Verify data
mysql -u username -p treasure_hunt -e "SELECT level_number, name, clues_allowed FROM levels;"
```

### Step 6: Start Application
```bash
# If using systemd
sudo systemctl start treasure-hunt
sudo systemctl status treasure-hunt

# If using screen/tmux
screen -S treasure-hunt
source .venv/bin/activate
python app.py

# Or if using gunicorn
sudo systemctl start gunicorn-treasure-hunt
```

### Step 7: Verify Application
```bash
# Check application logs
tail -f /var/log/treasure-hunt/app.log

# Or if using systemd
journalctl -u treasure-hunt -f

# Test the application
curl http://localhost:5000/
```

---

## Post-Deployment Testing

### 1. Admin Interface Tests
- [ ] Log in as admin
- [ ] Navigate to "Initialize Game"
- [ ] Verify per-level clue configuration inputs are visible
- [ ] Create a test game with different clue quotas per level
- [ ] Verify levels are created with correct clue_allowed values
- [ ] Check "Manage Levels" page shows clue quotas
- [ ] Verify "Level Tracker" shows "Clues Left" column

### 2. Player Interface Tests
- [ ] Log in as a test team
- [ ] Verify "Clues Remaining (Level X): Y" is displayed
- [ ] Request a clue and verify count decreases
- [ ] Exhaust all clues for current level
- [ ] Verify appropriate error message
- [ ] Advance to next level (manually via admin)
- [ ] Verify clue count resets for new level

### 3. Database Integrity Tests
```sql
-- Verify all levels have clues_allowed set
SELECT level_number, name, clues_allowed FROM levels WHERE clues_allowed = 0;
-- Should return no rows (or only levels intentionally set to 0)

-- Verify teams table structure
DESCRIBE teams;
-- Should NOT show clues_remaining column (MySQL/PostgreSQL)
-- May still show it in SQLite (but it's unused)

-- Test clue usage tracking
SELECT t.name, l.level_number, l.clues_allowed, COUNT(cu.id) as clues_used
FROM teams t
JOIN levels l ON l.level_number = t.current_level
LEFT JOIN team_progress tp ON tp.team_id = t.id
LEFT JOIN clue_usage cu ON cu.team_id = t.id
GROUP BY t.id, l.id;
```

---

## Rollback Procedure

If issues are encountered, you can rollback the migration:

### Step 1: Stop Application
```bash
sudo systemctl stop treasure-hunt
```

### Step 2: Rollback Migration
```bash
source .venv/bin/activate
python migrate_level_clues.py downgrade
```

### Step 3: Restore Previous Code
```bash
git checkout e6a53bc  # Previous commit before clue system changes
```

### Step 4: Restore Database (if needed)
```bash
# Only if rollback migration fails
mysql -u username -p treasure_hunt < backup_YYYYMMDD_HHMMSS.sql
```

### Step 5: Restart Application
```bash
sudo systemctl start treasure-hunt
```

---

## Troubleshooting

### Issue: Migration fails with "column already exists"
**Solution:** Migration is idempotent. Run it again, it will skip existing columns.

### Issue: SQLite "cannot drop column" error
**Solution:** This is expected. SQLite doesn't support DROP COLUMN. The column remains but is unused.

### Issue: Teams show 0 clues remaining
**Cause:** Level doesn't have clues_allowed set
**Solution:**
```sql
UPDATE levels SET clues_allowed = 10 WHERE clues_allowed = 0;
```

### Issue: Application won't start after migration
**Check:**
1. Verify all files were pulled: `git status`
2. Check Python errors: `python app.py` (run directly to see errors)
3. Verify database connection: Check `.env` file
4. Check logs: `tail -f /var/log/treasure-hunt/app.log`

### Issue: Dynamic property error
**Error:** `AttributeError: 'Team' object has no attribute 'clues_remaining'`
**Cause:** Old code still deployed
**Solution:** 
```bash
git pull origin main
sudo systemctl restart treasure-hunt
```

---

## Performance Considerations

### Before Deployment
- Current clue tracking: 1 database column read
- Queries: Simple SELECT on teams table

### After Deployment
- Current clue tracking: 1 JOIN + 1 COUNT query
- Queries: More complex but still fast

### Optimization (if needed)
If you notice performance issues with many teams:

```sql
-- Add index for faster clue usage queries
CREATE INDEX idx_clue_usage_team_question ON clue_usage(team_id, question_id);
CREATE INDEX idx_questions_level ON questions(level_id);
```

---

## Monitoring

### Key Metrics to Watch
1. **Response Time:** Dashboard load time
2. **Database Queries:** Number of queries per request
3. **Error Rate:** Any 500 errors in logs
4. **Clue Usage:** Verify teams can request clues

### Monitoring Commands
```bash
# Watch application logs
tail -f /var/log/treasure-hunt/app.log | grep -i error

# Monitor database connections
mysql -u username -p -e "SHOW PROCESSLIST;"

# Check application status
systemctl status treasure-hunt
```

---

## Success Criteria

✅ Migration completes without errors  
✅ All levels have clues_allowed > 0 (or intentionally 0)  
✅ Teams can request clues  
✅ Clue counts reset when advancing levels  
✅ Admin can configure per-level clue quotas  
✅ No application errors in logs  
✅ Database queries complete in < 100ms  

---

## Support

If you encounter issues during deployment:

1. **Check logs:** `/var/log/treasure-hunt/app.log`
2. **Review migration output:** Look for ✗ symbols
3. **Verify database state:** Run verification queries above
4. **Rollback if needed:** Follow rollback procedure
5. **Contact:** Review `TESTING_REPORT_2026-02-05.md` for detailed information

---

## Additional Notes

- **Backup Retention:** Keep database backups for at least 7 days
- **Testing Window:** Plan for 15-30 minutes of downtime
- **User Communication:** Notify users of maintenance window
- **Staging First:** Test on staging environment before production

---

**Last Updated:** February 5, 2026  
**Migration Version:** 1.0  
**Tested On:** MySQL 8.0, SQLite 3.x
