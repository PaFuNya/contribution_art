from typing import List, Tuple, Dict
"""
可视化模块 — 统一的图表样式和绘图函数
"""
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path

# ========== 全局样式设置 ==========
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 100
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['savefig.bbox'] = 'tight'

OUTPUT_DIR = Path(__file__).parent.parent / 'output'


def save_fig(fig: plt.Figure, filename: str) -> str:
    """保存图表到 output/ 目录"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / filename
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"图表已保存: {filepath}")
    return str(filepath)


def plot_distribution(df: pd.DataFrame, column: str, title: str = None,
                      xlabel: str = None, bins: int = 50) -> str:
    """绘制数值列分布图（直方图 + KDE + 箱线图）"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 直方图 + KDE
    ax1 = axes[0]
    df[column].dropna().hist(bins=bins, ax=ax1, alpha=0.7, color='steelblue', edgecolor='white')
    ax1.axvline(df[column].mean(), color='red', linestyle='--', label=f'均值: {df[column].mean():.2f}')
    ax1.axvline(df[column].median(), color='orange', linestyle='--', label=f'中位数: {df[column].median():.2f}')
    ax1.set_xlabel(xlabel or column, fontsize=12)
    ax1.set_ylabel('频次', fontsize=12)
    ax1.set_title(title or f'{column} 分布', fontsize=14)
    ax1.legend()

    # 箱线图
    ax2 = axes[1]
    df[column].dropna().plot.box(ax=ax2, vert=True, patch_artist=True,
                                  boxprops=dict(facecolor='lightblue'))
    ax2.set_ylabel(xlabel or column, fontsize=12)
    ax2.set_title(f'{column} 箱线图', fontsize=14)

    fig.tight_layout()
    return save_fig(fig, f'dist_{column}.png')


def plot_bar_counts(df: pd.DataFrame, column: str, top_n: int = 15,
                    title: str = None, horizontal: bool = False) -> str:
    """绘制分类列计数柱状图"""
    counts = df[column].value_counts().head(top_n)

    fig, ax = plt.subplots(figsize=(12, 6))
    if horizontal:
        counts.plot.barh(ax=ax, color='steelblue', edgecolor='white')
        ax.set_xlabel('数量', fontsize=12)
    else:
        counts.plot.bar(ax=ax, color='steelblue', edgecolor='white')
        ax.set_ylabel('数量', fontsize=12)
        plt.xticks(rotation=45, ha='right')

    ax.set_title(title or f'{column} Top {top_n}', fontsize=14)
    fig.tight_layout()
    return save_fig(fig, f'bar_{column}.png')


def plot_scatter(df: pd.DataFrame, x: str, y: str, hue: str = None,
                 title: str = None) -> str:
    """绘制散点图"""
    fig, ax = plt.subplots(figsize=(10, 7))
    if hue and hue in df.columns:
        # 取 top 10 类别，避免图例过多
        top_cats = df[hue].value_counts().head(10).index
        mask = df[hue].isin(top_cats)
        for cat in top_cats:
            subset = df[mask & (df[hue] == cat)]
            ax.scatter(subset[x], subset[y], alpha=0.5, s=20, label=cat)
        ax.legend(title=hue, fontsize=8, ncol=2)
    else:
        ax.scatter(df[x], df[y], alpha=0.3, s=15, color='steelblue')

    ax.set_xlabel(x, fontsize=12)
    ax.set_ylabel(y, fontsize=12)
    ax.set_title(title or f'{x} vs {y}', fontsize=14)
    fig.tight_layout()
    return save_fig(fig, f'scatter_{x}_vs_{y}.png')


def plot_correlation_heatmap(df: pd.DataFrame, columns: List[str] = None,
                              title: str = None) -> str:
    """绘制相关性热力图"""
    if columns:
        corr = df[columns].corr()
    else:
        corr = df.select_dtypes(include=[np.number]).corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, ax=ax, square=True, linewidths=0.5)
    ax.set_title(title or '相关性热力图', fontsize=14)
    fig.tight_layout()
    return save_fig(fig, 'correlation_heatmap.png')


def plot_time_trend(df: pd.DataFrame, time_col: str, value_col: str,
                    agg_func: str = 'mean', title: str = None) -> str:
    """绘制时间趋势图"""
    trend = df.groupby(time_col)[value_col].agg(agg_func).sort_index()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(trend.index, trend.values, marker='o', markersize=3,
            linewidth=1.5, color='steelblue')
    ax.fill_between(trend.index, trend.values, alpha=0.1, color='steelblue')
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel(f'{value_col}（{agg_func}）', fontsize=12)
    ax.set_title(title or f'{value_col} 随时间变化趋势', fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return save_fig(fig, f'trend_{value_col}.png')


def plot_group_comparison(df: pd.DataFrame, group_col: str, value_col: str,
                           top_n: int = 10, title: str = None) -> str:
    """绘制分组对比箱线图"""
    top_groups = df[group_col].value_counts().head(top_n).index
    mask = df[group_col].isin(top_groups)

    fig, ax = plt.subplots(figsize=(14, 6))
    df[mask].boxplot(column=value_col, by=group_col, ax=ax, rot=45)
    ax.set_xlabel(group_col, fontsize=12)
    ax.set_ylabel(value_col, fontsize=12)
    ax.set_title(title or f'不同{group_col}的{value_col}对比', fontsize=14)
    fig.suptitle('')
    fig.tight_layout()
    return save_fig(fig, f'box_{group_col}_vs_{value_col}.png')
