# Database Restore and Fix Scripts

This directory contains scripts for restoring database tables from backups and fixing inconsistencies between tables.

## Scripts

### 1. `restore_from_backup.py`

Restores tables from their backup versions.

```bash
python scripts/database_restore/restore_from_backup.py [options]
```

Options:
- `--tables`: Comma-separated list of tables to restore (default: url_tracking,tweets,kol_character)
- `--db-path`: Path to the SQLite database (default: data/local_database.db)
- `--no-backup`: Do not create backups of current tables before restoring
- `--verbose`: Enable verbose output

### 2. `fix_kol_id.py`

Fixes kol_id in kol_character table to match user_id in url_tracking table.

```bash
python scripts/database_restore/fix_kol_id.py [options]
```

Options:
- `--db-path`: Path to the SQLite database (default: data/local_database.db)
- `--apply`: Apply changes (default is dry run)
- `--add-missing`: Add missing screen_names to kol_character table
- `--verbose`: Enable verbose output

## Usage Examples

### Restore All Tables

```bash
python scripts/database_restore/restore_from_backup.py
```

### Restore Specific Tables

```bash
python scripts/database_restore/restore_from_backup.py --tables url_tracking,tweets
```

### Fix kol_id (Dry Run)

```bash
python scripts/database_restore/fix_kol_id.py
```

### Fix kol_id and Apply Changes

```bash
python scripts/database_restore/fix_kol_id.py --apply
```

### Fix kol_id and Add Missing screen_names

```bash
python scripts/database_restore/fix_kol_id.py --apply --add-missing
```

## Workflow

1. First restore tables from backups:
   ```bash
   python scripts/database_restore/restore_from_backup.py
   ```

2. Then fix kol_id in kol_character table:
   ```bash
   python scripts/database_restore/fix_kol_id.py --apply
   ```

3. Optionally add missing screen_names:
   ```bash
   python scripts/database_restore/fix_kol_id.py --apply --add-missing
   ```

## Notes

- Always run scripts in dry run mode first to see what changes will be made
- The scripts create backups before making changes by default
- All operations are logged for transparency
