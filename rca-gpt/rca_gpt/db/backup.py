"""
Database backup utilities
"""
import shutil
from pathlib import Path
from datetime import datetime
import yaml


def backup_database(config_path='config/config.yaml'):
    """
    Create backup of incident database
    
    Returns:
        Path to backup file
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_path = Path(config['database']['path'])
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    # Create backup directory
    backup_dir = db_path.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f"incidents_backup_{timestamp}.db"
    
    # Copy database
    shutil.copy2(db_path, backup_file)
    
    print(f"✅ Database backed up to: {backup_file}")
    return backup_file


def list_backups(config_path='config/config.yaml'):
    """List all available backups"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_path = Path(config['database']['path'])
    backup_dir = db_path.parent / 'backups'
    
    if not backup_dir.exists():
        return []
    
    backups = sorted(backup_dir.glob('incidents_backup_*.db'), reverse=True)
    return backups


def restore_database(backup_file, config_path='config/config.yaml'):
    """
    Restore database from backup
    
    Args:
        backup_file: Path to backup file
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    db_path = Path(config['database']['path'])
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    
    # Backup current database first
    if db_path.exists():
        current_backup = backup_database(config_path)
        print(f"   Current database backed up to: {current_backup}")
    
    # Restore
    shutil.copy2(backup_path, db_path)
    print(f"✅ Database restored from: {backup_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'backup':
        backup_database()
    elif len(sys.argv) > 1 and sys.argv[1] == 'list':
        backups = list_backups()
        print(f"\n📦 Found {len(backups)} backup(s):\n")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup.name}")
    else:
        print("Usage: python -m rca_gpt.db.backup [backup|list]")