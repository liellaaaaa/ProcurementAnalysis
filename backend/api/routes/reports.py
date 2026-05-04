from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from datetime import date, timedelta
from io import BytesIO
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.database import get_session, Product, PriceRecord

router = APIRouter(prefix="/api/v1/reports", tags=["报表生成"])

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def get_date_range(report_type: str):
    """获取报表日期范围"""
    today = date.today()
    if report_type == "weekly":
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    elif report_type == "monthly":
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return month_start, month_end
    return today - timedelta(days=7), today


@router.get("/pdf")
async def generate_pdf_report(report_type: str = Query("weekly", enum=["weekly", "monthly"])):
    """生成 PDF 报表"""
    if not HAS_REPORTLAB:
        return {"error": "reportlab 未安装，请运行: pip install reportlab"}

    session = get_session()
    start_date, end_date = get_date_range(report_type)

    title = "周报" if report_type == "weekly" else "月报"
    filename = f"price_{report_type}_{end_date.isoformat()}.pdf"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=1)
    elements.append(Paragraph(f"采购价格{title}", title_style))
    elements.append(Spacer(1, 0.5 * cm))

    period_text = f"统计周期: {start_date.isoformat()} 至 {end_date.isoformat()}"
    elements.append(Paragraph(period_text, styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    stats = session.query(
        func.count(func.distinct(PriceRecord.product_id)).label('product_count'),
        func.count(PriceRecord.id).label('record_count'),
        func.max(PriceRecord.price).label('max_price'),
        func.min(PriceRecord.price).label('min_price'),
        func.avg(PriceRecord.price).label('avg_price')
    ).filter(
        PriceRecord.record_date >= start_date,
        PriceRecord.record_date <= end_date
    ).first()

    overview_data = [
        ["指标", "数值"],
        ["产品数量", str(stats.product_count or 0)],
        ["价格记录数", str(stats.record_count or 0)],
        ["最高价", f"¥{stats.max_price:.2f}" if stats.max_price else "-"],
        ["最低价", f"¥{stats.min_price:.2f}" if stats.min_price else "-"],
        ["平均价", f"¥{stats.avg_price:.2f}" if stats.avg_price else "-"],
    ]

    overview_table = Table(overview_data, colWidths=[5 * cm, 5 * cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409eff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f7fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dcdfe6')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 1 * cm))

    products_data = session.query(
        Product.product_name,
        func.max(PriceRecord.price).label('max_price'),
        func.min(PriceRecord.price).label('min_price'),
        func.avg(PriceRecord.price).label('avg_price'),
        func.count(PriceRecord.id).label('record_count')
    ).join(PriceRecord).filter(
        PriceRecord.record_date >= start_date,
        PriceRecord.record_date <= end_date
    ).group_by(Product.id).order_by(func.avg(PriceRecord.price).desc()).limit(20).all()

    detail_header = [["产品名称", "最高价", "最低价", "均价", "记录数"]]
    detail_data = [[
        p.product_name[:20],
        f"¥{p.max_price:.2f}" if p.max_price else "-",
        f"¥{p.min_price:.2f}" if p.min_price else "-",
        f"¥{p.avg_price:.2f}" if p.avg_price else "-",
        str(p.record_count)
    ] for p in products_data]

    detail_table = Table(detail_header + detail_data, colWidths=[6 * cm, 3 * cm, 3 * cm, 3 * cm, 2 * cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#409eff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dcdfe6')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    buffer.seek(0)

    session.close()

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/excel")
async def generate_excel_report(report_type: str = Query("weekly", enum=["weekly", "monthly"])):
    """生成 Excel 报表"""
    if not HAS_OPENPYXL:
        return {"error": "openpyxl 未安装，请运行: pip install openpyxl"}

    session = get_session()
    start_date, end_date = get_date_range(report_type)

    wb = Workbook()

    products_ws = wb.active
    products_ws.title = "产品列表"
    products = session.query(Product).filter(Product.is_active == True).all()
    products_ws.append(["ID", "产品编码", "产品名称", "分类", "单位", "数据源"])
    for p in products:
        products_ws.append([p.id, p.product_code, p.product_name, p.category, p.unit, p.source])

    history_ws = wb.create_sheet("价格历史")
    history_records = session.query(PriceRecord, Product.product_name).join(Product).filter(
        PriceRecord.record_date >= start_date,
        PriceRecord.record_date <= end_date
    ).order_by(PriceRecord.record_date.desc()).all()
    history_ws.append(["日期", "产品", "价格", "趋势", "涨跌%", "来源"])
    for record, pname in history_records:
        history_ws.append([
            record.record_date.isoformat(),
            pname,
            record.price,
            record.trend,
            record.change_percent,
            record.source
        ])

    summary_ws = wb.create_sheet("统计汇总")
    stats = session.query(
        Product.product_name,
        func.max(PriceRecord.price).label('max_price'),
        func.min(PriceRecord.price).label('min_price'),
        func.avg(PriceRecord.price).label('avg_price'),
        func.count(PriceRecord.id).label('record_count')
    ).join(PriceRecord).filter(
        PriceRecord.record_date >= start_date,
        PriceRecord.record_date <= end_date
    ).group_by(Product.id).order_by(func.avg(PriceRecord.price).desc()).all()

    summary_ws.append(["产品名称", "最高价", "最低价", "均价", "记录数"])
    for s in stats:
        summary_ws.append([
            s.product_name,
            round(s.max_price, 2) if s.max_price else 0,
            round(s.min_price, 2) if s.min_price else 0,
            round(s.avg_price, 2) if s.avg_price else 0,
            s.record_count
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"price_{report_type}_{end_date.isoformat()}.xlsx"
    session.close()

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )