"""
Database cleanup utility script.
Use this to clear test data or reset the database.
"""

from db.memory import get_memory
import sys


def clear_all():
    """Clear all data from the database."""
    print("⚠️  WARNING: This will delete ALL data from the database!")
    confirm = input("Are you sure? Type 'yes' to confirm: ")

    if confirm.lower() == 'yes':
        memory = get_memory()
        memory.clear_all_data()
        print("✅ All database data has been cleared")
    else:
        print("❌ Operation cancelled")


def clear_user_by_email(email: str):
    """Clear data for a specific user by email."""
    print(f"🧹 Clearing data for user: {email}")
    memory = get_memory()
    memory.delete_user_by_email(email)
    print("✅ User data cleared")


if __name__ == "__main__":
    print("🗑️  NutriGenie Database Cleanup Utility")
    print("=" * 50)

    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            clear_all()
        elif sys.argv[1] == "--email" and len(sys.argv) > 2:
            email = sys.argv[2]
            clear_user_by_email(email)
        else:
            print("Usage:")
            print("  python clear_db.py --all              # Clear all data (requires confirmation)")
            print("  python clear_db.py --email <email>    # Clear data for specific user")
    else:
        print("\nOptions:")
        print("1. Clear all data")
        print("2. Clear user by email")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            clear_all()
        elif choice == "2":
            email = input("Enter user email: ")
            clear_user_by_email(email)
        elif choice == "3":
            print("👋 Exiting")
        else:
            print("❌ Invalid choice")
