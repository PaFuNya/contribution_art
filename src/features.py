"""
特征工程模块 — 为建模准备特征
"""
from typing import List, Tuple, Dict
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler


def create_popularity_features(df: pd.DataFrame) -> pd.DataFrame:
    """创建人气相关特征"""
    df = df.copy()
    # 人气综合得分（归一化后加权）
    for col in ['收藏', '关注人数', '社区成员数']:
        max_val = df[col].max()
        if max_val > 0:
            df[f'{col}_norm'] = df[col] / max_val

    df['人气综合'] = (
        df.get('收藏_norm', df['收藏'] / df['收藏'].max()) * 0.4 +
        df.get('关注人数_norm', df['关注人数'] / df['关注人数'].max()) * 0.3 +
        df.get('社区成员数_norm', df['社区成员数'] / df['社区成员数'].max()) * 0.3
    )
    return df


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """创建时间相关特征"""
    df = df.copy()
    current_year = 2025
    df['番龄'] = current_year - df['年份']
    df['是否经典'] = (df['番龄'] >= 10).astype(int)
    df['年代'] = pd.cut(df['年份'],
                        bins=[1960, 1990, 2000, 2010, 2020, 2030],
                        labels=['60-80s', '90s', '00s', '10s', '20s'])
    return df


def encode_categorical(df: pd.DataFrame, columns: List[str]) -> Tuple[pd.DataFrame, dict]:
    """Label Encoding 分类特征"""
    df = df.copy()
    encoders = {}
    for col in columns:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders


def get_top_genres(df: pd.DataFrame, n: int = 15) -> List[str]:
    """获取出现频率最高的 n 个类型"""
    all_genres = []
    for genres in df['类型_列表']:
        all_genres.extend([g.strip() for g in genres if g.strip()])
    return pd.Series(all_genres).value_counts().head(n).index.tolist()


def create_genre_dummies(df: pd.DataFrame, top_genres: List[str] = None) -> pd.DataFrame:
    """为 Top N 类型创建 one-hot 编码"""
    df = df.copy()
    if top_genres is None:
        top_genres = get_top_genres(df)

    for genre in top_genres:
        df[f'genre_{genre}'] = df['类型'].fillna('').str.contains(genre, regex=False).astype(int)
    return df


def prepare_modeling_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """准备建模特征集，返回 (df, feature_columns)"""
    df = df.copy()

    # 人气特征
    df = create_popularity_features(df)

    # 时间特征
    df = create_temporal_features(df)

    # 类型 one-hot
    top_genres = get_top_genres(df, n=15)
    df = create_genre_dummies(df, top_genres)

    # 编码分类列
    cat_cols = ['视频类型', '源材料', '受众群体', '年龄适度']
    existing_cats = [c for c in cat_cols if c in df.columns]
    df, encoders = encode_categorical(df, existing_cats)

    # 数值特征列
    numeric_features = ['集数', '时长_分钟', '人气排名', '收藏', '关注人数', '社区成员数',
                        '人气综合', '番龄', '类型数量']

    # 编码特征列
    encoded_features = [f'{c}_encoded' for c in existing_cats]

    # 类型 one-hot 列
    genre_features = [c for c in df.columns if c.startswith('genre_')]

    feature_cols = numeric_features + encoded_features + genre_features

    # 只保留存在的列
    feature_cols = [c for c in feature_cols if c in df.columns]

    print(f"特征数量: {len(feature_cols)}")
    print(f"  数值特征: {len(numeric_features)}")
    print(f"  编码特征: {len(encoded_features)}")
    print(f"  类型特征: {len(genre_features)}")

    return df, feature_cols
