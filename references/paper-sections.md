# 英文论文分节作战手册

面向 ML/DL 会议与期刊（NeurIPS / ICML / AAAI / TKDE 一类）。每一节给出：该节唯一任务、失败模式、可操作的改法、改前改后对照。

**示例中的数字全是占位**，不要直接引用。

---

## 0. 四条不变式

跨所有节成立，先记这四条：

1. **每节一个任务**。摘要卖结论，引言卖问题与贡献，实验卖证据。任务混了就必然啰嗦。
2. **评价性形容词必须与数字同句或邻句**。"显著优于" 要么补数字，要么删。
3. **每个 claim 有锚点**。指向表、图、节号或定理。锚不上的 claim 是愿望。
4. **`significantly` 只用于统计检验**。没有 p 值、置信区间或多种子方差，就写 `improves` / `reduces`。

---

## 1. Abstract

**唯一任务**：让读者在 150 词内知道"什么问题、你做了什么、证据多强"。

**典型结构**（不是模板，是信息顺序）：

| 位置 | 内容 | 常见错误 |
|---|---|---|
| 1 句 | 具体缺口，不是领域背景 | `In recent years, X has attracted increasing attention.` |
| 2 句 | 你做了什么、关键机制 | 只写"提出一个框架"不写机制 |
| 3 句 | 证据，带数字 | `Extensive experiments demonstrate superiority.` |
| 0–1 句 | 边界或含义 | 展望式空话 |

**判定清单**：

- 词数 120–220。超过 250 基本是引言压缩版。
- 至少 3 个具体数字（数据集数、指标、绝对或相对增益）。零数字的摘要说明作者自己也不知道结论多强。
- 不出现引用、不出现公式、不出现 "Section 3"。
- 第一句不出现 "recent years" / "with the rapid development" / "has attracted"。

**改前**
> In recent years, federated learning has attracted increasing attention due to growing privacy concerns. However, heterogeneity remains a significant challenge. In this paper, we propose a novel framework to address this issue. Extensive experiments demonstrate the effectiveness and superiority of our method.

**改后**
> Client heterogeneity makes federated averaging converge slowly when local updates drift. We bound that drift by capping the staleness of each update and show the cap can be set from the observed update norm rather than tuned per task. On CIFAR-10 with Dirichlet α=0.1, the method reaches 71.4% accuracy in 200 rounds, against 66.9% for the strongest baseline, with 1.3× the wall-clock per round.

差异不在用词，在于第二段每句都能被追问且答得出。

---

## 2. Introduction

**唯一任务**：建立"这个问题重要且未解决"到"你的做法可行"的推理链。

**四段骨架**（可合并，不可缺）：

1. 问题在具体场景下是什么（带一个数字或一个失败现象）
2. 现有做法为什么不够——**点名具体方法及其具体失效条件**，不写 "existing methods have limitations"
3. 你的洞察是什么（一句话，能被反驳的那种）
4. 你据此做了什么，证据在哪（指向节号）

**失败模式**：

| 模式 | 表现 | 改法 |
|---|---|---|
| 漏斗过长 | 三段背景才提到本文 | 背景压到 2 句，直接给缺口 |
| 缺口无主语 | `Existing methods still have limitations.` | 写清哪个方法、在什么条件下、失效成什么样 |
| 首创宣称 | `To the best of our knowledge, we are the first to...` | 删，或改成可核查的范围限定 `We are not aware of work that...` 并接受被反驳 |
| 与摘要重复 | 引言整段是摘要的扩写 | 引言补摘要没有的：为什么这条路走得通 |
| 贡献清单写成活动 | `We conduct extensive experiments on three datasets.` | 写发现，不写动作 |

**贡献条目写法**：每条一句话，形如「我们做了 X，因此 Y 在 Z 条件下成立（见 §4.2 / Table 2）」。三条不是配额，两条或四条都行。

---

## 3. Method

**唯一任务**：让读者能复现，并理解**为什么是这个设计而不是显然的替代方案**。

**失败模式**：

- 只有定义没有动机：公式连发三屏，读者不知道为什么要这样分解
- 符号无表：首次出现的符号必须就地定义，或在节首给符号表
- 用被动隐藏责任主体：`The gradients are clipped` → 谁 clip、何时 clip、clip 到多少
- `where` 链：`We define A as ..., where B is ..., and C denotes ...` 连续三段

**动机的标准句式**（很有效，直接用）：

> A natural alternative is ⟨显然做法⟩. It fails when ⟨具体条件⟩, because ⟨机制⟩. We instead ⟨你的做法⟩, which avoids ⟨代价⟩ at the cost of ⟨代价⟩.

