"""图表生成服务 - 使用 matplotlib 生成图表图片"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from typing import List, Dict, Any
import base64
import numpy
import warnings
import os
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 尝试注册 Windows 中文字体
try:
    from matplotlib.font_manager import FontProperties
    font_path = 'C:/Windows/Fonts/simhei.ttf'
    if os.path.exists(font_path):
        font_prop = FontProperties(fname=font_path)
        # 测试字体
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, '测试', fontproperties=font_prop)
        plt.close(fig)
except Exception:
    pass


def line_chart_to_bytes(
    dates: List[str],
    series_list: List[Dict[str, Any]],
    title: str = "价格走势",
    ylabel: str = "价格 (元/吨)"
) -> BytesIO:
    """生成多产品折线图返回 BytesIO"""
    buf = BytesIO()
    try:
        fig, ax = plt.subplots(figsize=(10, 5))

        colors = ['#00d4ff', '#ff6b6b', '#4ecdc4', '#ffa07a', '#98d8c8', '#dda0dd', '#f0e68c']

        for i, s in enumerate(series_list):
            if not s.get('data'):
                continue
            color = colors[i % len(colors)]
            ax.plot(range(len(s['data'])), s['data'], label=s.get('name', f'Series {i+1}'),
                   marker='o', markersize=3, color=color, linewidth=2)

        # 设置x轴标签
        if dates and len(dates) > 0:
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=30, fontsize=8)

        ax.set_title(title, fontsize=14, pad=15, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=10)
        ax.legend(loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        plt.close('all')
        buf.close()
        raise ValueError(f"折线图生成失败: {str(e)}") from e


def pie_chart_to_bytes(
    sizes: List[float],
    labels: List[str],
    title: str = "价格占比"
) -> BytesIO:
    """生成饼图返回 BytesIO"""
    buf = BytesIO()
    try:
        if not sizes or len(sizes) == 0:
            raise ValueError("饼图数据为空")

        fig, ax = plt.subplots(figsize=(8, 6))

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#DDA0DD', '#F0E68C', '#87CEEB']

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors[:len(sizes)],
            startangle=90,
            pctdistance=0.75,
            labeldistance=1.1
        )

        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title(title, fontsize=14, pad=15, fontweight='bold')

        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        plt.close('all')
        buf.close()
        raise ValueError(f"饼图生成失败: {str(e)}") from e


def bar_chart_to_bytes(
    categories: List[str],
    values: List[float],
    title: str = "涨跌排行",
    colors: List[str] = None
) -> BytesIO:
    """生成横向柱状图返回 BytesIO"""
    buf = BytesIO()
    try:
        if not categories or len(categories) == 0:
            raise ValueError("柱状图分类为空")

        fig, ax = plt.subplots(figsize=(10, 6))

        if colors is None:
            colors = ['#FF6B6B' if v >= 0 else '#4ECDC4' for v in values]

        y_pos = range(len(categories))
        bars = ax.barh(y_pos, values, color=colors, height=0.6, edgecolor='white', linewidth=0.5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=9)
        ax.set_xlabel('涨跌幅 (%)', fontsize=10)
        ax.set_title(title, fontsize=14, pad=15, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        for bar, val in zip(bars, values):
            x_pos = bar.get_width()
            offset = 0.3 if x_pos >= 0 else -0.3
            ha = 'left' if x_pos >= 0 else 'right'
            ax.text(x_pos + offset, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}%', ha=ha, va='center', fontsize=8)

        ax.axvline(x=0, color='#333333', linewidth=0.8)
        plt.tight_layout()

        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        plt.close('all')
        buf.close()
        raise ValueError(f"柱状图生成失败: {str(e)}") from e


def gauge_to_bytes(
    value: float,
    min_val: float = 0,
    max_val: float = 10,
    title: str = "价格波动幅度"
) -> BytesIO:
    """生成仪表盘返回 BytesIO"""
    buf = BytesIO()
    try:
        fig, ax = plt.subplots(figsize=(6, 4), subplot_kw={'projection': 'polar'})

        normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        normalized = max(0, min(1, normalized))

        colors = ['#4ECDC4', '#45B7D1', '#FF6B6B']
        color = colors[2] if normalized > 0.7 else colors[1] if normalized > 0.3 else colors[0]

        theta = numpy.linspace(0.25 * numpy.pi, 0.75 * numpy.pi, 100)
        r = [1] * 100
        ax.plot(theta, r, color='#e0e0e0', linewidth=8, solid_capstyle='butt')

        progress_theta = numpy.linspace(0.25 * numpy.pi, 0.25 * numpy.pi + normalized * 0.5 * numpy.pi, 100)
        ax.plot(progress_theta, r, color=color, linewidth=8, solid_capstyle='butt')

        pointer_theta = 0.25 * numpy.pi + normalized * 0.5 * numpy.pi
        ax.arrow(pointer_theta, 0.3, 0, 0.35, head_width=0.05, head_length=0.08, fc=color, ec=color, width=0.02)

        ax.text(0.5 * numpy.pi, 0.2, f'{value:.1f}%', ha='center', va='center', fontsize=16, fontweight='bold')

        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)
        ax.grid(False)
        ax.set_title(title, fontsize=12, pad=20, fontweight='bold', y=1.05)

        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        plt.close('all')
        buf.close()
        raise ValueError(f"仪表盘生成失败: {str(e)}") from e


def chart_to_base64(buf: BytesIO) -> str:
    """将 BytesIO 图表转为 base64 字符串"""
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')
