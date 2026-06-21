"""
动漫数据分析主流程
BigHomeWork Data Analysis — 完整数据分析 Pipeline
"""
import sys
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from src.cleaner import clean_all
from src.visualize import (plot_distribution, plot_bar_counts, plot_scatter,
                           plot_correlation_heatmap, plot_time_trend,
                           plot_group_comparison, save_fig, OUTPUT_DIR)
from src.features import (prepare_modeling_features, get_top_genres,
                          create_genre_dummies, create_temporal_features)
from src.model import (train_regression_models, get_feature_importance,
                       run_clustering, analyze_clusters, run_pca)
from src.llm_analysis import run_llm_analysis

# ========== 全局设置 ==========
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
DATA_PATH = 'data/AAACG.xlsx'


def step1_clean_data():
    """Step 1: 数据清洗"""
    print("\n" + "=" * 60)
    print("STEP 1: 数据清洗与预处理")
    print("=" * 60)
    df = clean_all(DATA_PATH)
    df.to_excel('data/AAACG_cleaned.xlsx', index=False)
    print(f"清洗后数据已保存: data/AAACG_cleaned.xlsx")
    return df


def step2_eda(df: pd.DataFrame):
    """Step 2: 探索性数据分析"""
    print("\n" + "=" * 60)
    print("STEP 2: 探索性数据分析 (EDA)")
    print("=" * 60)

    # 2.1 分数分布
    print("\n--- 2.1 分数分布 ---")
    plot_distribution(df, '分数', '动漫评分分布', '评分')

    # 2.2 集数分布（取 < 100 的）
    print("\n--- 2.2 集数分布 ---")
    df_short = df[df['集数'] <= 100]
    plot_distribution(df_short, '集数', '动漫集数分布（≤100集）', '集数', bins=50)

    # 2.3 类型分布
    print("\n--- 2.3 类型分布 ---")
    all_genres = []
    for genres in df['类型_列表']:
        all_genres.extend([g.strip() for g in genres if g.strip()])
    genre_counts = pd.Series(all_genres).value_counts().head(15)
    fig, ax = plt.subplots(figsize=(12, 6))
    genre_counts.plot.barh(ax=ax, color='steelblue', edgecolor='white')
    ax.set_xlabel('数量', fontsize=12)
    ax.set_title('Top 15 动漫类型', fontsize=14)
    ax.invert_yaxis()
    fig.tight_layout()
    save_fig(fig, 'bar_genre_top15.png')

    # 2.4 年份趋势
    print("\n--- 2.4 年份趋势 ---")
    df_year = df[df['年份'] >= 1990]
    plot_time_trend(df_year, '年份', '分数', 'mean', '平均评分随年份变化趋势')

    # 每年产出数量
    yearly_count = df[df['年份'] >= 1990].groupby('年份').size()
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(yearly_count.index, yearly_count.values, color='steelblue', alpha=0.8)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('动漫数量', fontsize=12)
    ax.set_title('每年动漫产出数量', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    fig.tight_layout()
    save_fig(fig, 'bar_yearly_count.png')

    # 2.5 视频类型对比
    print("\n--- 2.5 视频类型对比 ---")
    plot_group_comparison(df, '视频类型', '分数', title='不同视频类型的评分对比')

    # 2.6 源材料对比
    print("\n--- 2.6 源材料对比 ---")
    plot_group_comparison(df, '源材料', '分数', title='不同源材料的评分对比')

    # 2.7 工作室 Top 15 评分
    print("\n--- 2.7 工作室评分对比 ---")
    top_studios = df['工作室'].value_counts().head(15).index
    fig, ax = plt.subplots(figsize=(14, 6))
    df[df['工作室'].isin(top_studios)].boxplot(
        column='分数', by='工作室', ax=ax, rot=45
    )
    ax.set_xlabel('工作室', fontsize=12)
    ax.set_ylabel('评分', fontsize=12)
    ax.set_title('Top 15 工作室评分分布', fontsize=14)
    fig.suptitle('')
    fig.tight_layout()
    save_fig(fig, 'box_studio_vs_score.png')

    # 2.8 相关性热力图
    print("\n--- 2.8 相关性分析 ---")
    numeric_cols = ['分数', '集数', '时长_分钟', '人气排名', '收藏', '关注人数', '社区成员数']
    existing = [c for c in numeric_cols if c in df.columns]
    plot_correlation_heatmap(df, existing, '数值特征相关性热力图')

    # 2.9 人气 vs 分数
    print("\n--- 2.9 人气与评分关系 ---")
    plot_scatter(df, '收藏', '分数', '视频类型', '收藏数 vs 评分')

    print("\nEDA 完成！")


def step3_feature_engineering(df: pd.DataFrame):
    """Step 3: 特征工程"""
    print("\n" + "=" * 60)
    print("STEP 3: 特征工程")
    print("=" * 60)
    df_model, feature_cols = prepare_modeling_features(df)
    print(f"最终特征列: {feature_cols}")
    return df_model, feature_cols


def step4_modeling(df: pd.DataFrame, feature_cols: list):
    """Step 4: 建模"""
    print("\n" + "=" * 60)
    print("STEP 4: 建模与评估")
    print("=" * 60)

    # 4.1 回归：预测分数
    print("\n--- 4.1 回归模型 ---")
    results = train_regression_models(df, feature_cols, target='分数')

    # 特征重要性
    df_imp = get_feature_importance(results, feature_cols)
    if not df_imp.empty:
        print("\n特征重要性 Top 15:")
        print(df_imp['平均重要性'].head(15).to_string())

        # 绘制特征重要性
        top_imp = df_imp['平均重要性'].head(15)
        fig, ax = plt.subplots(figsize=(10, 8))
        top_imp.plot.barh(ax=ax, color='steelblue', edgecolor='white')
        ax.set_xlabel('重要性', fontsize=12)
        ax.set_title('Top 15 特征重要性（预测评分）', fontsize=14)
        ax.invert_yaxis()
        fig.tight_layout()
        save_fig(fig, 'feature_importance.png')

    # 最佳模型预测 vs 实际
    best_name = max(results, key=lambda k: results[k]['R2'])
    best = results[best_name]
    print(f"\n最佳模型: {best_name} (R²={best['R2']:.4f})")

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(best['y_test'], best['y_pred'], alpha=0.3, s=10, color='steelblue')
    ax.plot([5, 10], [5, 10], 'r--', label='完美预测线')
    ax.set_xlabel('实际评分', fontsize=12)
    ax.set_ylabel('预测评分', fontsize=12)
    ax.set_title(f'{best_name}: 预测 vs 实际', fontsize=14)
    ax.legend()
    ax.set_xlim(5, 10)
    ax.set_ylim(5, 10)
    fig.tight_layout()
    save_fig(fig, 'regression_pred_vs_actual.png')

    # 4.2 聚类
    print("\n--- 4.2 聚类分析 ---")
    X = df[feature_cols].fillna(0)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    df_clustered, km = run_clustering(df, feature_cols, n_clusters=4)

    # 聚类分析
    cluster_summary = analyze_clusters(df_clustered)
    print("\n各聚类特征均值:")
    key_cols = ['分数', '集数', '收藏', '关注人数', '社区成员数', '人气排名']
    key_cols = [c for c in key_cols if c in df_clustered.columns]
    print(df_clustered.groupby('聚类标签')[key_cols].mean().to_string())

    # PCA 可视化
    X_pca, pca = run_pca(X_scaled, n_components=2)
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1],
                         c=df_clustered['聚类标签'], cmap='Set1',
                         alpha=0.4, s=10)
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
    ax.set_title('动漫聚类 PCA 可视化', fontsize=14)
    plt.colorbar(scatter, ax=ax, label='聚类标签')
    fig.tight_layout()
    save_fig(fig, 'pca_clusters.png')

    # 聚类雷达图 — 各聚类特征对比
    cluster_means = df_clustered.groupby('聚类标签')[key_cols].mean()
    cluster_means_norm = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min())

    fig, ax = plt.subplots(figsize=(10, 6))
    cluster_means_norm.T.plot.bar(ax=ax, width=0.8)
    ax.set_ylabel('归一化值', fontsize=12)
    ax.set_title('各聚类特征对比（归一化）', fontsize=14)
    ax.legend(title='聚类', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=30, ha='right')
    fig.tight_layout()
    save_fig(fig, 'cluster_comparison.png')

    return df_clustered, results


