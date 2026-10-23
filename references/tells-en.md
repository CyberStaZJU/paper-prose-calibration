# 英文论文体 AI 痕迹清单

面向 ML/DL 论文（会议与期刊）。通用英文写作痕迹仍适用，但这里按**论文体中真正被审稿人扣分的形态**重排。

**Dated 2026-10.** 词表随模型代际漂移，见第 6 节。

---

## 1. 评价性形容词通胀（论文体第一大痕迹）

模型写结果时倾向用形容词替代数字，因为形容词是统计上更安全的下一词。

**黑名单**：novel, significant/significantly, substantial/substantially, remarkable, superior, comprehensive, extensive, effective, efficient, robust, promising, state-of-the-art, dramatic, drastic, considerable, notable, unprecedented, seamless.

**判定**：每个评价性形容词，看同句或邻句有没有数字、检验或明确比较条件。没有就删或换。

> 病：`Our method achieves significantly better accuracy and is more efficient than baselines.`
> 改：`On CIFAR-10 (α=0.1) our method reaches 71.4% at 200 rounds; FedAvg reaches 66.9% at the same round count, and both use 1.3 s per round.`

**`significantly` 单独一条铁律**：只用于统计检验。没有 ≥3 seeds 的均值±方差、或没有检验，就不能用。

---

## 2. 空承诺句式（论文体专属）

这些句子在任何论文里都不携带信息，且高度可识别：

| 句式 | 问题 |
|---|---|
| `Extensive experiments demonstrate the effectiveness of our method.` | 没有实验信息 |
| `Experiments show that our method outperforms state-of-the-art methods.` | 哪来的 SOTA、哪个指标、差多少 |
| `To this end, we propose a novel framework ...` | `to this end` + `novel` + `framework` 三连填充 |
| `Our method is simple yet effective.` | 删掉后信息量不变 |
| `This validates the superiority of our design.` | `validate` 越界（只有实验） |
| `We conduct comprehensive experiments on three datasets.` | 贡献条目写成活动 |
| `The results are promising and open new directions.` | 展望式空转 |

替换原则：**把"我们证明了有效"改成"我们在什么条件下观察到多少差异"**。

---

## 3. 越界与虚指

**动词越界**：`prove` / `validate` / `guarantee` 用于纯实验结论。审稿人最快抓这一条。按 `paper-sections.md` 第 8 节的动词阶梯降级。

**虚指归因**：

- `Recent studies have shown that ...`（哪些？）
- `It is widely accepted that ...`
- `Most existing methods suffer from ...`（哪些方法？哪一条？）
- `Prior work ignores ...`（忽略不等于没做）

判定：能否立刻写出 2–3 篇具体文献 + 年份。写不出就是虚指。

**假缺口**：`However, these methods still have limitations.` 必须改成「哪个方法、在什么条件下、失效成什么现象」。

---

## 4. 句法与结构痕迹

- **Copula 回避**：`serves as`, `stands as`, `represents a`, `boasts`, `features a` 替代 `is` / `has`。论文陈述本该用最平的系动词，所以这条在学术体里格外明显。
- **`-ing` 尾巴**：`..., highlighting the importance of X` / `..., underscoring Y`。附带的解释性从句通常没有证据支撑。
- **否定平行**：`It is not merely X; it is Y` / `not because X but because Y`。用一次可以，连着用是模板。
- **三项并列**：形容词三连（`simple, efficient, and effective`）与贡献三连。两项或四项更可信。
- **伪范围**：`from X to Y` 而 X、Y 不同尺度（`from small models to large-scale deployment`）。
- **`In this paper, we` 高频**：每段开头都来一次。删到只在必要处出现。
- **名词化堆叠**：`the utilization of ... for the improvement of ...`。动词还原。
- **分段等长**：每段 4–5 句、体量接近，是模板结构的副产品，不是论证需要。

---

## 5. 结构与排版痕迹

- **`Challenges and Future Prospects` 型收尾**：`Despite these advances, X faces several challenges ...` 后接乐观展望。
- **分形摘要**：文首、节首、段首各说一遍同一件事。
- **Bold-first bullets**：每条以粗体标签加冒号开头。
- **表格粗体滥用**：整列加粗、给不显著差异加粗或加星。
- **Title Case 小标题**。
- **Em dash**：见第 6 节，已是弱指标。
- **Curly quotes**：投稿模板里会出错，且是复制痕迹。

---

## 6. 词表代际（重要：会过期）

单词过用是分代际的，不要用 2023 年的表查 2026 年的稿子。

| 代际 | 高频词 |
|---|---|
| 2023 – 2024 中（GPT-4） | Additionally, boasts, bolstered, crucial, **delve**, emphasizing, enduring, garner, intricate, interplay, key, landscape, meticulously, pivotal, underscore, tapestry, testament, valuable, vibrant |
| 2024 中 – 2025 中（GPT-4o） | align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant |
| 2025 中 – 2026 中（GPT-5） | emphasizing, enhance, highlighting, showcasing + 归因/知名度集群 |
| 2026 中以后（GPT-6） | challenge, clearer, dependable, echoed, foster, leverage, matters, multifaceted, practical, prioritize, quietly, steady, universally |

两点容易误判：

- `delve` 在 2025 年已崩落。今天还在抓它，抓的是旧文本。
- GPT-6 那批词看着无害（`practical`, `steady`, `matters`），靠直觉抓不到，只能靠密度。

**Em dash 已降级**：GPT-5.1 起被硬性压制，2026 年 7 月的研究里 ChatGPT 用破折号比专业作家还少。**反向指标反而更强**——标点只剩逗号句号、句长挤在 8–20 词区间，是新一代指纹。

---

## 7. 引文层面

- 引用只出现在 Related Work，正文从不回指 → 定位缺失
- 参考文献列表里有、正文从未引用 → 结构错误
- 引用了最强基线，但结果表里没有它
- `et al.` 用在两作者文献上
- 引用预印本却当作已发表结论使用

---

## 8. 论文体快速自查（8 条）

1. 摘要数字 <3 个？
2. `significantly` 出现次数 > 检验次数？
3. 评价性形容词里有多少能在邻句找到数字？
4. `novel` / `framework` / `comprehensive` 合计 >4 次？
5. 有没有 `prove` / `validate` 用在纯实验结论上？
6. 引言第几段才出现本文做法？
7. 每个贡献条目是否指向节号或表号？
8. 关掉正文只看摘要与表格，能复述贡献吗？

---

## 9. 这些痕迹指向的真问题

Wikipedia 的田野指南明确说：这些是问题的**迹象**，不是问题本身。论文体里对应的真问题只有四个：

1. claim 没有证据锚点
2. 具体设置被概括掉（数据集、条件、种子）
3. 解释附在撑不住它的数据上
4. 缺口靠断言而非文献建立

只改表面，会让稿子更难被识别，但审稿人照样拒。任何风格改写都必须配一次证据补强或范围校准。
