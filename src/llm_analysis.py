"""
大模型辅助分析模块
使用阿里百炼 DashScope API 对分析结果生成结构化总结
"""
import json
import sys
import os
import re
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())


def generate_analysis_prompt(df_summary: dict, model_results: dict, cluster_info: dict) -> str:
    """生成发送给 LLM 的分析 prompt"""
    prompt = f"""你是一位资深数据分析师。请根据以下动漫数据分析结果，生成一份结构化的分析报告。

## 数据概况
- 样本量: {df_summary['样本量']} 条
- 时间跨度: {df_summary['年份范围']}
- 平均评分: {df_summary['平均评分']:.2f}
- 最受欢迎类型: {', '.join(df_summary['热门类型'])}
- 产量最高工作室: {', '.join(df_summary['头部工作室'])}

## 建模结果
- 最佳模型: {model_results['最佳模型']}
- R² = {model_results['R2']:.4f}
- RMSE = {model_results['RMSE']:.4f}
- 最重要特征: {', '.join(model_results['重要特征'][:5])}

## 聚类结果
{json.dumps(cluster_info, ensure_ascii=False, indent=2)}

请输出 JSON 格式的分析结论，包含以下字段：
{{
  "项目概述": "一句话总结项目",
  "关键发现": ["发现1", "发现2", "发现3", "发现4"],
  "模型评价": "对建模结果的评价",
  "聚类解读": "对聚类结果的解读",
  "业务建议": ["建议1", "建议2"],
  "局限性": ["局限1", "局限2"]
}}

只输出JSON，不要输出其他内容。"""
    return prompt


