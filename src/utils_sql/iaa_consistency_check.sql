-- =====================================================================
-- iaa_consistency_check.sql
-- 标注者间一致性（IAA, Inter-Annotator Agreement）校验
-- 适用：SQLite / MySQL（日期函数略有差异，逻辑通用）
--
-- 表结构假设：
--   annotations(text_id, annotator_id, label_polarity, label_intensity,
--               label_ambiguity, labeled_at)
--   同一条文本 text_id 由 >=2 名标注员独立标注，用于计算一致性。
-- =====================================================================

-- 1. 双人标注配对：把同一条文本的两名标注员结果两两配对
WITH paired AS (
    SELECT
        a.text_id,
        a.annotator_id        AS annotator_a,
        b.annotator_id        AS annotator_b,
        a.label_polarity      AS label_a,
        b.label_polarity      AS label_b,
        CASE WHEN a.label_polarity = b.label_polarity THEN 1 ELSE 0 END AS agree
    FROM annotations a
    JOIN annotations b
      ON a.text_id = b.text_id
     AND a.annotator_id < b.annotator_id   -- 避免自配和重复配对
)

-- 2. 整体一致率（Simple Agreement）
SELECT
    COUNT(*)                                              AS 配对总数,
    SUM(agree)                                            AS 一致数,
    ROUND(SUM(agree) * 1.0 / COUNT(*), 3)                 AS 一致率
FROM paired;


-- 3. 按标注员对统计一致率（定位哪两位分歧最大，便于定向培训）
SELECT
    annotator_a,
    annotator_b,
    COUNT(*)                                  AS 共同标注数,
    SUM(agree)                                AS 一致数,
    ROUND(SUM(agree) * 1.0 / COUNT(*), 3)     AS 一致率
FROM paired
GROUP BY annotator_a, annotator_b
ORDER BY 一致率 ASC;


-- 4. 按文本统计分歧（找出争议样本，进入规则评审会讨论）
SELECT
    text_id,
    COUNT(DISTINCT label_polarity)           AS 不同标签数,
    GROUP_CONCAT(DISTINCT annotator_id)      AS 标注员,
    GROUP_CONCAT(label_polarity)             AS 各自标签
FROM annotations
GROUP BY text_id
HAVING COUNT(DISTINCT label_polarity) > 1
ORDER BY 不同标签数 DESC;


-- =====================================================================
-- 5. Cohen's Kappa（两位标注员 A1 / A2，三分类：正面/负面/中性）
--    kappa = (Po - Pe) / (1 - Pe)
--    Po = 观察一致率；Pe = 偶然一致率（由各标签边际分布算出）
--    判读：<0.4 一致性差 | 0.4-0.6 中等 | 0.6-0.8 较好 | >0.8 很好
-- =====================================================================
WITH a1 AS (
    SELECT label_polarity AS lab, COUNT(*) AS n
    FROM annotations WHERE annotator_id = 'A1' GROUP BY label_polarity
),
a2 AS (
    SELECT label_polarity AS lab, COUNT(*) AS n
    FROM annotations WHERE annotator_id = 'A2' GROUP BY label_polarity
),
tot AS (
    SELECT COUNT(*) AS n FROM annotations WHERE annotator_id = 'A1'
),
po AS (
    SELECT SUM(CASE WHEN x.label_polarity = y.label_polarity THEN 1 ELSE 0 END) * 1.0
           / (SELECT n FROM tot) AS Po
    FROM (SELECT text_id, label_polarity FROM annotations WHERE annotator_id='A1') x
    JOIN (SELECT text_id, label_polarity FROM annotations WHERE annotator_id='A2') y
      ON x.text_id = y.text_id
),
pe AS (
    SELECT SUM(a1.n * 1.0 / (SELECT n FROM tot) * a2.n * 1.0 / (SELECT n FROM tot)) AS Pe
    FROM a1 JOIN a2 ON a1.lab = a2.lab
)
SELECT
    ROUND(po.Po, 3)                                          AS 观察一致率Po,
    ROUND(pe.Pe, 3)                                          AS 偶然一致率Pe,
    ROUND((po.Po - pe.Pe) / (1 - pe.Pe), 3)                  AS Cohen_Kappa
FROM po, pe;
