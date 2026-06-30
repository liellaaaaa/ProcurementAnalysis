"""
迁移 operation_logs 表结构
1. 备份原数据库
2. 重建 operation_logs 表（新增字段和索引）
3. 回填原有数据
"""
import os
import sqlite3
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "prices.db")
BACKUP_PATH = os.path.join(BASE_DIR, "data", "database", f"prices.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


def migrate():
    # 1. 备份
    print(f"[1/4] Backing up database to: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("[OK] Backup done")

    # 2. 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查原表结构
    cursor.execute("PRAGMA table_info(operation_logs)")
    old_columns = [row[1] for row in cursor.fetchall()]
    print(f"[INFO] Original columns: {old_columns}")

    # 3. 创建新表
    print("[2/4] Rebuilding operation_logs table...")

    # 先关闭外键约束
    cursor.execute("PRAGMA foreign_keys = OFF")

    # 开始事务
    cursor.execute("BEGIN TRANSACTION")

    # 创建临时表（新结构）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR(10),
            module VARCHAR(20),
            action VARCHAR(20),
            details VARCHAR(1000),
            result VARCHAR(20),
            operator VARCHAR(50) DEFAULT 'system',
            user_id INTEGER,
            ip_address VARCHAR(50),
            user_agent VARCHAR(500),
            session_id VARCHAR(100),
            page VARCHAR(200),
            referrer VARCHAR(200),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 创建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_user_id ON operation_logs_new(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_module ON operation_logs_new(module)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_action ON operation_logs_new(action)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_session_id ON operation_logs_new(session_id)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_page ON operation_logs_new(page)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_timestamp ON operation_logs_new(timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_page_action ON operation_logs_new(page, action)",
        "CREATE INDEX IF NOT EXISTS ix_operation_logs_user_timestamp ON operation_logs_new(user_id, timestamp)",
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)

    # 复制数据
    old_cols = ['id', 'timestamp', 'level', 'module', 'action', 'details', 'result', 'operator', 'user_id']
    col_mapping = ', '.join(old_cols)
    cursor.execute(f"INSERT INTO operation_logs_new ({col_mapping}) SELECT {col_mapping} FROM operation_logs")

    # 删除旧表
    cursor.execute("DROP TABLE operation_logs")

    # 重命名新表
    cursor.execute("ALTER TABLE operation_logs_new RENAME TO operation_logs")

    cursor.execute("COMMIT")

    # 重新启用外键约束
    cursor.execute("PRAGMA foreign_keys = ON")

    # 4. 验证
    cursor.execute("PRAGMA table_info(operation_logs)")
    new_columns = [row[1] for row in cursor.fetchall()]
    print(f"[INFO] New columns: {new_columns}")

    cursor.execute("SELECT COUNT(*) FROM operation_logs")
    count = cursor.fetchone()[0]
    print(f"[INFO] Data migrated: {count} records")

    conn.close()
    print("[OK] Migration complete!")


if __name__ == "__main__":
    migrate()
