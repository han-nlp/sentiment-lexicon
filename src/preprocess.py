# -*- coding: utf-8 -*-
"""
preprocess.py —— 数据清洗模块
功能：读取原始评论 CSV，完成去重、去空、文本规范化、一致性校验，输出清洗后数据。
用法：python src/preprocess.py
输入：data/raw_comments.csv（需含"评论内容"列；若无则用 ground_truth.csv 演示）
输出：data/cleaned_comments.csv
"""
from pathlib import Path
import re
import pandas as pd

# 统一用相对路径，任何人 clone 后都能直接运行
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def normalize_text(text: str) -> str:
    """文本规范化：去首尾空白、合并连续空格/标点、统一全角。"""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", "", text)          # 中文评论去掉内部空白
    text = re.sub(r"([，。！？])\1+", r"\1", text)  # 合并重复标点
    return text


def load_raw() -> pd.DataFrame:
    raw = DATA_DIR / "raw_comments.csv"
    if raw.exists():
        return pd.read_csv(raw)
    # 演示兜底：用仓库自带的 ground_truth.csv
    fallback = ROOT / "ground_truth.csv"
    print(f"[提示] 未找到 data/raw_comments.csv，使用 {fallback.name} 演示")
    return pd.read_csv(fallback)


def main():
    df = load_raw()
    n0 = len(df)

    df["评论内容"] = df["评论内容"].apply(normalize_text)

    # 1. 去空
    df = df[df["评论内容"].str.len() > 0]
    # 2. 去重（完全重复的评论只保留一条）
    df = df.drop_duplicates(subset=["评论内容"]).reset_index(drop=True)

    # 3. 一致性校验：人工标注列若存在，取值必须在合法标签内
    valid_labels = {"正面", "负面", "中性"}
    if "人工标注" in df.columns:
        bad = df[df["人工标注"].notna() & ~df["人工标注"].isin(valid_labels)]
        if len(bad):
            print(f"[校验警告] {len(bad)} 条人工标注标签非法：{bad['人工标注'].unique()}")

    out = DATA_DIR / "cleaned_comments.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"清洗完成：{n0} 条 -> {len(df)} 条（去重/去空 {n0 - len(df)} 条）")
    print(f"已保存：{out}")


if __name__ == "__main__":
    main()
