"""
每日数据自动刷新脚本
- 爬取基准价 + 详细报价（调用 shengyishe）
- 日志记录到 log/operations.log

建议通过 Windows 任务计划程序每天 7:30 执行：
  python -m backend.scripts.daily_refresh
"""
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "log"
LOG_FILE = LOG_DIR / "operations.log"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [daily_refresh] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_scraper():
    log("开始执行 shengyishe 爬虫（基准价 + 详细报价）...")
    result = subprocess.run(
        [sys.executable, "-m", "backend.scrapers.shengyishe"],
        cwd=str(PROJECT_ROOT),
    )
    log(f"shengyishe 爬虫执行完毕，退出码: {result.returncode}")
    return result.returncode


if __name__ == "__main__":
    try:
        exit_code = run_scraper()
        sys.exit(exit_code)
    except Exception as e:
        log(f"脚本异常: {e}")
        sys.exit(1)
