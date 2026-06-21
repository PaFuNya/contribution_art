# 🎬 动漫数据分析 — 数据分析应用期末项目

## 项目简介

基于 MyAnimeList 平台的动漫数据集（15000条），完成从数据获取到分析建模再到可视化的完整数据分析流程。

## 研究问题

1. 动漫评分的分布规律是什么？哪些因素影响评分？
2. 能否基于特征预测动漫评分？
3. 能否将动漫自动分群？各群体有什么特征？

## 项目结构

```
├── README.md              # 项目说明
├── CLAUDE.md              # Claude Code 工作手册
├── main.py                # 主分析流程（一键运行）
├── requirements.txt       # Python 依赖
├── data/
│   ├── AAACG.xlsx         # 原始数据
│   └── AAACG_cleaned.xlsx # 清洗后数据
├── src/
│   ├── cleaner.py         # 数据清洗模块
│   ├── features.py        # 特征工程模块
│   ├── model.py           # 建模模块（回归/聚类/降维）
│   ├── visualize.py       # 可视化模块
│   └── llm_analysis.py    # 大模型辅助分析模块
├── notebooks/
│   └── analysis.ipynb     # 交互式分析 Notebook
├── output/                # 图表和分析结果
└── report/                # 项目报告
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行完整分析
python main.py

# 3. 查看结果
# output/ 目录下包含所有图表和分析摘要
```

## 技术栈

- **Python 3.8+**
- **Pandas** — 数据处理
- **Matplotlib + Seaborn** — 可视化
- **scikit-learn** — 机器学习建模
- **LightGBM / XGBoost** — 梯度提升模型

## 分析流程

| 步骤 | 内容 | 输出 |
|------|------|------|
| Step 1 | 数据清洗与预处理 | `data/AAACG_cleaned.xlsx` |
| Step 2 | 探索性数据分析 | 9 张 EDA 图表 |
| Step 3 | 特征工程 | 28 个特征 |
| Step 4 | 建模（回归+聚类+PCA） | 模型评估图表 |
| Step 5 | 大模型辅助分析 | `output/llm_analysis.json` |
| Step 6 | 分析摘要 | `output/analysis_summary.md` |

## 建模结果

| 模型 | RMSE | MAE | R² |
|------|------|-----|-----|
| LinearRegression | 0.4870 | 0.3839 | 0.5623 |
| Ridge | 0.4869 | 0.3839 | 0.5624 |
| Lasso | 0.4907 | 0.3870 | 0.5556 |
| RandomForest | 0.3926 | 0.2995 | 0.7156 |
| **GradientBoosting** | **0.3808** | **0.2903** | **0.7323** |

## 小组分工

（请填写实际分工）

| 成员 | 负责内容 |
|------|---------|
| 朗东成| 数据清洗 + EDA |
| 朗东成 & CC | 特征工程 + 建模 |
| 朗东成| 可视化 + 报告 |
| 朗东成| 大模型辅助分析 + PPT |
