"""
预警服务 - 价格预警触发逻辑
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.database import AlertConfig, AlertRecord, PriceRecord, Product


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

    # 获取最新价格记录
    if triggered_price is not None:
        latest_record = session.query(PriceRecord).filter(
            PriceRecord.product_id == product_id
        ).order_by(PriceRecord.record_date.desc()).first()
        current_price = triggered_price
    else:
        latest_record = session.query(PriceRecord).filter(
            PriceRecord.product_id == product_id
        ).order_by(PriceRecord.record_date.desc()).first()
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
            prev_record = session.query(PriceRecord).filter(
                PriceRecord.product_id == product_id,
                PriceRecord.record_date < (latest_record.record_date if latest_record else datetime.now().date())
            ).order_by(PriceRecord.record_date.desc()).first()

            if prev_record and prev_record.price > 0:
                change_rate = ((current_price - prev_record.price) / prev_record.price) * 100
                if config.change_percent is not None and abs(change_rate) > config.change_percent:
                    triggered = True
                    message = f"价格变化率超过阈值：当前变化率 {change_rate:.2f}% > 阈值 {config.change_percent}%"

        elif config.alert_type == "trend":
            # 趋势预警：价格涨跌时触发（需要至少两条记录）
            prev_record = session.query(PriceRecord).filter(
                PriceRecord.product_id == product_id,
                PriceRecord.id != (latest_record.id if latest_record else 0)
            ).order_by(PriceRecord.record_date.desc()).first()

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