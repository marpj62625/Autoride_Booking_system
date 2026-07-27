# Database Migrations

This directory contains database migration scripts for the AutoRide system.

## Available Migrations

### 001: Booking Extension Tables
**Files:**
- `001_add_extension_tables.sql` - Forward migration
- `001_rollback_extension_tables.sql` - Rollback migration
- `001_add_extension_tables.py` - Legacy Python version (deprecated)

**Purpose:** Adds database schema for booking extension and conflict resolution feature.

**Tables Created:**
- `booking_extensions` - Stores extension requests and approvals
- `booking_conflicts` - Tracks conflicts when extensions overlap
- `extension_payments` - Records extension payment transactions

**Bookings Table Changes:**
- Adds 4 new columns with DEFAULT values (backward compatible)

---

## Running Migrations

### Method 1: Using Python Runner (Recommended)

#### Forward Migration
```bash
cd backend/migrations
python run_migration.py
```

#### Rollback Migration
```bash
cd backend/migrations
python run_migration.py rollback
```

### Method 2: Direct SQL Execution

#### Using psql
```bash
psql <connection_string> -f 001_add_extension_tables.sql
```

#### Using Python Script
```python
import psycopg
from config import SUPABASE_DB_URL

conn = psycopg.connect(SUPABASE_DB_URL)
cursor = conn.cursor()

with open('001_add_extension_tables.sql', 'r') as f:
    cursor.execute(f.read())

conn.commit()
conn.close()
```

---

## Testing Migrations

### Full Migration Test (with cleanup)
```bash
python test_migration.py
```

This will:
1. Clean up any existing extension tables
2. Run the forward migration
3. Verify all objects were created correctly

### Rollback Test
```bash
python test_rollback.py
```

This will:
1. Run the rollback migration
2. Verify all objects were removed correctly

---

## Migration File Naming Convention

```
<version>_<description>.sql        # Forward migration
<version>_rollback_<description>.sql  # Rollback migration
```

Example:
- `001_add_extension_tables.sql`
- `001_rollback_extension_tables.sql`

---

## Best Practices

### Before Running Migrations

1. **Backup Database**
   ```bash
   pg_dump <connection_string> > backup_$(date +%Y%m%d).sql
   ```

2. **Test on Staging First**
   - Always test migrations on a staging database
   - Verify application functionality after migration

3. **Review Migration Script**
   - Check all table names, column names, data types
   - Verify foreign key relationships
   - Check default values and constraints

### During Migration

1. **Use Transactions**
   - All migration scripts use BEGIN/COMMIT blocks
   - Failed migrations will rollback automatically

2. **Monitor Progress**
   - Watch for error messages
   - Check execution time
   - Verify disk space

3. **Verify Results**
   - Use verification scripts after migration
   - Check table counts
   - Test key queries

### After Migration

1. **Verify Application**
   - Test critical user flows
   - Check admin functionality
   - Monitor error logs

2. **Performance Check**
   - Check query performance
   - Verify indexes are being used
   - Monitor database load

3. **Document**
   - Record migration date and time
   - Note any issues encountered
   - Update changelog

---

## Rollback Procedure

If migration causes issues:

1. **Immediate Rollback**
   ```bash
   python run_migration.py rollback
   ```

2. **Verify Rollback**
   ```bash
   python test_rollback.py
   ```

3. **Restore from Backup** (if rollback fails)
   ```bash
   psql <connection_string> < backup_file.sql
   ```

---

## Migration Scripts Reference

### run_migration.py
**Purpose:** Production-ready migration runner with verification

**Features:**
- Automatic connection handling
- Transaction management
- Error handling with rollback
- Post-migration verification
- Detailed logging

**Usage:**
```bash
# Run forward migration
python run_migration.py

# Run rollback
python run_migration.py rollback
```

### test_migration.py
**Purpose:** Complete migration test with cleanup

**Features:**
- Cleans up existing tables first
- Runs fresh migration
- Comprehensive verification
- Useful for development

**Usage:**
```bash
python test_migration.py
```

### test_rollback.py
**Purpose:** Test rollback functionality

**Features:**
- Executes rollback script
- Verifies all objects removed
- Confirms database restoration

**Usage:**
```bash
python test_rollback.py
```

---

## Troubleshooting

### Error: "Table already exists"
**Solution:** Run rollback first, then re-run migration
```bash
python run_migration.py rollback
python run_migration.py
```

### Error: "Foreign key constraint violation"
**Cause:** Migration order issue or existing data conflicts  
**Solution:** Check for dependent data, run cleanup if needed

### Error: "Permission denied"
**Cause:** Insufficient database privileges  
**Solution:** Ensure database user has CREATE TABLE permissions

### Error: "Column already exists"
**Cause:** Partial migration was applied  
**Solution:** Run rollback to clean state, then re-migrate

---

## Verification Queries

### Check if tables exist
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments');
```

### Check bookings table columns
```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'bookings' 
  AND column_name IN ('has_active_extension', 'extension_count', 'is_conflict_affected', 'conflict_id');
```

### Check indexes
```sql
SELECT indexname 
FROM pg_indexes 
WHERE indexname LIKE 'idx_booking_extensions%' 
   OR indexname LIKE 'idx_booking_conflicts%' 
   OR indexname LIKE 'idx_extension_payments%';
```

### Check foreign keys
```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments', 'bookings');
```

---

## Migration History

| Version | Description | Date | Status |
|---------|-------------|------|--------|
| 001 | Add booking extension tables | 2024 | ? Tested |

---

## Support

For issues with migrations:
1. Check the MIGRATION_TEST_REPORT.md for detailed test results
2. Review the SQL files for schema details
3. Run verification queries to diagnose issues
4. Check PostgreSQL logs for detailed error messages

---

**Last Updated:** 2024  
**Database:** PostgreSQL (Supabase)  
**Status:** Production Ready
