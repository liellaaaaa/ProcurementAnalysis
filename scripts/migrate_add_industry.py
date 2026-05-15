"""
数据库迁移脚本 - 添加行业相关字段
用于在现有数据库上添加新字段，不丢失数据
"""
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "database" / "prices.db"


def migrate():
    """执行迁移"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    # 检查 products 表是否有 industry 字段
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]

    print(f"当前 products 表字段: {columns}")

    if 'industry' not in columns:
        print("添加 products.industry 字段...")
        cursor.execute("ALTER TABLE products ADD COLUMN industry VARCHAR(20)")
        print("  -> 完成")

    # 检查 price_records 表的新字段
    cursor.execute("PRAGMA table_info(price_records)")
    columns = [col[1] for col in cursor.fetchall()]

    print(f"当前 price_records 表字段: {columns}")

    new_fields = [
        ('unit', 'VARCHAR(20)'),
        ('price_original', 'VARCHAR(100)'),
        ('price_category', 'VARCHAR(20)'),
        ('extra_data', 'TEXT'),  # SQLite 没有 JSON 类型，用 TEXT 存储
    ]

    for field_name, field_type in new_fields:
        if field_name not in columns:
            print(f"添加 price_records.{field_name} 字段...")
            cursor.execute(f"ALTER TABLE price_records ADD COLUMN {field_name} {field_type}")
            print(f"  -> 完成")

    conn.commit()
    conn.close()
    print("\n迁移完成!")


if __name__ == "__main__":
    migrate()