写出代价很重要。没有代价的设计在读稿人眼里等于没想清楚。

**记号纪律**：

- 一个符号一种含义，全文不重用
- 向量粗体、矩阵大写、集合花体，全文一致
- 目标函数出现前，先说清优化变量

---

## 4. Experiments

**唯一任务**：让 claim 可验证，包括不利的部分。

**Setup 必须齐**：数据集与划分、client/样本数、模型与规模、超参、随机种子数、硬件、评估指标定义。缺一项就在附录，并在正文给指针。

**结果陈述的三条规则**：

1. **给绝对数，不只给相对数**。`improves by 4.5 points` 不如 `71.4% vs 66.9%`。
2. **说清比较条件**。同轮数？同墙钟？同参数量？三个不同答案会得出三个不同结论。
3. **不利结果要留**。某项指标落后时写清权衡，不要换评价标准，也不要把一个指标的落后写成方法整体有缺陷。

**`significantly` 的使用**：只有做了检验才能用。多种子跑出均值±标准差是最低要求（≥3 seeds）。只跑一个种子就写 `significantly` 是可以被直接质疑的。

**消融的写法**：
- 错：`Ablation shows each component is effective.`（循环论证：去掉就变差，所以有效）
- 对：`Removing the cap raises staleness to 12 rounds and drops accuracy to 67.1%, which is consistent with the drift bound in §3.2.`

消融要指向机制，不是指向"有效"。

**表格纪律**：只加粗本方法一行；标准差写在括号里；不要给不显著的差异标加粗或星号。

---

## 5. Related Work

**唯一任务**：定位，不是罗列。

**失败模式**：注释书目（`X et al. proposed ... Y et al. proposed ...`），读完不知道该引哪篇。

**改法**：按**机制**分组，每组一句话总结该组共同假设，然后一句说明你的工作与这组的差别。差异要具体到机制，不到"性能更好"。

> 错：`Federated averaging has been improved in many works [1,2,3,4].`
> 对：`Most staleness-aware methods bound the delay at the server [1,2]; we bound it at the client, which keeps the server aggregation unchanged and therefore composes with existing optimizers.`

**必查**：最强基线是否引了、是否比了。漏掉最强基线是审稿意见里最常见的一条，且与文笔无关。

---

## 6. Conclusion

**唯一任务**：说清结论的适用范围与下一步的具体问题。

**失败模式**：摘要复述、`In the future, we will extend to more datasets and tasks` 这类清单、零限制。

**改法**：一句结论（带最强数字）→ 一句边界（什么条件下不成立）→ 一句具体的下一步（一个可执行的问题，不是方向）。

**限制段**：单独一小段，写真实限制。放在这里不会削弱论文，放在摘要里才会。

---

## 7. Rebuttal

**唯一任务**：用证据回答审稿人问的那个问题。

**规则**：

- 先复述问题一句（证明读懂了），再给答案，再给证据位置
- 不做预防性道歉。`We are sorry for the confusion` 换成 `The intended meaning is ...; we will clarify in §3.`
- 不承认想象中的弱点。审稿人没提的问题，不要顺手自曝
- 补实验就报数字，不报"we will run"
- 措辞比正文更强硬：正文用 `suggest`，rebuttal 有证据就可以用 `show`

---

## 8. 动词阶梯（claim ladder）

按证据强度选动词，不要升级也不要降级：

| 证据 | 动词 |
|---|---|
| 定理、形式化证明 | `prove`, `guarantee` |
| 多数据集 + 多种子 + 有对照 | `show`, `demonstrate` |
| 单数据集 / 单种子 / 单一设置 | `improve`, `reduce`, `observe`（并写条件） |
| 相关性分析 | `is associated with`, `correlates with` |
| 机制假设、未验证解释 | `suggest`, `is consistent with`, `may` |
| 未做 | 不写 |

反向也查：正文出现 `prove` 但只有实验，必须降级。这是审稿人最快抓到的越界。

---

## 9. 一页速查

投稿前按顺序过：

1. 摘要有几个数字？<3 就去补或改结论
2. 引言第几句出现本文做法？>第 3 段就有问题
3. 每个贡献条目是否指向具体节/表？
4. 每个 `significantly` 后面是否有检验？
5. 每个评价性形容词是否邻句有数字？
6. 最强基线引了吗、比了吗？
7. 消融解释的是机制还是"有效性"？
8. 结论有没有一句真实的边界？
9. 全文 `we propose a novel` 出现几次？>2 就删到 1
10. 关掉 PDF，只看表格和摘要，能不能复述你的贡献？
