#!/usr/bin/env python3
"""
CLI Wrapper for GitHub Restore System
Provides user-friendly command-line interface with helpful examples

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from github_restore import GitHubRestoreSystem, print_results

def print_examples():
    """Print helpful usage examples"""
    print()
    print("🔧 ANGLES AI UNIVERSE™ DISASTER RECOVERY")
    print("=" * 50)
    print()
    print("📖 USAGE EXAMPLES:")
    print()
    print("1. DRY RUN (recommended first step):")
    print("   python run_restore_now.py --dry-run")
    print("   → Shows what would be restored without making changes")
    print()
    print("2. RESTORE SPECIFIC DATE:")
    print("   python run_restore_now.py --at 2025-08-07")
    print("   → Restores backups from August 7, 2025")
    print()
    print("3. RESTORE WITH NOTION SYNC:")
    print("   python run_restore_now.py --with-notion")
    print("   → Restores to both Supabase and Notion databases")
    print()
    print("4. RESTORE SPECIFIC FILE:")
    print("   python run_restore_now.py --file exports/decision_vault_2025-08-07.json")
    print("   → Restores from a specific backup file")
    print()
    print("5. FORCE RESTORE (DANGEROUS):")
    print("   python run_restore_now.py --file exports/backup.json --force")
    print("   → Overwrites newer records (use with caution)")
    print()
    print("6. FULL RESTORE WITH ALL OPTIONS:")
    print("   python run_restore_now.py --at 2025-08-07 --with-notion --force")
    print("   → Complete restore with Notion sync and force overwrite")
    print()
    print("⚠️  SAFETY TIPS:")
    print("   • Always run --dry-run first to see what will be restored")
    print("   • Use --force only when you're sure you want to overwrite newer data")
    print("   • Back up your current data before running live restores")
    print("   • Check logs/restore.log for detailed operation logs")
    print()
    print("🔍 AVAILABLE OPTIONS:")
    print("   --dry-run          Simulate restore without making changes")
    print("   --at YYYY-MM-DD    Restore from specific date")
    print("   --file PATH        Restore from specific file (can use multiple times)")
    print("   --force            Overwrite newer records")
    print("   --with-notion      Include Notion database sync")
    print("   --help             Show detailed help")
    print()
    print("=" * 50)

def main():
    """Main entry point for CLI wrapper"""
    parser = argparse.ArgumentParser(
        description="Restore Angles AI Universe™ memory system from GitHub backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For detailed examples and usage information, run without arguments.
        """
    )
    
    parser.add_argument('--at', type=str, metavar='YYYY-MM-DD',
                       help='Restore from specific date (YYYY-MM-DD)')
    parser.add_argument('--file', type=str, action='append', metavar='PATH',
                       help='Restore from explicit file(s) (can be used multiple times)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be restored without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite newer records in database')
    parser.add_argument('--with-notion', action='store_true',
                       help='Also restore to Notion database')
    
    # If no arguments provided, show examples
    if len(sys.argv) == 1:
        print_examples()
        return
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.at and args.file:
        print("❌ ERROR: Cannot use both --at and --file options together")
        print("Use either --at for date-specific restore or --file for explicit files")
        sys.exit(1)
    
    # Show safety warning for non-dry-run operations
    if not args.dry_run:
        print()
        print("⚠️  WARNING: This will modify your database!")
        print("             Run with --dry-run first to see what will be restored.")
        
        response = input("Continue with live restore? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("Restore cancelled by user")
            sys.exit(0)
        print()
    
    try:
        # Initialize restore system
        print("🔧 Initializing restore system...")
        restore_system = GitHubRestoreSystem()
        
        # Run restore
        result = restore_system.run_restore(
            target_date=args.at,
            explicit_files=args.file,
            dry_run=args.dry_run,
            force=args.force,
            with_notion=args.with_notion
        )
        
        # Print results
        print_results(result)
        
        # Show next steps
        if result['success']:
            if args.dry_run:
                print("💡 NEXT STEPS:")
                print("   • Review the dry-run results above")
                print("   • Run without --dry-run to perform actual restore")
                if not args.with_notion and (result.get('notion_result') is None):
                    print("   • Add --with-notion to also sync to Notion")
            else:
                print("🎉 RESTORE COMPLETED SUCCESSFULLY!")
                print("   • Check your Supabase database for restored data")
                if args.with_notion:
                    print("   • Check your Notion database for synced pages")
                print("   • View logs/restore.log for detailed operation log")
        else:
            print("💔 RESTORE FAILED")
            print("   • Check the error message above")
            print("   • View logs/restore.log for detailed error information")
            print("   • Ensure all environment variables are set correctly")
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Restore interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        print("   • Check logs/restore.log for detailed error information")
        print("   • Ensure all environment variables are set correctly")
        print("   • Verify git repository and GitHub access")
        sys.exit(1)

if __name__ == "__main__":
    main()