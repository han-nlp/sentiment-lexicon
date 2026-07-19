import pandas as pd

df = pd.read_csv("d:/py学习/ground_truth.csv")

labeled = df[df["人工标注"].notna()]

if len(labeled) == 0:
    print("还没有人工标注,请先在csv里填写'人工标注'列")
else:
    correct = (labeled["自动标注"] == labeled["人工标注"]).sum()
    total = len(labeled)
    accuracy = correct / total * 100
    print(f"人工校验了 {total} 条评论,其中自动标注正确的有 {correct} 条,准确率为 {accuracy:.1f}%")

    errors = labeled[labeled["自动标注"] != labeled["人工标注"]]
    print(f"\n标错{len(errors)}条,明细如下:")
    for _,row in errors.iterrows():
        print(f"原文:{row['评论内容']}")
        print(f"  自动标注: {row['自动标注']} -> 人工标注: {row['人工标注']}")
        print()