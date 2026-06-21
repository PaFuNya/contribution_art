"""
建模模块 — 回归、聚类、分类
"""
from typing import List, Tuple, Dict
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (mean_squared_error, mean_absolute_error, r2_score,
                             silhouette_score, calinski_harabasz_score)
import warnings
warnings.filterwarnings('ignore')

RANDOM_STATE = 42


# ========== 回归：预测分数 ==========

def train_regression_models(df: pd.DataFrame, feature_cols: List[str],
                            target: str = '分数') -> dict:
    """训练多个回归模型并比较"""
    X = df[feature_cols].fillna(0)
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.01),
        'RandomForest': RandomForestRegressor(n_estimators=100, max_depth=10,
                                               random_state=RANDOM_STATE, n_jobs=-1),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, max_depth=5,
                                                       learning_rate=0.1,
                                                       random_state=RANDOM_STATE),
    }

    results = {}
    for name, model in models.items():
        if name in ['LinearRegression', 'Ridge', 'Lasso']:
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        results[name] = {
            'model': model,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'y_test': y_test,
            'y_pred': y_pred,
        }
        print(f"{name:25s} | RMSE: {rmse:.4f} | MAE: {mae:.4f} | R²: {r2:.4f}")

    return results


def get_feature_importance(results: dict, feature_cols: List[str]) -> pd.DataFrame:
    """提取树模型的特征重要性"""
    importances = {}
    for name, res in results.items():
        model = res['model']
        if hasattr(model, 'feature_importances_'):
            importances[name] = model.feature_importances_

    if not importances:
        return pd.DataFrame()

    df_imp = pd.DataFrame(importances, index=feature_cols)
    df_imp['平均重要性'] = df_imp.mean(axis=1)
    return df_imp.sort_values('平均重要性', ascending=False)


# ========== 聚类：动漫分群 ==========

def find_optimal_k(X_scaled: np.ndarray, k_range: range = range(2, 11)) -> int:
    """用轮廓系数找最优 K"""
    scores = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels, sample_size=5000, random_state=RANDOM_STATE)
        scores.append((k, score))
        print(f"  K={k}: 轮廓系数={score:.4f}")

    best_k = max(scores, key=lambda x: x[1])[0]
    print(f"最优 K = {best_k}")
    return best_k


def run_clustering(df: pd.DataFrame, feature_cols: List[str],
                   n_clusters: int = None) -> Tuple[pd.DataFrame, KMeans]:
    """执行 K-Means 聚类"""
    X = df[feature_cols].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if n_clusters is None:
        print("寻找最优聚类数...")
        n_clusters = find_optimal_k(X_scaled)

    km = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    df = df.copy()
    df['聚类标签'] = km.fit_predict(X_scaled)

    # 评估
    sil = silhouette_score(X_scaled, df['聚类标签'], sample_size=5000, random_state=RANDOM_STATE)
    ch = calinski_harabasz_score(X_scaled, df['聚类标签'])
    print(f"轮廓系数: {sil:.4f}")
    print(f"Calinski-Harabasz: {ch:.2f}")

    return df, km


def analyze_clusters(df: pd.DataFrame, cluster_col: str = '聚类标签') -> pd.DataFrame:
    """分析每个聚类的特征"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    summary = df.groupby(cluster_col)[numeric_cols].agg(['mean', 'median', 'count'])
    return summary


# ========== 降维：PCA 可视化 ==========

def run_pca(X_scaled: np.ndarray, n_components: int = 2) -> np.ndarray:
    """PCA 降维"""
    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)
    print(f"PCA 解释方差比: {pca.explained_variance_ratio_}")
    print(f"累计解释方差: {sum(pca.explained_variance_ratio_):.4f}")
    return X_pca, pca
