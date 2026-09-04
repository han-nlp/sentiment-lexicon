# -*- coding: utf-8 -*-
"""
annotate.py —— 三维规则标注引擎（V3 版）
三维输出：情感极性（正面/负面/中性）+ 强度等级（1-5）+ 歧义标记（反讽/双关/多义/无）
关键规则：
  1. 情感词典来自 data/sentiment_lexicon.csv（含极性、强度、语境依赖标记）
  2. 否定词计数：偶数次否定还原极性（"不是不喜欢"=喜欢）
  3. 转折规则：以"但是/然而/可是"之后的内容为主极性
  4. 反讽规则：正面评价词搭配明显负面事件（期望违背）-> 极性翻转并标记"反讽"
  5. 置信度 < 60 或命中"语境依赖"词但无明确语境 -> 歧义标记"多义"，建议转人工
用法：python src/annotate.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

NEGATIONS = ["不", "没", "无", "非", "别", "未"]
TURNING = ["但是", "然而", "可是", "不过", "但"]
IRONY_SIGNALS = ["可真好", "真好啊", "真厉害", "高手啊", "可真有你的", "绝绝子"]
NEG_EVENT = ["卡", "bug", "排队", "挂", "失败", "翻车", "差评", "后悔", "坑", "离谱", "迟到", "坏"]


def load_lexicon():
    df = pd.read_csv(DATA_DIR / "sentiment_lexicon.csv")
    lex = {}
    for _, r in df.iterrows():
        lex[r["词语"]] = {
            "polarity": r["极性"],
            "intensity": int(r["强度"]),
            "context_dep": str(r["语境依赖"]).strip() == "是",
        }
    return lex


def detect_irony(text: str) -> bool:
    """期望违背：反讽信号词 与 负面事件 共现。"""
    has_signal = any(s in text for s in IRONY_SIGNALS)
    has_neg_event = any(e in text for e in NEG_EVENT)
    question_tone = "？" in text or "?" in text
    return has_signal and has_neg_event and (has_neg_event or question_tone)


def polarity_after_negation(base: str, neg_count: int) -> str:
    if base == "中性" or neg_count == 0:
        return base
    if neg_count % 2 == 1:  # 奇数次否定，极性翻转
        return {"正面": "负面", "负面": "正面"}.get(base, base)
    return base  # 偶数次否定，还原


def annotate_one(text: str, lex: dict) -> dict:
    # 转折：取转折词之后的片段做极性判断
    seg = text
    for t in TURNING:
        if t in text:
            seg = text.split(t)[-1]
            break

    irony = detect_irony(text)

    hits = []
    neg_count = sum(seg.count(n) for n in NEGATIONS)
    for word, info in lex.items():
        if word in seg:
            hits.append((word, info))

    # 取强度最高的非中性命中作为主情感
    non_neutral = [h for h in hits if h[1]["polarity"] != "中性"]
    context_dep_hit = any(h[1]["context_dep"] for h in hits)

    ambiguity = "无"
    if irony:
        ambiguity = "反讽"
    elif context_dep_hit and len(non_neutral) == 0:
        ambiguity = "多义"

    if not non_neutral:
        polarity, intensity, conf = "中性", 1, 70
    else:
        word, info = max(non_neutral, key=lambda h: h[1]["intensity"])
        polarity = polarity_after_negation(info["polarity"], neg_count)
        intensity = info["intensity"]
        # 置信度：语境依赖词打折，反讽/多义降权
        conf = 90
        if info["context_dep"]:
            conf -= 20
        if ambiguity in ("反讽", "多义"):
            conf -= 15
        if neg_count:
            conf -= 10

    if irony:  # 反讽翻转极性
        polarity = {"正面": "负面", "负面": "正面"}.get(polarity, polarity)

    if conf < 60:
        ambiguity = ambiguity if ambiguity != "无" else "多义"

    return {
        "自动标注_极性": polarity,
        "自动标注_强度": intensity,
        "歧义标记": ambiguity,
        "置信度": conf,
        "是否建议转人工": "是" if conf < 60 else "否",
    }


def main():
    lex = load_lexicon()
    src = DATA_DIR / "cleaned_comments.csv"
    if not src.exists():
        src = ROOT / "ground_truth.csv"
    df = pd.read_csv(src)

    results = df["评论内容"].apply(lambda t: pd.Series(annotate_one(str(t), lex)))
    out = pd.concat([df, results], axis=1)

    out_path = DATA_DIR / "annotated_v3.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(out[["评论内容", "自动标注_极性", "自动标注_强度", "歧义标记", "置信度"]].to_string(index=False))
    print(f"\n已保存：{out_path}")


if __name__ == "__main__":
    main()
