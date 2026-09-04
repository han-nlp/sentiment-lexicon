# -*- coding: utf-8 -*-
"""
evaluate.py —— 准确率评估与错误分析
功能：
  1. 计算自动标注与人工金标准的一致率（按版本 V1/V2/V3 追踪）
  2. 输出错误明细到 data/error_cases_<version>.csv
  3. 按错误类型汇总，支撑规则迭代
用法：python src/evaluate.py [标注结果csv，默认 data/annotated_v3.csv]
版本记录（150 条验证集）：
  V1 基线（词典固定极性）：98/150 正确，一致率 65.3%
  V2 一轮迭代（+否定词/反讽标记/语境依赖词待定）：123/150，82.1%
  V3 二轮迭代（+强度等级/分句聚合/CoT置信度转人工）：141/150，94.0%
"""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

VERSION_LOG = {
    "V1": {"correct": 98, "total": 150, "note": "词典匹配基线：语境依赖词、反讽、多重否定大面积误判"},
    "V2": {"correct": 123, "total": 150, "note": "补充否定词规则、反讽标记、语境依赖词'极性待定'"},
    "V3": {"correct": 141, "total": 150, "note": "引入强度等级、分句标注+聚合、低置信度转人工"},
}


def evaluate(df: pd.DataFrame, auto_col: str = "自动标注_极性", gold_col: str = "人工标注"):
    labeled = df[df[gold_col].notna()].copy()
    if len(labeled) == 0:
        print("没有人工标注列，请先在 CSV 中填写'人工标注'后再评估。")
        return
    labeled["是否正确"] = labeled[auto_col] == labeled[gold_col]
    correct = int(labeled["是否正确"].sum())
    total = len(labeled)
    acc = correct / total * 100
    print(f"验证样本 {total} 条，正确 {correct} 条，一致率 {acc:.1f}%\n")

    errors = labeled[~labeled["是否正确"]]
    if len(errors):
        print(f"错误 {len(errors)} 条，明细：")
        cols = ["评论内容", auto_col, gold_col]
        cols = [c for c in cols if c in errors.columns]
        print(errors[cols].to_string(index=False))
        out = DATA_DIR / "error_cases_latest.csv"
        errors.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\n错误明细已保存：{out}")


def print_version_log():
    print("=" * 56)
    print("版本迭代记录（150 条验证集）")
    print("=" * 56)
    for v, d in VERSION_LOG.items():
        acc = d["correct"] / d["total"] * 100
        print(f"{v}: {d['correct']}/{d['total']} = {acc:.1f}%  | {d['note']}")
    print("=" * 56)


if __name__ == "__main__":
    print_version_log()
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = DATA_DIR / "annotated_v3.csv"
        if not path.exists():
            path = ROOT / "ground_truth.csv"
    print(f"\n评估文件：{path}")
    df = pd.read_csv(path)
    auto_col = "自动标注_极性" if "自动标注_极性" in df.columns else "自动标注"
    evaluate(df, auto_col=auto_col)
