import re
import sys
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright

from backend.scrapers.base import BaseScraper, ScrapedItem
from backend.models.database import get_session, Product, PriceRecord, ScraperLog, ProductCategory
from backend.services.alert_service import check_and_trigger_alerts


class ShengyisheScraper(BaseScraper):
    """生意社化工价格爬虫 - 使用 Playwright 绕过反爬"""

    BASE_URL = "https://www.100ppi.com"
    SOURCE_KEY = "shengyishe"

    def __init__(self, name: str = "shengyishe"):
        super().__init__(name)
        self._product_industry_map = {}

    def get_entry_urls(self) -> List[str]:
        """从数据库获取已导入产品的 source_url（去重）"""
        session = get_session()
        try:
            products = session.query(Product).filter(
                Product.source_url.isnot(None),
                Product.is_active == True
            ).all()

            # 去重，每个URL只爬一次
            urls = []
            seen_urls = set()
            for p in products:
                if p.source_url and p.source_url not in seen_urls:
                    urls.append(p.source_url)
                    seen_urls.add(p.source_url)
                    self._product_industry_map[p.source_url] = p.industry

            print(f"从数据库获取到 {len(urls)} 个唯一产品URL")
            return urls
        except Exception as e:
            print(f"数据库读取失败: {e}")
            return []
        finally:
            session.close()

    def parse_price(self, price_str: str) -> Optional[float]:
        """解析价格字符串，提取数值"""
        if not price_str:
            return None
        match = re.search(r'([\d,]+\.?\d*)', price_str.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def scrape_page(self, url: str) -> List[Dict]:
        """爬取单个产品详情页或列表页，提取基准价和详细报价"""
        industry = self._product_industry_map.get(url, "化工")
        print(f"  正在爬取 [{industry}]: {url}")

        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=30000, wait_until='networkidle')
                page.wait_for_timeout(1000)

                # 判断是列表页还是详情页
                if 'plist-' in url:
                    # 列表页：解析所有报价行，按日期和产品分组，计算基准价
                    rows = self._parse_list_page(page, industry)
                    if rows:
                        grouped = self._group_by_date_and_calculate_benchmark(rows)
                        if grouped:
                            # 按日期分组，每组包含多个产品
                            from collections import defaultdict
                            by_date = defaultdict(list)
                            for g in grouped:
                                by_date[g['date']].append(g)

                            # 取最新一天的数据（该天包含所有产品）
                            latest_date = max(by_date.keys())
                            latest_items = by_date[latest_date]
                            for item_data in latest_items:
                                item_list = self._create_price_items(item_data, url, industry)
                                results.extend(item_list)
                else:
                    # 详情页：使用原有逻辑
                    if industry == "化工":
                        results = self._parse_chemical_detail(page)
                    elif industry == "能源":
                        results = self._parse_energy_detail(page)
                    elif industry == "农副":
                        results = self._parse_agri_detail(page)
                    elif industry == "有色":
                        results = self._parse_nonferrous_detail(page)
                    else:
                        results = self._parse_chemical_detail(page)

                    # 如果行业解析方法返回空，fallback 到基准价
                    if not results:
                        price_data = self._parse_benchmark_price(page, industry)
                        if price_data:
                            results.append(price_data)

            except Exception as e:
                print(f"  页面加载失败: {e}")
            finally:
                browser.close()

        for r in results:
            r['source_url'] = url
            r['industry'] = industry

        print(f"  获取到 {len(results)} 条数据")
        return results

    def _parse_list_page(self, page, industry: str) -> List[Dict]:
        """
        统一解析列表页表格（四个行业通用）
        返回: 当日所有报价行的解析结果
        """
        results = []
        try:
            table = page.query_selector('table.lp-table.mb15')
            if not table:
                table = page.query_selector('table.lp-table')
            if not table:
                return results

            rows = table.query_selector_all('tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 8:
                    continue

                product_name = cells[0].text_content().strip()
                if not product_name or product_name == '商品名称':
                    continue

                spec_text = cells[1].text_content().strip()     # 规格
                brand = cells[2].text_content().strip()          # 品牌/产地
                price_str = cells[3].text_content().strip()      # 报价
                price_type = cells[4].text_content().strip()     # 报价类型
                region = cells[5].text_content().strip()          # 交货地
                supplier = cells[6].text_content().strip()        # 交易商
                publish_date = cells[7].text_content().strip()    # 发布时间

                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                parsed_spec = self._parse_spec_text(spec_text, industry)

                results.append({
                    'product_name': product_name,
                    'spec_raw': spec_text,
                    'brand': brand,
                    'price': price,
                    'price_str': price_str,
                    'price_type': price_type,
                    'region': region,
                    'supplier': supplier,
                    'publish_date': publish_date,
                    'industry': industry,
                    'parsed_spec': parsed_spec
                })
        except Exception as e:
            print(f"  列表页解析失败: {e}")

        return results

    def _group_by_date_and_calculate_benchmark(self, rows: List[Dict]) -> List[Dict]:
        """
        按日期分组，计算每日的基准价（按产品分组计算）
        """
        from collections import defaultdict

        by_date = defaultdict(list)
        for row in rows:
            by_date[row['publish_date']].append(row)

        results = []
        for date, day_rows in by_date.items():
            # 先按产品分组，计算每个产品的基准价
            by_product = defaultdict(list)
            for row in day_rows:
                by_product[row['product_name']].append(row)

            product_results = []
            for product_name, product_rows in by_product.items():
                prices = [r['price'] for r in product_rows]
                benchmark = sum(prices) / len(prices) if prices else 0

                product_results.append({
                    'date': date,
                    'product_name': product_name,
                    'benchmark': round(benchmark, 2),
                    'quote_count': len(product_rows),
                    'details': product_rows
                })

            results.extend(product_results)

        return results

    def _parse_spec_text(self, spec_text: str, industry: str) -> Dict:
        """
        从规格文本中解析行业特有信息
        """
        result = {}

        if industry == '农副':
            if '分类:' in spec_text:
                result['分类'] = spec_text.split('分类:')[1].split(';')[0]
            match = re.search(r'熔点\(℃\):([\d]+);?', spec_text)
            if match:
                result['熔点'] = match.group(1) + '℃'

        elif industry == '能源':
            if '类别:' in spec_text:
                result['类别'] = spec_text.split('类别:')[1]

        elif industry == '有色':
            match = re.search(r'Au不小于\(%\):([\d.]+)', spec_text)
            if match:
                result['纯度'] = match.group(1) + '%'
            result['品名'] = '黄金'

        elif industry == '化工':
            if '品级:' in spec_text:
                result['品级'] = spec_text.split('品级:')[1].rstrip(';')
            purity_match = re.search(r'(\d+\.?\d*%以上?)', spec_text)
            if not purity_match:
                purity_match = re.search(r'(\d+元以上)', spec_text)
            if purity_match:
                result['纯度描述'] = purity_match.group(1)

        return result

    def _create_price_items(self, grouped_data: Dict, source_url: str, industry: str) -> List[Dict]:
        """
        从分组数据创建价格项
        grouped_data 格式: {date, product_name, benchmark, quote_count, details}
        """
        details = grouped_data['details']
        if not details:
            return []

        first = details[0]
        benchmark = grouped_data['benchmark']

        item = {
            'name': grouped_data['product_name'],
            'specification': '',  # 规格在详细报价中
            'brand': '',  # 品牌在详细报价中
            'price': benchmark,  # 基准价
            'price_str': f'{benchmark}元/吨',
            'price_type': first['price_type'],
            'region': '',  # 交货地在详细报价中
            'supplier': '',  # 供应商在详细报价中
            'date': grouped_data['date'],
            'unit': '元/吨' if industry in ['化工', '农副'] else ('元/立方米' if industry == '能源' else '元/克'),
            'price_category': '现货',
            'industry': industry,
            'source_url': source_url,
            'extra_data': {
                '报价类型': first['price_type'],
                '基准价': benchmark,
                '详细报价': details,  # 该产品的所有详细报价
                '行业特有': first.get('parsed_spec', {})
            }
        }
        return [item]

    def _parse_benchmark_price(self, page, industry: str) -> Optional[Dict]:
        """解析详情页的基准价"""
        try:
            # 查找价格元素
            price_el = page.query_selector('.price-fb01_1')
            price_str = price_el.inner_text() if price_el else ""
            price = self.parse_price(price_str)
            if price is None or price <= 0:
                return None

            # 查找日期
            date_el = page.query_selector('.post_date_li')
            date_text = date_el.inner_text() if date_el else ""
            import re
            date_match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', date_text)
            record_date = date_match.group(1) if date_match else ""
            # 转换为 YYYY-MM-DD HH:MM 格式
            if record_date:
                # record_date is like "05-15 14:12" -> "2026-05-15 14:12"
                record_date = f"2026-{record_date.replace('-', '-').replace(' ', ' ')}"

            # 查找产品名称 - 多种方法依次尝试
            product_name = ""
            name_el = page.query_selector('.pricename a')
            if name_el:
                product_name = name_el.inner_text().strip()
            if not product_name:
                # 尝试从 .pricename div 获取
                name_el2 = page.query_selector('.pricename')
                if name_el2:
                    text = name_el2.inner_text() or ""
                    product_name = text.split('\n')[0].strip()
            if not product_name:
                # 尝试从页面标题获取 "轻质纯碱基准价 - 生意社..."
                title = page.title() or ""
                if '基准价' in title:
                    product_name = title.split('基准价')[0].strip()
            if not product_name:
                # 兜底：从 URL 提取
                import re
                match = re.search(r'detail-(\d+)\.html', url)
                product_name = match.group(1) if match else ""

            # 获取 extra_data（按行业）
            extra_data = {'报价类型': '基准价'}
            if industry == "化工":
                extra_data.update({'规格': '', '品牌/产地': '', '报价类型': '基准价'})
            elif industry == "能源":
                extra_data.update({'规格': '', '数量': '', '现货类型': '基准价', '有效时间': ''})
            elif industry == "农副":
                extra_data.update({'分类': '', '等级/熔点': '', '品牌/产地': '', '报价类型': '基准价'})
            elif industry == "有色":
                extra_data.update({'品名/纯度': '', '品牌/产地': '', '报价类型': '基准价'})

            return {
                'name': product_name,
                'specification': '',
                'brand': '',
                'price': price,
                'price_str': price_str,
                'price_type': '基准价',
                'region': '',
                'supplier': '生意社',
                'date': record_date,
                'unit': '元/吨' if industry == '化工' else ('元/吨' if industry == '农副' else ('元/立方米' if industry == '能源' else '元/克')),
                'price_category': '现货',
                'extra_data': extra_data
            }
        except Exception as e:
            print(f"  基准价解析失败: {e}")
            return None

    def _parse_chemical_detail(self, page) -> List[Dict]:
        """化工详情页解析 - 解析产品详细价格表格"""
        results = []
        try:
            rows = page.query_selector_all('table.rmbpj tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 5:
                    continue

                # 商品名称在第一个 td
                name = cells[0].text_content() or ""
                name = name.strip()
                if not name or name == '产品' or '查看更多' in name:
                    continue

                # 价格列是第二个 td
                price_str = cells[1].text_content() or ""
                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                # 其他列：较昨日等
                # 提取品牌（可能在其他单元格）
                brand = ''
                region = ''
                for cell in cells[1:]:
                    text = cell.text_content() or ""
                    if '华东' in text or '华南' in text or '华北' in text:
                        region = text.strip()
                        break

                results.append({
                    'name': name,
                    'specification': '',
                    'brand': brand,
                    'price': price,
                    'price_str': price_str.strip(),
                    'price_type': '市场价',
                    'region': region,
                    'supplier': '生意社',
                    'date': '',
                    'unit': '元/吨',
                    'price_category': '现货',
                    'extra_data': {
                        '规格': '',
                        '品牌/产地': brand,
                        '报价类型': '市场价'
                    }
                })
        except Exception as e:
            print(f"  化工解析失败: {e}")
        return results

    def _parse_energy_detail(self, page) -> List[Dict]:
        """能源详情页解析（液化天然气/原油）"""
        results = []
        try:
            rows = page.query_selector_all('table tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 7:
                    continue

                spec = cells[0].text_content() or ""
                spec = spec.strip()
                if not spec or spec in ['规格', '规格属性']:
                    continue

                price_str = cells[1].text_content() or ""
                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                quantity = cells[2].text_content() or ""
                spot_type = cells[3].text_content() or ""
                region = cells[4].text_content() or ""
                date = cells[5].text_content() or ""
                valid_time = cells[6].text_content() or ""

                results.append({
                    'name': '',
                    'specification': spec.strip(),
                    'brand': '',
                    'price': price,
                    'price_str': price_str.strip(),
                    'price_type': '市场价',
                    'region': region.strip(),
                    'supplier': '',
                    'date': date.strip(),
                    'unit': '元/立方米',
                    'price_category': '现货',
                    'extra_data': {
                        '规格': spec.strip(),
                        '数量': quantity.strip(),
                        '现货类型': spot_type.strip(),
                        '有效时间': valid_time.strip()
                    }
                })
        except Exception as e:
            print(f"  能源解析失败: {e}")
        return results

    def _parse_agri_detail(self, page) -> List[Dict]:
        """农副详情页解析（玉米/棕榈油）"""
        results = []
        try:
            rows = page.query_selector_all('table tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 6:
                    continue

                name = cells[0].text_content() or ""
                name = name.strip()
                if not name or name == '商品名称':
                    continue

                price_str = cells[3].text_content() or ""
                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                category = cells[1].text_content() or ""
                grade = cells[2].text_content() or ""
                brand = cells[4].text_content() or ""
                price_type = cells[5].text_content() or ""
                region = page.query_selector('.region, .location') or None
                region_text = region.text_content() if region else ""
                date = page.query_selector('.date, .publish-date') or None
                date_text = date.text_content() if date else ""

                results.append({
                    'name': name,
                    'specification': '',
                    'brand': brand.strip(),
                    'price': price,
                    'price_str': price_str.strip(),
                    'price_type': price_type.strip() or '市场价',
                    'region': region_text.strip(),
                    'supplier': '',
                    'date': date_text.strip(),
                    'unit': '元/吨',
                    'price_category': '现货',
                    'extra_data': {
                        '分类': category.strip(),
                        '等级/熔点': grade.strip(),
                        '品牌/产地': brand.strip(),
                        '报价类型': price_type.strip() or '市场价'
                    }
                })
        except Exception as e:
            print(f"  农副解析失败: {e}")
        return results

    def _parse_nonferrous_detail(self, page) -> List[Dict]:
        """有色详情页解析（黄金/金属硅）"""
        results = []
        try:
            rows = page.query_selector_all('table tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 5:
                    continue

                # 产品分类在第一个 td
                category = cells[0].text_content() or ""
                category = category.strip()
                if not category or category == '产品分类' or '查看更多' in category:
                    continue

                # 基准价在第二个 td (cells[1])，实时价格在 cells[4]
                # 使用实时价格（cells[4]）作为主价格
                price_str = cells[4].text_content() or ""
                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                # 产品名称在 cells[2]
                name = cells[2].text_content() or ""
                # 产区在 cells[3]
                region = cells[3].text_content() or ""
                # 时间在最后一个 td
                date = cells[-1].text_content() or ""

                # 从品名中提取纯度作为规格
                spec = name.split()[-1] if name else ''

                results.append({
                    'name': name.strip(),
                    'specification': spec,
                    'brand': region.strip(),  # 产区就是品牌/产地
                    'price': price,
                    'price_str': price_str.strip(),
                    'price_type': '市场价',
                    'region': region.strip(),
                    'supplier': '',
                    'date': date.strip(),
                    'unit': '元/克',
                    'price_category': '现货',
                    'extra_data': {
                        '品名/纯度': name.strip(),
                        '品牌/产地': region.strip(),
                        '报价类型': '市场价'
                    }
                })
        except Exception as e:
            print(f"  有色解析失败: {e}")
        return results

    def run(self) -> List[ScrapedItem]:
        """执行爬取流程"""
        urls = self.get_entry_urls()
        if not urls:
            print("未获取到任何产品URL")
            return []

        all_results = []
        seen = set()

        for url in urls:
            items = self.scrape_page(url)
            for item in items:
                # 对于列表页数据，supplier为空，不作为去重依据
                supplier_part = item['supplier'] if item['supplier'] else 'NOSUPPLIER'
                key = f"{item['name']}|{item['specification']}|{supplier_part}|{item['date']}"
                if key not in seen:
                    seen.add(key)
                    all_results.append(self._dict_to_scraped_item(item))

            import time
            time.sleep(0.5)

        print(f"\n生意社爬取完成，共获取 {len(all_results)} 条去重后数据")
        return all_results

    def scrape_historical_prices(self, product_id: int, days: int = 365) -> List[Dict]:
        """爬取指定产品的历史价格数据"""
        from datetime import datetime, timedelta

        session = get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product or not product.source_url:
                print(f"  产品 {product_id} 未找到或无 source_url")
                return []

            url = product.source_url
            industry = product.industry or "化工"
            print(f"  正在爬取历史数据 [{industry}]: {url}")

        finally:
            session.close()

        results = []

        # 从详情页获取图表iframe的src
        chart_url = f"https://www.100ppi.com/graph/cindex.php?f=graph_ppid_ave&ppid={self._extract_product_id(url)}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                # 访问图表iframe获取ECharts中的数据
                page.goto(chart_url, timeout=60000, wait_until='networkidle')
                page.wait_for_timeout(3000)

                # 从ECharts实例获取历史价格数据
                chart_data = page.evaluate('''
                    () => {
                        try {
                            const chartDom = document.querySelector('[id="container"]');
                            if (chartDom && window.echarts) {
                                const inst = echarts.getInstanceByDom(chartDom);
                                if (inst) {
                                    const opt = inst.getOption();
                                    return {
                                        dates: opt.xAxis[0].data,
                                        prices: opt.series[0].data
                                    };
                                }
                            }
                            return null;
                        } catch(e) {
                            return null;
                        }
                    }
                ''')

                if chart_data and chart_data.get('dates') and chart_data.get('prices'):
                    dates = chart_data['dates']
                    prices = chart_data['prices']
                    for i, date_str in enumerate(dates):
                        if i < len(prices):
                            price = prices[i]
                            if price and price > 0:
                                results.append({
                                    'date': date_str,
                                    'price': float(price),
                                    'change': '',
                                    'change_percent': 0.0,
                                    'trend': '平',
                                    'industry': industry
                                })
                    print(f"  从ECharts获取到 {len(results)} 条历史数据")

            except Exception as e:
                print(f"  图表页面加载失败: {e}")
            finally:
                browser.close()

        # 过滤掉数据库中已存在的日期（增量更新）
        results = self._filter_existing_records(product_id, results)

        print(f"  获取到 {len(results)} 条新历史数据")
        return results

    def _extract_product_id(self, url: str) -> str:
        """从URL提取产品ID"""
        match = re.search(r'detail-(\d+)\.html', url)
        return match.group(1) if match else ""

    def _parse_historical_table(self, page, industry: str) -> List[Dict]:
        """解析页面中的历史价格表格"""
        results = []

        try:
            # 尝试多种方式定位历史价格表格
            # 方式1: 查找表格 (历史数据通常在 table 中)
            rows = page.query_selector_all('table tr')

            if rows:
                for row in rows:
                    cells = row.query_selector_all('td')
                    if len(cells) >= 5:
                        # 尝试解析: 日期 | 价格 | 涨跌额 | 涨跌% | 趋势
                        date_text = cells[0].text_content() or ""
                        price_text = cells[1].text_content() or ""
                        change_text = cells[2].text_content() or ""
                        change_pct_text = cells[3].text_content() or ""
                        trend_text = cells[4].text_content() or ""

                        price = self.parse_price(price_text)
                        if price is None or price <= 0:
                            continue

                        # 解析日期
                        record_date = self._parse_historical_date(date_text.strip())
                        if not record_date:
                            continue

                        # 解析涨跌幅
                        change_percent = self._parse_change_percent(change_pct_text)
                        trend = trend_text.strip() if trend_text else self._get_trend_from_change(change_percent)

                        results.append({
                            'date': record_date,
                            'price': price,
                            'change': change_text.strip(),
                            'change_percent': change_percent,
                            'trend': trend,
                            'industry': industry
                        })

            # 方式2: 如果没有找到表格，尝试查找特定div中的历史数据
            if not results:
                # 生意社的历史数据可能在一个特定的div中，如 .history-table 或类似class
                history_divs = page.query_selector_all('[class*="history"], [class*="table"], [id*="history"]')
                for div in history_divs:
                    text = div.inner_text() or ""
                    # 尝试从文本中提取日期和价格
                    lines = text.split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            date_str = parts[0]
                            price_str = parts[1] if len(parts) > 1 else ""
                            price = self.parse_price(price_str)
                            if price and price > 0:
                                record_date = self._parse_historical_date(date_str)
                                if record_date:
                                    results.append({
                                        'date': record_date,
                                        'price': price,
                                        'change': '',
                                        'change_percent': 0.0,
                                        'trend': '平',
                                        'industry': industry
                                    })

        except Exception as e:
            print(f"  历史价格表格解析失败: {e}")

        return results

    def _parse_historical_date(self, date_str: str) -> Optional[str]:
        """解析历史价格日期字符串"""
        if not date_str:
            return None

        # 尝试多种日期格式
        date_str = date_str.strip()

        # 格式1: YYYY-MM-DD
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

        # 格式2: YYYY/MM/DD
        match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

        # 格式3: MM-DD (需要补充年份)
        match = re.search(r'(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year = datetime.now().year
            return f"{year}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"

        return None

    def _parse_change_percent(self, change_str: str) -> float:
        """解析涨跌幅字符串"""
        if not change_str:
            return 0.0

        change_str = change_str.strip().replace('%', '')
        try:
            return float(change_str)
        except ValueError:
            return 0.0

    def _get_trend_from_change(self, change_percent: float) -> str:
        """根据涨跌幅确定趋势"""
        if change_percent > 0:
            return "涨"
        elif change_percent < 0:
            return "跌"
        else:
            return "平"

    def _filter_existing_records(self, product_id: int, records: List[Dict]) -> List[Dict]:
        """过滤掉数据库中已存在的记录（按日期）"""
        if not records:
            return []

        session = get_session()
        try:
            # 获取该产品已有的所有日期
            existing_dates = set()
            db_records = session.query(PriceRecord.record_date).filter(
                PriceRecord.product_id == product_id,
                PriceRecord.source == self.SOURCE_KEY
            ).all()
            for r in db_records:
                existing_dates.add(r.record_date.isoformat() if r.record_date else None)

            # 过滤
            filtered = []
            for record in records:
                if record['date'] not in existing_dates:
                    filtered.append(record)

            return filtered
        finally:
            session.close()

    def save_historical_to_db(self, product_id: int, records: List[Dict]) -> int:
        """保存历史价格数据到数据库"""
        if not records:
            return 0

        session = get_session()
        saved_count = 0

        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return 0

            for record in records:
                try:
                    record_date = datetime.strptime(record['date'], "%Y-%m-%d").date()

                    # 检查是否已存在
                    existing = session.query(PriceRecord).filter(
                        PriceRecord.product_id == product_id,
                        PriceRecord.record_date == record_date,
                        PriceRecord.source == self.SOURCE_KEY
                    ).first()

                    if existing:
                        # 更新已有记录
                        existing.price = record['price']
                        existing.trend = record['trend']
                        # 计算涨跌幅：对比该产品昨日收盘价
                        prev_record = session.query(PriceRecord).filter(
                            PriceRecord.product_id == product_id,
                            PriceRecord.record_date < record_date,
                            PriceRecord.source == self.SOURCE_KEY
                        ).order_by(PriceRecord.record_date.desc()).first()
                        if prev_record and prev_record.price > 0:
                            existing.change_percent = round(((record['price'] - prev_record.price) / prev_record.price) * 100, 2)
                            existing.trend = "涨" if existing.change_percent > 0 else "跌" if existing.change_percent < 0 else "平"
                    else:
                        # 新增记录 - 先查上一条计算涨跌幅
                        prev_record = session.query(PriceRecord).filter(
                            PriceRecord.product_id == product_id,
                            PriceRecord.record_date < record_date,
                            PriceRecord.source == self.SOURCE_KEY
                        ).order_by(PriceRecord.record_date.desc()).first()
                        if prev_record and prev_record.price > 0:
                            change_pct = round(((record['price'] - prev_record.price) / prev_record.price) * 100, 2)
                            trend_val = "涨" if change_pct > 0 else "跌" if change_pct < 0 else "平"
                        else:
                            change_pct = 0.0
                            trend_val = "平"

                        price_record = PriceRecord(
                            product_id=product_id,
                            price=record['price'],
                            unit=product.unit or "元/吨",
                            price_original=f"{record['price']}元/吨",
                            price_category='现货',
                            price_type='基准价',
                            trend=trend_val,
                            change_percent=change_pct,
                            source=self.SOURCE_KEY,
                            region='',
                            supplier='生意社',
                            brand='',
                            specification='',
                            extra_data={'报价类型': '基准价'},
                            record_date=record_date
                        )
                        session.add(price_record)
                    saved_count += 1

                except Exception as e:
                    print(f"  保存历史记录失败: {e}")
                    continue

            session.commit()
        except Exception as e:
            print(f"  数据库事务失败: {e}")
            session.rollback()
        finally:
            session.close()

        return saved_count

    def _dict_to_scraped_item(self, data: Dict) -> ScrapedItem:
        """将字典转换为 ScrapedItem"""
        name = data['name']
        specification = data.get('specification', '')
        source_url = data.get('source_url', '')

        # 尝试从数据库获取已存在的 product_code（批量导入时用 product_name + source_url 生成）
        product_code = self._get_product_code_from_db(source_url, name)
        if not product_code:
            # 兜底：使用 name + specification 生成
            product_code = self._generate_code(name, specification)

        price_str = data.get('price_str', '')
        unit = data.get('unit', '元/吨')
        price_category = data.get('price_category', '现货')
        extra_data = data.get('extra_data', {})

        return ScrapedItem(
            product_code=product_code,
            product_name=name,
            price=data['price'],
            price_type=data.get('price_type', '市场价'),
            trend="平",
            change_percent=0.0,
            record_date=data['date'] or datetime.now().strftime("%Y-%m-%d"),
            raw_data=data,
            unit=unit,
            price_original=price_str,
            price_category=price_category,
            extra_data=extra_data
        )

    def _get_product_code_from_db(self, source_url: str, product_name: str) -> Optional[str]:
        """从数据库根据 product_name 获取 product_code"""
        session = get_session()
        try:
            # 用 product_name 查找（列表页一个产品只对应一条基准价记录）
            product = session.query(Product).filter(
                Product.product_name == product_name,
                Product.is_active == True
            ).first()
            if product:
                return product.product_code
            return None
        finally:
            session.close()

    def _generate_code(self, name: str, specification: str = None) -> str:
        """生成产品编码"""
        import hashlib
        raw = f"{name}|{specification or ''}"
        return hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    def parse_product_list(self, html: str) -> List[str]:
        """BaseScraper 要求的方法，新流程中由 get_entry_urls() 提供 URL"""
        return []

    def parse_product_detail(self, html: str, url: str) -> Optional[ScrapedItem]:
        """BaseScraper 要求的方法，新流程中由 scrape_page() 解析详情页"""
        return None

    def save_to_db(self, items: List[ScrapedItem]) -> int:
        """保存到数据库（支持同产品同日期不同地区/供应商的重复数据）"""
        session = get_session()
        saved_count = 0

        for item in items:
            try:
                product = session.query(Product).filter_by(product_code=item.product_code).first()
                if not product:
                    product = Product(
                        product_code=item.product_code,
                        product_name=item.product_name,
                        industry=item.raw_data.get('industry', '化工'),
                        category="化工",
                        unit=item.unit or "元/吨",
                        source=self.name,
                        source_url=item.raw_data.get('source_url')
                    )
                    session.add(product)
                    session.flush()

                    # 创建 ProductCategory 关联
                    from backend.scripts.seed_categories import match_product_to_categories
                    matched_ids = match_product_to_categories(product.product_name, session)
                    for cat_id in matched_ids:
                        existing_assoc = session.query(ProductCategory).filter(
                            ProductCategory.product_id == product.id,
                            ProductCategory.category_id == cat_id
                        ).first()
                        if not existing_assoc:
                            assoc = ProductCategory(product_id=product.id, category_id=cat_id)
                            session.add(assoc)

                from datetime import datetime as dt, date

                record_date_str = item.record_date
                # Handle both date-only and datetime formats
                if ' ' in record_date_str or ':' in record_date_str:
                    # Format: "2026-05-15 14:12" or "2026-05-15 14:12:00"
                    record_date_str = record_date_str.split('.')[0]  # Remove microseconds if any
                    record_date = dt.strptime(record_date_str, "%Y-%m-%d %H:%M").date()
                else:
                    record_date = dt.strptime(record_date_str, "%Y-%m-%d").date()

                # 计算涨跌幅：对比该产品昨日收盘价
                prev_record = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product.id,
                    PriceRecord.record_date < record_date
                ).order_by(PriceRecord.record_date.desc()).first()

                if prev_record and prev_record.price > 0:
                    change_percent = round(((item.price - prev_record.price) / prev_record.price) * 100, 2)
                    trend = "涨" if change_percent > 0 else "跌" if change_percent < 0 else "平"
                else:
                    change_percent = 0.0
                    trend = "平"

                # 检查是否已存在相同 product_id + record_date + source + region + supplier 的记录
                region_val = item.raw_data.get('region')
                supplier_val = item.raw_data.get('supplier')
                existing = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product.id,
                    PriceRecord.record_date == record_date,
                    PriceRecord.source == self.name,
                    PriceRecord.region == region_val,
                    PriceRecord.supplier == supplier_val
                ).first()

                if existing:
                    # 更新已有记录
                    existing.price = item.price
                    existing.unit = item.unit
                    existing.price_original = item.price_original
                    existing.price_category = item.price_category
                    existing.price_type = item.price_type or "市场价"
                    existing.trend = trend
                    existing.change_percent = change_percent
                    existing.brand = item.raw_data.get('brand')
                    existing.specification = item.raw_data.get('specification')
                    existing.extra_data = item.extra_data
                else:
                    record = PriceRecord(
                        product_id=product.id,
                        price=item.price,
                        unit=item.unit,
                        price_original=item.price_original,
                        price_category=item.price_category,
                        price_type=item.price_type or "市场价",
                        trend=trend,
                        change_percent=change_percent,
                        source=self.name,
                        region=region_val,
                        supplier=supplier_val,
                        brand=item.raw_data.get('brand'),
                        specification=item.raw_data.get('specification'),
                        extra_data=item.extra_data,
                        record_date=record_date
                    )
                    session.add(record)
                saved_count += 1
            except Exception as e:
                print(f"Error saving item: {e}")
                session.rollback()

        session.commit()

        # 检查预警触发（针对每个保存的产品）
        for item in items:
            product = session.query(Product).filter_by(product_code=item.product_code).first()
            if product:
                check_and_trigger_alerts(session, product.id, item.price)

        session.close()
        return saved_count

    def log_scraper_run(self, status: str, items_scraped: int, error_message: str = None):
        """记录爬虫运行日志"""
        session = get_session()
        log = ScraperLog(
            scraper_name=self.name,
            status=status,
            items_scraped=items_scraped,
            error_message=error_message,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        session.add(log)
        session.commit()
        session.close()


def run_scraper():
    """运行爬虫"""
    scraper = ShengyisheScraper()
    scraper.log_scraper_run("running", 0)

    try:
        items = scraper.run()
        saved = scraper.save_to_db(items)
        scraper.log_scraper_run("success", saved)
        print(f"Scraped {len(items)} items, saved {saved} to database.")
    except Exception as e:
        scraper.log_scraper_run("failed", 0, str(e))
        print(f"Scraper failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_scraper()