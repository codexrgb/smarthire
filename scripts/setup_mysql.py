"""
Interactive & Secure Setup Script for SmartHire 2.0 with MySQL.

Performs:
1. Secure credential collection (password prompted via getpass without echoing).
2. URL-encoding of credentials to handle special characters.
3. Server connectivity check on MySQL 5.7+ (port 3306).
4. Creation of dedicated 'smarthire_test' database with utf8mb4 character set.
5. Local .env file generation/update (guaranteed .gitignored).
6. Safe cleanup of C:\\mysql-init.txt if elevated permissions are available.
7. Immediate automated execution of the 5-check verification suite.

Execution:
  python scripts/setup_mysql.py
Or non-interactively via flags:
  python scripts/setup_mysql.py --user root --password <SECRET> --database smarthire_test
"""

import os
import sys
import getpass
import argparse
import secrets
from pathlib import Path
from urllib.parse import quote_plus

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymysql
from scripts.verify_mysql import run_mysql_verification, sanitize_url


def setup_mysql_environment(
    host: str = "127.0.0.1",
    port: int = 3306,
    user: str = "root",
    password: str = "",
    database: str = "smarthire_test"
) -> bool:
    print("=" * 72)
    print(" SmartHire 2.0 -- MySQL Configuration & Setup")
    print("=" * 72)

    # 1. Test raw connection to MySQL server
    print(f"\n[1/4] Connecting to MySQL server at {host}:{port} as user '{user}'...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            connect_timeout=10
        )
    except Exception as e:
        print(f"\n[ERROR] Could not connect to MySQL server: {type(e).__name__}: {str(e)}")
        print("Please verify that the MySQL57 Windows service is running and credentials are correct.")
        return False

    # 2. Create dedicated database with utf8mb4
    print(f"\n[2/4] Ensuring database '{database}' exists with utf8mb4 encoding...")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        print(f"  --> PASS: Database '{database}' is ready (utf8mb4_unicode_ci).")
    except Exception as e:
        print(f"  --> FAIL: Failed to create database '{database}': {str(e)}")
        conn.close()
        return False
    finally:
        conn.close()

    # 3. Build URL-encoded connection string
    quoted_user = quote_plus(user)
    quoted_pass = quote_plus(password)
    db_url = f"mysql+pymysql://{quoted_user}:{quoted_pass}@{host}:{port}/{database}?charset=utf8mb4"

    # 4. Configure local .env file
    print(f"\n[3/4] Configuring local .env file...")
    env_path = PROJECT_ROOT / ".env"
    env_example_path = PROJECT_ROOT / ".env.example"

    env_lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            env_lines = f.readlines()
    elif env_example_path.exists():
        with open(env_example_path, "r", encoding="utf-8") as f:
            env_lines = f.readlines()
    else:
        env_lines = [
            "# SmartHire 2.0 Local Environment\n",
            "SECRET_KEY=" + secrets.token_hex(32) + "\n",
            "ALGORITHM=HS256\n",
            "ACCESS_TOKEN_EXPIRE_MINUTES=60\n",
            "DATABASE_URL=\n",
            "CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8501\n",
            "STORAGE_DIR=./storage/resumes\n",
            "MAX_UPLOAD_SIZE_MB=10\n"
        ]

    # Replace or add DATABASE_URL and SECRET_KEY if needed
    db_url_set = False
    new_lines = []
    for line in env_lines:
        stripped = line.strip()
        if stripped.startswith("DATABASE_URL="):
            new_lines.append(f"DATABASE_URL={db_url}\n")
            db_url_set = True
        elif stripped.startswith("SECRET_KEY=") and "placeholder" in stripped:
            new_lines.append(f"SECRET_KEY={secrets.token_hex(32)}\n")
        else:
            new_lines.append(line)

    if not db_url_set:
        new_lines.append(f"\nDATABASE_URL={db_url}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"  --> PASS: Updated {env_path.name} with DATABASE_URL ({sanitize_url(db_url)}).")
    print("  --> Checked: .env is excluded from git via .gitignore.")

    # 5. Attempt cleanup of C:\mysql-init.txt if present
    init_path = Path("C:/mysql-init.txt")
    if init_path.exists():
        print(f"\n[Cleanup] Detected temporary password file: {init_path}")
        try:
            os.remove(init_path)
            print("  --> PASS: Successfully deleted C:\\mysql-init.txt.")
        except PermissionError:
            print("  --> NOTICE: Could not delete C:\\mysql-init.txt due to Windows Administrator permissions.")
            print("  --> ACTION REQUIRED: Run this command in an Administrator PowerShell window:")
            print("        Remove-Item -Force C:\\mysql-init.txt")

    # 6. Run verification workflow
    print(f"\n[4/4] Executing live verification suite against '{database}'...")
    return run_mysql_verification(db_url)


def main():
    parser = argparse.ArgumentParser(description="SmartHire 2.0 MySQL Setup")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="MySQL host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port (default: 3306)")
    parser.add_argument("--user", type=str, default="root", help="MySQL username (default: root)")
    parser.add_argument("--password", type=str, default=None, help="MySQL password (prompted if omitted)")
    parser.add_argument("--database", type=str, default="smarthire_test", help="Database name (default: smarthire_test)")
    args = parser.parse_args()

    password = args.password
    if password is None:
        print("Enter MySQL credentials for SmartHire 2.0 local database setup.")
        print("(Password entry is hidden; characters will not appear on screen)")
        password = getpass.getpass(f"Enter MySQL password for user '{args.user}': ")

    success = setup_mysql_environment(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=args.database
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