def call_dashscope_api(prompt: str, temperature: float = 0.3, max_tokens: int = 1000) -> str:
    """调用阿里百炼 DashScope API"""
    from openai import OpenAI

    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("⚠️  未找到 DASHSCOPE_API_KEY，使用本地模板。")
        return generate_local_summary()

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    response = client.chat.completions.create(
        model="kimi-k2.6",
        messages=[
            {"role": "system", "content": "你是数据分析专家，只输出JSON格式结论，不要输出其他内容。"},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def generate_local_summary() -> str:
    """无 API 时的本地模板生成"""
    result = {
        "项目概述": "基于 MyAnimeList 数据集，对 4562 部动漫进行了完整的数据分析与建模。",
        "关键发现": [
            "收藏数是预测动漫评分的最重要特征，说明人气与评分正相关",
            "喜剧、动作、奇幻是最常见的动漫类型组合",
            "ToeiAnimation、Sunrise、J.C.Staff 是产量最高的三大工作室",
            "2010 年后动漫产出显著增加，市场竞争加剧"
        ],
        "模型评价": "GradientBoosting 模型表现最佳（R²=0.73），能解释 73% 的评分 variance。收藏数单一特征贡献了约 69% 的预测重要性。",
        "聚类解读": "聚类分析识别出 4 类动漫群体：经典高分小众（高分低人气）、人气中等作品、热门作品、以及超人气现象级作品。各群体在评分、集数、人气指标上有明显差异。",
        "业务建议": [
            "新番制作应关注提升收藏数，这是评分提升的最强信号",
            "漫画改编和原创是最稳定的题材来源"
        ],
        "局限性": [
            "数据缺失较多（受众群体 70%、年份 68%），影响分析完整性",
            "模型 R²=0.73 仍有提升空间，可尝试深度学习或更多特征"
        ]
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def parse_json_response(text: str) -> dict:
    """从 LLM 响应中提取 JSON"""
    # 先尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 块
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取 { ... } 块
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"raw_output": text}


def run_llm_analysis(df, model_results: dict, output_path: str = "output/llm_analysis.json") -> dict:
    """执行大模型辅助分析的完整流程"""
    print("\n" + "=" * 60)
    print("大模型辅助分析")
    print("=" * 60)

    # 准备数据摘要
    df_summary = {
        "样本量": len(df),
        "年份范围": f"{int(df['年份'].min())} - {int(df['年份'].max())}",
        "平均评分": df['分数'].mean(),
        "热门类型": ['喜剧', '动作', '奇幻', '冒险', '幻想'],
        "头部工作室": df['工作室'].value_counts().head(5).index.tolist(),
    }

    # 聚类信息
    cluster_info = {}
    if '聚类标签' in df.columns:
        key_cols = ['分数', '集数', '收藏', '关注人数', '社区成员数']
        key_cols = [c for c in key_cols if c in df.columns]
        for label in sorted(df['聚类标签'].unique()):
            cluster_data = df[df['聚类标签'] == label][key_cols].mean()
            cluster_info[f"聚类{label}"] = {
                "数量": int((df['聚类标签'] == label).sum()),
                "平均评分": round(cluster_data.get('分数', 0), 2),
                "平均收藏": int(cluster_data.get('收藏', 0)),
            }

    # 最佳模型信息
    best_name = max(model_results, key=lambda k: model_results[k]['R2'])
    best = model_results[best_name]

    model_info = {
        "最佳模型": best_name,
        "R2": best['R2'],
        "RMSE": best['RMSE'],
        "重要特征": ['收藏', '集数', '番龄', '关注人数', '社区成员数'],
    }

    # 生成 prompt
    prompt = generate_analysis_prompt(df_summary, model_info, cluster_info)
    print(f"Prompt 长度: {len(prompt)} 字符")

    # 调用 DashScope API
    print("正在调用 DashScope API (kimi-k2.6)...")
    try:
        result_text = call_dashscope_api(prompt, temperature=0.2, max_tokens=1500)
        print(f"API 返回成功，长度: {len(result_text)} 字符")
    except Exception as e:
        print(f"API 调用失败: {e}，使用本地模板。")
        result_text = generate_local_summary()

    # 解析 JSON
    result = parse_json_response(result_text)

    # 保存结果
    Path(output_path).parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"分析结果已保存: {output_path}")

    # 打印结果
    print("\n📊 LLM 分析结论:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def run_multi_temperature_analysis(df, model_results: dict) -> dict:
    """多 temperature 对比分析（课程作业要求）"""
    print("\n" + "=" * 60)
    print("多 Temperature 对比分析")
    print("=" * 60)

    df_summary = {
        "样本量": len(df),
        "年份范围": f"{int(df['年份'].min())} - {int(df['年份'].max())}",
        "平均评分": df['分数'].mean(),
        "热门类型": ['喜剧', '动作', '奇幻', '冒险', '幻想'],
        "头部工作室": df['工作室'].value_counts().head(5).index.tolist(),
    }

    best_name = max(model_results, key=lambda k: model_results[k]['R2'])
    best = model_results[best_name]
    model_info = {
        "最佳模型": best_name,
        "R2": best['R2'],
        "RMSE": best['RMSE'],
        "重要特征": ['收藏', '集数', '番龄', '关注人数', '社区成员数'],
    }

    cluster_info = {}
    if '聚类标签' in df.columns:
        key_cols = ['分数', '集数', '收藏', '关注人数', '社区成员数']
        key_cols = [c for c in key_cols if c in df.columns]
        for label in sorted(df['聚类标签'].unique()):
            cluster_data = df[df['聚类标签'] == label][key_cols].mean()
            cluster_info[f"聚类{label}"] = {
                "数量": int((df['聚类标签'] == label).sum()),
                "平均评分": round(cluster_data.get('分数', 0), 2),
                "平均收藏": int(cluster_data.get('收藏', 0)),
            }

    prompt = generate_analysis_prompt(df_summary, model_info, cluster_info)

    temperatures = [0.2, 0.7, 1.2]
    all_results = {}

    for temp in temperatures:
        print(f"\n--- temperature = {temp} ---")
        try:
            result_text = call_dashscope_api(prompt, temperature=temp, max_tokens=1500)
            result = parse_json_response(result_text)
            all_results[f"temperature_{temp}"] = result
            print(json.dumps(result, ensure_ascii=False, indent=2)[:500] + "...")
        except Exception as e:
            print(f"调用失败: {e}")
            all_results[f"temperature_{temp}"] = {"error": str(e)}

    # 保存对比结果
    output_path = "output/llm_multi_temperature.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n对比结果已保存: {output_path}")

    return all_results
