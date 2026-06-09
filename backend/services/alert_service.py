"""
预警服务 - 价格预警触发逻辑
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.database import AlertConfig, AlertRecord, PriceRecord, BenchmarkPrice, Product


def get_latest_price_record(session: Session, product_id: int):
    """获取最新价格记录，优先从 BenchmarkPrice 获取，其次 PriceRecord"""
    # 优先从 BenchmarkPrice 获取（主数据源）
    latest_bp = session.query(BenchmarkPrice).filter(
        BenchmarkPrice.product_id == product_id
    ).order_by(BenchmarkPrice.record_date.desc()).first()

    if latest_bp:
        return latest_bp, 'benchmark'

    # fallback 到 PriceRecord
    latest_pr = session.query(PriceRecord).filter(
        PriceRecord.product_id == product_id
    ).order_by(PriceRecord.record_date.desc()).first()

    if latest_pr:
        return latest_pr, 'price_record'

    return None, None


def get_previous_price_record(session: Session, product_id: int, latest_record_date, source: str):
    """获取上一个周期的价格记录，source 参数决定从哪个表获取"""
    if source == 'benchmark':
        return session.query(BenchmarkPrice).filter(
            BenchmarkPrice.product_id == product_id,
            BenchmarkPrice.record_date < latest_record_date
        ).order_by(BenchmarkPrice.record_date.desc()).first()
    else:
        return session.query(PriceRecord).filter(
            PriceRecord.product_id == product_id,
            PriceRecord.record_date < latest_record_date
        ).order_by(PriceRecord.record_date.desc()).first()


def check_and_trigger_alerts(session: Session, product_id: int, triggered_price: float = None) -> List[AlertRecord]:
    """
    检查并触发预警
    在价格保存后调用，遍历该产品所有激活的预警配置，判断是否触发

    Args:
        session: 数据库会话
        product_id: 产品ID
        triggered_price: 触发预警的价格（可选，如果不传则查询最新价格）

    Returns:
        触发的新预警记录列表
    """
    triggered_alerts = []

    # 查询该产品所有激活的预警配置
    configs = session.query(AlertConfig).filter(
        AlertConfig.product_id == product_id,
        AlertConfig.is_active == True
    ).all()

    if not configs:
        return []

    # 获取最新价格记录（优先从 BenchmarkPrice，其次 PriceRecord）
    if triggered_price is not None:
        latest_record, source = get_latest_price_record(session, product_id)
        current_price = triggered_price
    else:
        latest_record, source = get_latest_price_record(session, product_id)
        current_price = latest_record.price if latest_record else None

    if current_price is None:
        return []

    for config in configs:
        triggered = False
        message = ""

        if config.alert_type == "threshold":
            # 绝对阈值：价格超过 threshold_value 时触发
            if config.threshold_value is not None and current_price > config.threshold_value:
                triggered = True
                message = f"价格超过阈值：当前价格 {current_price} 元/吨 > 阈值 {config.threshold_value} 元/吨"

        elif config.alert_type == "change_rate":
            # 价格变化率：需要对比上次价格
            if latest_record:
                prev_record = get_previous_price_record(
                    session, product_id,
                    latest_record.record_date if hasattr(latest_record, 'record_date') else datetime.now().date(),
                    source
                )
            else:
                prev_record = None

            if prev_record and prev_record.price > 0:
                change_rate = ((current_price - prev_record.price) / prev_record.price) * 100
                if config.change_percent is not None and abs(change_rate) > config.change_percent:
                    triggered = True
                    message = f"价格变化率超过阈值：当前变化率 {change_rate:.2f}% > 阈值 {config.change_percent}%"

        elif config.alert_type == "trend":
            # 趋势预警：价格涨跌时触发（需要至少两条记录）
            if not latest_record:
                continue
            prev_record = get_previous_price_record(
                session, product_id,
                latest_record.record_date if hasattr(latest_record, 'record_date') else datetime.now().date(),
                source
            )

            if prev_record:
                if current_price > prev_record.price:
                    triggered = True
                    message = f"价格上涨提醒：当前 {current_price} 元/吨，较上次 {prev_record.price} 元/吨上涨"
                elif current_price < prev_record.price:
                    triggered = True
                    message = f"价格下跌提醒：当前 {current_price} 元/吨，较上次 {prev_record.price} 元/吨下跌"

        if triggered:
            alert_record = AlertRecord(
                alert_config_id=config.id,
                product_id=product_id,
                alert_message=message,
                triggered_price=current_price,
                triggered_at=datetime.now(),
                is_read=False
            )
            session.add(alert_record)
            triggered_alerts.append(alert_record)

    if triggered_alerts:
        session.commit()

    return triggered_alerts


def check_all_products_alerts(session: Session) -> List[AlertRecord]:
    """
    检查所有产品的预警（管理员手动触发全部检查时使用）
    """
    all_alerts = []
    products = session.query(Product).filter(Product.is_active == True).all()

    for product in products:
        alerts = check_and_trigger_alerts(session, product.id)
        all_alerts.extend(alerts)

    return all_alerts