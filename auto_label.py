import pandas as pd
import time
from sentiment_dict import sentiment_dict

#==========1. 读取数据==========
df = pd.read_csv("d:/py学习/xhs_comment.csv")
print(f"共读取 {len(df)} 条评论")

#==========2. 定义自动标注函数==========
def auto_label(text):
    #升级标注规则:优先匹配情感强度更高的词.如果一句话里同时出现正面词,负面词和中性词,取最后匹配到的非中性词,避免被开头的'咱就是说'等中性词带偏.
    last_sentiment = "中性"

    for word, sentiment in sentiment_dict.items():
        if word in text:
            if sentiment !="中性":
                last_sentiment = sentiment
            elif last_sentiment == "中性":
                last_sentiment = "中性"
    
    return last_sentiment
#==========3. 对全部评论进行自动标注==========
df["自动标注"] = df["评论内容"].apply(auto_label)

#==========4. 统计结果==========
print("\n===自动标注结果统计===")
print(df["自动标注"].value_counts())

#==========5. 保存结果==========
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f"auto_label_{timestamp}.csv"
df.to_csv(filename,index=False,encoding="utf-8-sig")
print(f"标注完成,已保存到{filename}")