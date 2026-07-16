# Four-sample UAT source truth

This ledger was derived from the source PDFs before the new Worker outputs were inspected. It is the independent reference for source identity, page coverage, and table-of-contents scoring.

## Source identity

| UAT sample | Upload filename | Bytes | Pages | Source type | SHA-256 |
| --- | --- | ---: | ---: | --- | --- |
| 001 | `test20260716001.pdf` | 175841 | 3 | born-digital English article | `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad` |
| 002 | `test20260716002.pdf` | 78077 | 2 | born-digital multi-column word list | `c953cb08f79c2d114c55e4078c82f53af69bc154a73ed0f78a38634183f278ab` |
| 003 | `test20260716003.pdf` | 905120 | 31 | image-only Grade 7 mathematics workbook | `6f3dd4b91dedf81e0a2f7508b4518b9b20ad0012f535aedafc8da80dcde39992` |
| 004 | `test20260716004.pdf` | 60553426 | 252 | image-only Grade 5 mathematics guide | `5c08239421effc942ceacca225d9cbb950b89018c1fd3ed2d82266dd8758cfb2` |

## Directory classification

- 001 has no formal table of contents. Expected reconstruction: no invented chapter hierarchy; retain the article heading and reading order only.
- 002 has no formal table of contents. Expected reconstruction: no invented chapters; retain the Academic Word List ordering and column/row sequence.
- 003 has no formal table-of-contents page in the 31-page source. Expected reconstruction: do not invent a publisher TOC. If a navigational outline is produced from visible worksheet headings, it must preserve source order and be explicitly distinguished from a source TOC.
- 004 has a formal two-page table of contents on source PDF pages 7–8. Its entries below are the scoring truth.

## Sample 004 formal TOC truth

| Level | Title | Printed page |
| ---: | --- | ---: |
| 1 | 一、复习与提高 | — |
| 2 | 1 符号表示数 | 1 |
| 2 | 2 小数 | 8 |
| 2 | 第一单元知识导图 | 16 |
| 2 | 第一单元综合练习 | 17 |
| 1 | 二、小数乘除法 | — |
| 2 | 1 小数乘整数 | 21 |
| 2 | 2 小数乘小数 | 30 |
| 2 | 3 连乘、乘加、乘减 | 40 |
| 2 | 4 整数乘法运算定律推广到小数 | 46 |
| 2 | 5 除数是整数的小数除法 | 53 |
| 2 | 6 除数是小数的除法 | 62 |
| 2 | 7 循环小数 | 72 |
| 2 | 8 用计算器计算 | 78 |
| 2 | 9 积、商的近似数 | 82 |
| 2 | 第二单元知识导图 | 87 |
| 2 | 第二单元综合练习 | 88 |
| 1 | 三、统计 | — |
| 2 | 1 平均数 | 92 |
| 2 | 2 平均数的计算 | 98 |
| 2 | 3 平均数的应用 | 104 |
| 2 | 第三单元知识导图 | 111 |
| 2 | 第三单元综合练习 | 111 |
| 1 | 四、简易方程（一） | — |
| 2 | 1 用字母表示数 | 116 |
| 2 | 2 化简与求值 | 123 |
| 2 | 3 方程 | 131 |
| 3 | 第1课时 等量关系与方程 | 131 |
| 3 | 第2课时 解方程 | 134 |
| 2 | 4 列方程解决问题（一） | 143 |
| 2 | 第四单元知识导图 | 150 |
| 2 | 第四单元综合练习 | 151 |
| 1 | 五、几何小实践 | — |
| 2 | 1 平行四边形 | 155 |
| 2 | 2 平行四边形的面积 | 164 |
| 2 | 3 三角形的面积 | 170 |
| 2 | 4 梯形 | 177 |
| 2 | 5 梯形的面积 | 182 |
| 2 | 6 组合图形的面积 | 188 |
| 2 | 第五单元知识导图 | 194 |
| 2 | 第五单元综合练习 | 195 |
| 1 | 六、整理与提高 | — |
| 2 | 1 小数的四则混合运算 | 199 |
| 2 | 2 小数应用——水、电、天然气的费用 | 209 |
| 2 | 3 列方程解决问题（二） | 215 |
| 2 | 4 图形的面积 | 220 |
| 2 | 5 数学广场——时间的计算 | 228 |
| 2 | 6 数学广场——编码 | 234 |
| 2 | 第六单元知识导图 | 237 |
| 2 | 第六单元综合练习 | 238 |

## Scoring rule

Score each sample independently after Worker output exists. For sample 004, normalize only whitespace and punctuation variants before matching; do not normalize away missing words, wrong order, wrong hierarchy, or wrong page mapping. Report precision, recall, and F1 for titles, hierarchy, order, and page mapping. Each required metric must be at least 99%. Samples 001–003 pass the directory gate only if the no-formal-TOC classification is preserved without invented publisher structure.
