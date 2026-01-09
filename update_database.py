"""
Utility script to update the database from another Bushel_Management project.
This copies the database file from the source project to this reporting project.
"""
import shutil
import sys
from pathlib import Path
from datetime import datetime


def update_database(source_db_path: str = None, backup: bool = True):
    """
    Copy database from source project to this reporting project.
    
    Args:
        source_db_path: Path to the source database file. If None, will prompt or use common locations.
        backup: Whether to create a backup of the existing database before overwriting.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    target_db_path = project_root / 'data' / 'bushel_management.db'
    
    # Ensure data directory exists
    target_db_path.parent.mkdir(exist_ok=True)
    
    # If no source path provided, try common locations
    if source_db_path is None:
        # Common locations to check
        common_paths = [
            # Primary source database location
            Path.home() / 'PycharmProjects' / 'Bushel_Management' / 'data' / 'bushel_management.db',
            Path.home() / 'PycharmProjects' / 'Bushel_Management' / 'database' / 'bushel_management.db',
            # Alternative locations
            Path.home() / 'PycharmProjects' / 'Bushel_Management_data' / 'bushel_management.db',
            Path.home() / 'PycharmProjects' / 'Bushel_Management_data' / 'data' / 'bushel_management.db',
        ]
        
        print("No source database path provided. Checking common locations...")
        for path in common_paths:
            if path.exists():
                print(f"Found database at: {path}")
                source_db_path = str(path)
                break
        
        if source_db_path is None:
            print("\nCould not find database automatically. Please provide the source path.")
            print("\nCommon locations to check:")
            print("  - Bushel_Management/data/bushel_management.db")
            print("  - Bushel_Management/database/bushel_management.db")
            source_db_path = input("\nEnter full path to source database: ").strip()
    
    # Convert to Path object
    source_path = Path(source_db_path)
    
    # Validate source file exists
    if not source_path.exists():
        print(f"❌ Error: Source database not found at: {source_path}")
        print(f"   Please check the path and try again.")
        return False
    
    # Check source file size
    source_size = source_path.stat().st_size / (1024 * 1024)  # Size in MB
    print(f"\n📊 Source database: {source_path}")
    print(f"   Size: {source_size:.2f} MB")
    
    # Backup existing database if it exists
    if target_db_path.exists() and backup:
        backup_path = project_root / 'data' / f'bushel_management_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        print(f"\n💾 Creating backup of existing database...")
        shutil.copy2(target_db_path, backup_path)
        print(f"   Backup saved to: {backup_path}")
    
    # Copy the database
    print(f"\n📋 Copying database...")
    try:
        shutil.copy2(source_path, target_db_path)
        
        # Verify the copy
        if target_db_path.exists():
            target_size = target_db_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"✅ Database updated successfully!")
            print(f"   Target: {target_db_path}")
            print(f"   Size: {target_size:.2f} MB")
            
            # Verify sizes match
            if abs(source_size - target_size) < 0.01:  # Allow small difference for filesystem
                print(f"   ✓ File sizes match")
            else:
                print(f"   ⚠️  Warning: File sizes don't match exactly (might be normal)")
            
            return True
        else:
            print(f"❌ Error: Copy completed but target file not found!")
            return False
            
    except Exception as e:
        print(f"❌ Error copying database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("Bushel Management Database Update Utility")
    print("=" * 60)
    
    # Check if path provided as command line argument
    source_path = None
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
        print(f"Using source path from command line: {source_path}")
    
    # Run the update
    success = update_database(source_path, backup=True)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Database update completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Database update failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
