"""
数据清洗模块 — 动漫数据集预处理
"""
from typing import List, Tuple
import pandas as pd
import numpy as np


def load_data(filepath: str) -> pd.DataFrame:
    """加载原始数据"""
    df = pd.read_excel(filepath)
    return df


def clean_episodes(df: pd.DataFrame) -> pd.DataFrame:
    """清洗集数列：填充缺失值为中位数"""
    df = df.copy()
    median_eps = df['集数'].median()
    df['集数'] = df['集数'].fillna(median_eps)
    return df


def parse_duration_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """将时长字段（如'24分钟'）转为数值（分钟）"""
    df = df.copy()
    df['时长_分钟'] = (
        df['时长']
        .str.extract(r'(\d+)')[0]
        .astype(float)
        .fillna(0)
    )
    return df


def parse_multi_value_columns(df: pd.DataFrame) -> pd.DataFrame:
    """拆分多值列（类型、主题）为列表，方便后续分析"""
    df = df.copy()
    df['类型_列表'] = df['类型'].fillna('').str.split(r'[,，]')
    df['主题_列表'] = df['主题'].fillna('').str.split(r'[,，]')
    df['类型数量'] = df['类型_列表'].apply(lambda x: len([i for i in x if i.strip()]))
    return df


def fill_categorical_with_unknown(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """将分类列的缺失值填充为 'Unknown'"""
    df = df.copy()
    for col in columns:
        df[col] = df[col].fillna('Unknown')
    return df


def drop_high_null_columns(df: pd.DataFrame, threshold: float = 0.7) -> pd.DataFrame:
    """删除缺失率超过阈值的列"""
    df = df.copy()
    null_pct = df.isnull().mean()
    cols_to_drop = null_pct[null_pct > threshold].index.tolist()
    if cols_to_drop:
        print(f"删除缺失率>{threshold*100:.0f}%的列: {cols_to_drop}")
    return df.drop(columns=cols_to_drop)


def clean_all(filepath: str) -> pd.DataFrame:
    """完整清洗流程"""
    df = load_data(filepath)

    # 1. 时长转数值
    df = parse_duration_minutes(df)

    # 2. 多值列拆分
    df = parse_multi_value_columns(df)

    # 3. 集数填充
    df = clean_episodes(df)

    # 4. 分类列填充
    cat_cols = ['视频类型', '工作室', '源材料', '年龄适度', '受众群体']
    df = fill_categorical_with_unknown(df, cat_cols)

    # 5. 删除高缺失列（年份和季节缺失68.8%，保留年份用于分析，季节删除）
    df = df.drop(columns=['季节', '年份和季节'], errors='ignore')

    # 6. 删除剩余缺失行（年份、类型、主题少量缺失）
    before = len(df)
    df = df.dropna(subset=['年份', '类型'])
    print(f"删除缺失行: {before - len(df)} 条")

    # 7. 类型转换
    df['年份'] = df['年份'].astype(int)
    df['集数'] = df['集数'].astype(int)

    print(f"清洗完成: {df.shape[0]} 行 × {df.shape[1]} 列")
    return df.reset_index(drop=True)