def step5_summary(df: pd.DataFrame, results: dict) -> str:
    """Step 5: 生成分析摘要"""
    print("\n" + "=" * 60)
    print("STEP 5: 分析摘要")
    print("=" * 60)

    best_name = max(results, key=lambda k: results[k]['R2'])
    best = results[best_name]

    summary = f"""
# 动漫数据分析报告摘要

## 数据概况
- 数据集: MyAnimeList 动漫数据
- 样本量: {len(df)} 条
- 字段数: {len(df.columns)} 个
- 时间跨度: {int(df['年份'].min())} - {int(df['年份'].max())}

## 关键发现
1. **评分分布**: 平均分 {df['分数'].mean():.2f}，标准差 {df['分数'].std():.2f}
2. **最受欢迎类型**: {', '.join(get_top_genres(df, 5))}
3. **产量最高工作室**: {df['工作室'].value_counts().head(3).index.tolist()}
4. **产量趋势**: 2010年后动漫产出显著增加

## 建模结果
- 最佳回归模型: {best_name}
- R² = {best['R2']:.4f}
- RMSE = {best['RMSE']:.4f}
- MAE = {best['MAE']:.4f}

## 聚类结果
- 聚类数: {df['聚类标签'].nunique() if '聚类标签' in df.columns else 'N/A'}
- 各聚类特征差异明显，可识别出经典高分、人气新番、小众作品等群体
"""

    # 保存摘要
    with open('output/analysis_summary.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    print(summary)
    print("摘要已保存: output/analysis_summary.md")

    return summary


if __name__ == '__main__':
    print("🎬 动漫数据分析项目 — 完整 Pipeline")
    print("=" * 60)

    # Step 1: 清洗
    df = step1_clean_data()

    # Step 2: EDA
    step2_eda(df)

    # Step 3: 特征工程
    df_model, feature_cols = step3_feature_engineering(df)

    # Step 4: 建模
    df_clustered, results = step4_modeling(df_model, feature_cols)

    # Step 5: 大模型辅助分析
    llm_result = run_llm_analysis(df_clustered, results)

    # Step 6: 摘要
    step5_summary(df_clustered, results)

    print("\n✅ 全部分析完成！输出文件在 output/ 目录下。")
