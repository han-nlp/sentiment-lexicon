# -*- coding: utf-8 -*-
"""
auto_label.py —— V1 基线自动标注脚本（历史版本）
==============================================
V1 逻辑：扫描句子，命中词典中的词就取其固定极性；若一句话同时出现
多个情感词，取【最后一个匹配到的非中性词】（为避免被开头的"咱就是说"
等中性发语词带偏）。

⚠️ 历史基线版本：硬编码本机路径的问题已修复为相对路径，逻辑保持 V1 原貌。
   该逻辑不处理反讽/多义/否定，演示时会复现 V1 的典型误判，
   这正是 65.3% -> 94% 迭代的起点。最新实现见 ../../src/annotate.py

用法：python legacy/v1_dict_baseline/auto_label.py
输入：legacy/v1_dict_baseline/sample_comments.csv（含"评论内容"列）
输出：legacy/v1_dict_baseline/v1_auto_labeled.csv
"""
from pathlib import Path
import time
import pandas as pd
from sentiment_dict import sentiment_dict

HERE = Path(__file__).resolve().parent
INPUT = HERE / "sample_comments.csv"


def auto_label(text: str) -> str:
    """V1 规则：取最后一个匹配到的非中性词的极性。"""
    last_sentiment = "中性"
    for word, sentiment in sentiment_dict.items():
        if word in text:
            if sentiment != "中性":
                last_sentiment = sentiment
            elif last_sentiment == "中性":
                last_sentiment = "中性"
    return last_sentiment


def main():
    df = pd.read_csv(INPUT)
    print(f"共读取 {len(df)} 条评论")

    df["自动标注"] = df["评论内容"].apply(auto_label)

    print("\n=== V1 自动标注结果统计 ===")
    print(df["自动标注"].value_counts())

    out = HERE / f"v1_auto_labeled_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n标注完成，已保存到 {out.name}")
    print("提示：其中反讽/感动义'破防'/多重否定等样本会被误判，属 V1 预期缺陷。")


if __name__ == "__main__":
    main()
