# -*- coding: utf-8 -*-
"""
calc_accuracy.py —— V1 基线准确率复算脚本（历史版本）
==================================================
用 V1 的"固定极性词典 + 取最后非中性词"逻辑，对人工金标准复算一致率，
并打印错误明细，用于直观复现 V1 的典型缺陷。

⚠️ 历史基线版本：硬编码本机路径已修复为相对路径，逻辑保持 V1 原貌。
   最新评估（含 V1/V2/V3 版本记录）见 ../../src/evaluate.py

用法：
    python legacy/v1_dict_baseline/calc_accuracy.py
默认输入：同目录 v1_demo_gold.csv —— 这是【边界难例集】，集中收录了 V1
         会失败的反讽/多义/多重否定/词典遗漏样本（取自 error_analysis.csv
         的错误类型），用于演示 V1 缺陷，因此一致率会明显偏低，这是预期的。
可选：    python calc_accuracy.py <任意金标准csv，需含"评论内容/人工标注"列>

历史数字：V1 在 150 条【随机】验证集上一致率为 65.3%；
         在本难例集上更低，因为这里只收 V1 的"翻车"样本。
"""
from pathlib import Path
import sys
import pandas as pd
from sentiment_dict import sentiment_dict

HERE = Path(__file__).resolve().parent
DEFAULT_GOLD = HERE / "v1_demo_gold.csv"
REPO_GOLD = HERE.parent.parent / "ground_truth.csv"


def v1_label(text: str) -> str:
    """与 auto_label.py 完全相同的 V1 规则：遍历词典，取最后命中的非中性词。"""
    last = "中性"
    for word, sent in sentiment_dict.items():
        if word in text and sent != "中性":
            last = sent
    return last


def main():
    gold_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GOLD
    if not gold_path.exists():
        print(f"未找到金标准文件：{gold_path}")
        return

    df = pd.read_csv(gold_path)
    df["V1自动标注"] = df["评论内容"].apply(v1_label)

    labeled = df[df["人工标注"].notna()]
    correct = (labeled["V1自动标注"] == labeled["人工标注"]).sum()
    total = len(labeled)
    is_demo = gold_path.name == "v1_demo_gold.csv"
    print(f"评估文件：{gold_path.name}" + ("（边界难例集）" if is_demo else ""))
    print(f"人工校验 {total} 条，V1 正确 {correct} 条，一致率 {correct/total*100:.1f}%")
    if is_demo:
        print("注：本集只收 V1 失败样本，一致率偏低属预期；"
              "V1 在 150 条随机验证集上为 65.3%。\n")

    errors = labeled[labeled["V1自动标注"] != labeled["人工标注"]]
    print(f"V1 标错 {len(errors)} 条，明细：")
    for _, row in errors.iterrows():
        etype = f"［{row['错误类型']}］" if "错误类型" in df.columns and pd.notna(row.get("错误类型")) else ""
        print(f"原文：{row['评论内容']} {etype}")
        print(f"  V1自动：{row['V1自动标注']} -> 人工：{row['人工标注']}")
    print("\n以上错误对应 data/error_analysis.csv 的四类归因："
          "词典遗漏 / 歧义词 / 长句误判 / 反讽，均在 V2/V3 中修复。")


if __name__ == "__main__":
    main()
