"""
批量导入61个采购监控产品
用于初始化新的行业分类数据
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 61个产品清单
PRODUCTS = [
    # ========== 化工（54个品类）==========
    {"product_name": "AES", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1544.html"},
    {"product_name": "DMF", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-786.html"},
    {"product_name": "EGDA", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1611.html"},
    {"product_name": "TDI", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1095.html"},
    {"product_name": "苯酚", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-464.html"},
    {"product_name": "丙二醇甲醚醋酸酯", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1482.html"},
    {"product_name": "丙酮", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-582.html"},
    {"product_name": "丙烯", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-505.html"},
    {"product_name": "丙烯酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-584.html"},
    {"product_name": "丙烯酰胺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1615.html"},
    {"product_name": "纯苯", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-120.html"},
    {"product_name": "醋酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-218.html"},
    {"product_name": "电石", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-640.html"},
    {"product_name": "丁酮肟", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1703.html"},
    {"product_name": "二丙二醇", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1519.html"},
    {"product_name": "二甘醇", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1332.html"},
    {"product_name": "二甲胺水溶液", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1555.html"},
    {"product_name": "二乙醇胺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1483.html"},
    {"product_name": "富马酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1593.html"},
    {"product_name": "过硫酸铵", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1474.html"},
    {"product_name": "过硫酸钾", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1508.html"},
    {"product_name": "过硫酸钠", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1486.html"},
    {"product_name": "环氧丙烷", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-438.html"},
    {"product_name": "环氧氯丙烷", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-439.html"},
    {"product_name": "环氧树脂", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1304.html"},
    {"product_name": "环氧乙烷", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-856.html"},
    {"product_name": "黄磷", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-708.html"},
    {"product_name": "甲醇", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-817.html"},
    {"product_name": "甲醛", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-778.html"},
    {"product_name": "焦亚硫酸钠", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-648.html"},
    {"product_name": "聚丙烯酰胺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1283.html"},
    {"product_name": "聚合MDI", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-975.html"},
    {"product_name": "磷酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-709.html"},
    {"product_name": "硫磺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-427.html"},
    {"product_name": "硫脲", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1497.html"},
    {"product_name": "硫酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-236.html"},
    {"product_name": "硫酸二甲酯", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1693.html"},
    {"product_name": "硫酸二乙酯", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1668.html"},
    {"product_name": "尿素", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-89.html"},
    {"product_name": "轻质纯碱", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-226.html"},
    {"product_name": "三乙醇胺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1470.html"},
    {"product_name": "双氰胺", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1727.html"},
    {"product_name": "双氧水", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-758.html"},
    {"product_name": "顺酐", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-660.html"},
    {"product_name": "盐酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-355.html"},
    {"product_name": "一水柠檬酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1471.html"},
    {"product_name": "衣康酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1591.html"},
    {"product_name": "乙二醇丁醚", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1465.html"},
    {"product_name": "异丙醇", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-941.html"},
    {"product_name": "异辛醇", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-489.html"},
    {"product_name": "油酸", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1558.html"},
    {"product_name": "有机硅DMC", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-751.html"},
    {"product_name": "元明粉", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1504.html"},
    {"product_name": "精萘", "industry": "化工", "source_url": "https://www.100ppi.com/rawmex/detail-1655.html"},

    # ========== 能源（3个品类）==========
    {"product_name": "液化天然气", "industry": "能源", "source_url": "https://www.100ppi.com/rawmex/detail-897.html"},
    {"product_name": "Brent原油", "industry": "能源", "source_url": "https://www.100ppi.com/rawmex/detail-1127.html"},
    {"product_name": "WTI原油", "industry": "能源", "source_url": "https://www.100ppi.com/rawmex/detail-1036.html"},

    # ========== 农副（2个品类）==========
    {"product_name": "玉米", "industry": "农副", "source_url": "https://www.100ppi.com/rawmex/detail-274.html"},
    {"product_name": "棕榈油", "industry": "农副", "source_url": "https://www.100ppi.com/rawmex/detail-820.html"},

    # ========== 有色（2个品类）==========
    {"product_name": "黄金", "industry": "有色", "source_url": "https://www.100ppi.com/rawmex/detail-551.html"},
    {"product_name": "金属硅", "industry": "有色", "source_url": "https://www.100ppi.com/rawmex/detail-238.html"},
]


def batch_import():
    """批量导入产品"""
    url = f"{BASE_URL}/api/v1/products/batch"

    payload = {"products": PRODUCTS}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"批量导入完成!")
        print(f"总数: {result['total']}")
        print(f"创建: {result['created']}")
        print(f"跳过: {result['skipped']}")
        print()
        print("详情:")
        for r in result['results']:
            status = r['status']
            name = r['product_name']
            if status == 'created':
                print(f"  [创建] {name}")
            else:
                print(f"  [跳过] {name} - {r.get('reason', '')}")

        return result
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到后端服务，请确保 FastAPI 服务正在运行 (uvicorn backend.main:app)")
        return None
    except Exception as e:
        print(f"错误: {e}")
        return None


if __name__ == "__main__":
    batch_import()