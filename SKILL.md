---
name: prose-calibration
description: "Diagnose and rewrite machine-sounding English academic prose, section by section, along four axes: information density, stance calibration, template form, and claim-to-evidence traceability. Targets the failure modes that get ML/DL papers rejected on writing: adjective inflation without numbers, empty claims such as 'extensive experiments demonstrate effectiveness', misuse of 'significantly' and 'prove' without statistical support, gaps asserted instead of cited, and contributions that describe activities rather than findings. Also handles Chinese technical documents, SOPs, and reports. Use when revising an abstract, introduction, contributions list, method section, experiments section, related work, conclusion, or rebuttal; when a draft reads like ChatGPT/GPT output, feels padded, evasive, over-cautious, or uniformly rhythmical; or when a reviewer says the writing is vague. Enforces a no-fabrication guardrail: a style pass must be paired with at least one specificity or scope correction, and every surviving claim must be anchored to a table, figure, or section."
description_zh: "文风校准（论文优先）：英文论文分节改写，四轴诊断、claim 锚点核查、禁止洗稿"
description_en: "Section-aware calibration of English academic prose: strip AI tells and defensive hedging, force numbers and claim anchors"
version: 2.1.1
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
display_name: "文风校准"
display_name_en: "prose-calibration"
visibility: "public"
agent_created: true
---

# 文风校准（论文优先）

改写"读起来像模型写的"文本。主战场是**英文 ML/DL 论文正文**；中文技术文档、SOP、汇报为次要场景。

目标不是骗过检测器，是让每一句都承担信息，且每个 claim 都能指到证据。

## 何时使用

- 改摘要、引言、贡献列表、方法节、实验节、相关工作、结论、审稿回复
- 稿子被说"太虚""说了等于没说""AI 味重""读起来不像人写的"
- 审稿意见指出 writing is vague / claims are not supported / contributions are unclear
- 中文技术方案、SOP、汇报材料需要去模板化

不适用：代码、数学推导、需逐字保持的法律条文。文学创作只动第二节的形式轴，不要碰作者腔调。

## 一、四条不变式

跨所有节成立，先记这四条：

1. **每节一个任务**。摘要卖结论，引言卖问题与贡献，实验卖证据。任务混了必然啰嗦。
2. **评价性形容词必须与数字同句或邻句**。"significantly better" 要么补数字，要么删。
3. **每个 claim 有锚点**。指向表、图、节号或定理。锚不上的 claim 是愿望，不是结论。
4. **`significantly` 只用于统计检验**。没有 ≥3 seeds 的均值±方差或检验，改写为 `improves` / `reduces`。

## 二、四轴模型

逐句标注，不要通读一遍凭感觉整体重写。

### 轴 A｜信息密度

| 状态 | 判据 | 处置 |
|---|---|---|
| 承重 | 含数字、条件、机制、可核查事实、明确操作 | 保留，不许为"简洁"削掉限定 |
| 待补 | 观点成立但缺关键参数/来源/条件 | 补，或标 `[TODO: 具体内容]` |
| 虚指 | 挂给"recent studies""most methods"而无具体文献 | 补具体文献+年份，补不出就降级或删 |
| 空转 | 删掉后读者信息量不变 | 删 |

判据只有一条：**删掉这句，读者会不会少知道一件事**。

### 轴 B｜姿态校准

按证据等级选动词，不升级也不降级。反向也查：正文出现 `prove` 但只有实验，必须降级——这是审稿人最快抓到的越界。

| 证据 | 动词 |
|---|---|
| 定理、形式化证明 | prove, guarantee |
| 多数据集 + 多种子 + 有对照 | show, demonstrate |
| 单数据集 / 单种子 / 单一设置 | improve, reduce, observe（条件写进同句） |
| 相关性分析 | is associated with, correlates with |
| 机制假设、未验证解释 | suggest, is consistent with, may |
| 未做 | 不写 |

欠断言（`might possibly suggest`）与过断言（`prove` 用在单种子上）都是病，方向相反而已。

**限缩密度要单独数。** 实测一份 1.1 万词的稿子，在 35 行内连出四处自我限缩：

> Means are reported without formal significance tests / the main claim remains narrow / should be read as fixed-configuration evidence / it is not a claim that every baseline is intrinsically weak

单看每句都诚实，四句连读的效果是**先替审稿人把稿子否了**。判据：一节内超过 2 处「不是…／只能…／应读作…」，且其中至少一处是审稿人没问的，就得删。删的优先级——作者没被质疑的免责 > 重复声明 > 具体条件下的限定（这条要留）。

区别在于：**限定条件要留，自我贬低要删。**`At α=0.01 the gain disappears` 是信息，`the main claim remains narrow` 是姿态。

### 轴 C｜模板形式

结构、句法、标点、词表四层。**判定原则优先于词表**，因为词表按模型代际漂移。

- 结构：短节是否都以小结收尾、是否有 `Challenges and Future Prospects` 型段落、段落是否等长
- 句法：句长变异系数、8–20 词带占比、三项并列、否定平行、`-ing` 解释尾巴、copula 回避
- 标点：破折号与分号是否成瘾；**反向也查**——只剩逗号句号、句长挤在 8–20 词，是新一代指纹
- 词表：命中密度，不是单词命中

### 轴 D｜可溯性（论文专属）

对每个存活的 claim 问：读者要在哪里验证它？

| 情况 | 处置 |
|---|---|
| 能指到具体表/图/节/定理 | 加锚点（`(Table 2)`、`(§4.3)`） |
| 只能指到"我们的实验" | 补具体设置，或删 |
| 指不到任何东西 | 降级为假设，或删 |

贡献条目必须逐条能指到节或表。消融段落必须指向机制（§3.2 的界），不是指向"有效"。

## 三、流程

### 第 0 步｜定位节

先确认改哪一节。不同节规则不同（见 `references/paper-sections.md`）。用户没说就按文本特征判断：出现 `we propose` 与贡献列表多半是引言，出现数字与 `±` 多半是实验。判断不了就问一句。

### 第 1 步｜机器体检

```bash
python3 scripts/prose_scan.py --file draft.tex --paper
```

`--paper` 追加论文指标：数字密度、8–20 词带占比、评价性形容词密度、动词阶梯分布、空承诺句式、虚指归因、hedge 堆叠、名词化密度、`significantly` 与检验的配对、claim 锚点数、定理环境数、分节词数、摘要专项。

喂 `.tex` 时脚本会先剥 preamble、注释、浮动体、标题行，只统计正文散文——**表里的数字不算证据，`%-----` 不算破折号**。这一步在真实稿件上先后修过 5 个 bug，回归用例最后 5 条守着它；换论文模板后如果分节词数明显不对，先查那里。

读法：不看单项绝对值，看**三项以上同时偏**。单项超标可能只是体裁惯例。样本 <300 词时密度类指标不稳定，只看方向。

脚本算不出的（语义空转、虚构引用、因果越界、限缩密度）必须人工读，不要假装脚本给了结论。

### 第 2 步｜逐句四态

按轴 A 给每句打标，只标不写。防止整体改写把承重句一起冲掉。

### 第 3 步｜四手术

只动被标记的句子，一次一种：

- **S1 删**：空转句整句删，不留半句
- **S2 换**：形容词换数字（`significantly better` → `71.4% vs 66.9%`）；抽象名词换具体；被动换主动；`serves as` 换 `is`
- **S3 并/拆**：一句里塞了论证、限定、道歉、例外就拆开；三句说同一件事就并
- **S4 补**：补条件、补种子数、补比较条件、补失效情形。**只能补原文已有依据的内容**，补不出标 `[TODO: ...]`

### 第 4 步｜锚点补全

给每个存活 claim 加节/表/图指针（轴 D）。加不上的回到第 3 步降级或删。论文体里这一步最容易被跳过，跳过的结果是稿子读起来顺、但站不住。

### 第 5 步｜节奏复核

改完重读，专查过度矫正：

- 句长是否变齐整（把长短句改没了）
- 标点是否只剩逗号句号
- 是否每段都变成三句
- 是否把作者原有的插入语、限定从句全部磨平

命中任一条就是改过头。用自然手段恢复：补一个具体数字、拆一个条件从句、保留作者原本的一处口语。**不要随机插破折号**。

### 第 6 步｜交付

见第五节。

## 四、判定表：什么必须留

去 AI 味最常见的错误是把该留的一起删了。下列内容即使读着"啰嗦"也保留：

| 内容 | 为什么留 |
|---|---|
| 数据集、划分、client/样本数、模型规模 | 可复现性的最小集 |
| 随机种子数、均值±方差、检验方法 | 支撑 `significantly` 的唯一依据 |
| 硬件、超参、轮数、墙钟 | 读者据此判断比较是否公平 |
| 适用范围与失效条件 | 读者据此决定能不能用 |
| 与基线的差距方向（哪怕不利于自己） | 删掉就是藏负面结果 |
| 观察性设计的因果限制 | 删掉即越界 |
| 最强基线及其结果 | 漏掉是最常见的审稿意见 |
| 伦理、许可、数据可用性声明 | 不可协商 |
| SOP 中的禁止项与前置条件 | 删掉会致误操作 |

可以删且通常该删：

- 复述标题的段首句、`In recent years, X has attracted increasing attention`
- `It is worth noting that` / `To this end` / `In this paper, we`
- 预告"本文将……"后又完整重复目录
- 同一限定在摘要、引言、结论各说一遍（留一处，通常在限制节）
- 展望式收尾（`The future looks bright` / `open new directions`）
- 为防假想批评而追加的自我辩解、预防性道歉

## 五、输出协议

默认三段，不写长篇解释：

**1. 体检摘要**（≤8 行）

只列触发问题的指标，带数值与判断。没跑脚本就写人工观察到的模式，不伪造数值。

**2. 改写稿**

直接给可用文本。保持术语、编号、公式、`\cite{}`、`\ref{}` 不动。LaTeX 命令不翻译。

**3. 变更清单 + 锚点缺口 + 残余风险**

| 原句（截断） | 手法 | 理由 |
|---|---|---|
| …… | S2 换 | 形容词换数字，见 Table 2 |
| …… | S1 删 | 空转，删后信息量不变 |
| …… | S4 补 | 补种子数与轮数，原文 §4.1 已有 |

**锚点缺口**：哪些 claim 现在指不到表/图/节，需要作者补实验或补引用。

**残余风险**：哪些地方没敢改，因为缺证据（"这里写 `significantly` 但只有单种子，需要补跑或改成 `improves`"）。这一节比改写稿更重要，不要省。

若用户只要"改得像人写的"而拒绝补内容：明确说明纯样式改写只降低表面痕迹，不改变证据强度，且会让问题更难被发现。

## 六、硬性禁令

1. 不得虚构数字、数据集、引用、机制、引语。补不出就留 `[TODO]`。
2. 不得把相关性写成因果，不得把单数据集/单种子结论写成普适结论。
3. 不得删除影响有效性、适用范围、伦理法律的限定。
4. 不得在无检验的情况下保留或新增 `significantly`。
5. 不得把 `prove` / `validate` / `guarantee` 用于纯实验结论。
6. 不得删除最强基线，或只引用不比较。
7. 不得把消融写成"验证了各模块的有效性"而不指向机制。
8. 不得交付纯样式改写。至少一处必须是信息补强或范围校准，否则拒改并说明原因。
9. 不得机械套用词表。词表按代际更新，同一词在技术语境可能是唯一准确说法。
10. 不得过度矫正。为去掉一个指纹而制造另一个（标点单调、句长齐整、段落等长）是失败。
11. 不得声称"已通过 AI 检测"。检测器不可靠，人的判断也不可靠。

## 七、分节规则

改论文时**必读** `references/paper-sections.md`，那里有每节的骨架、失败模式与改前改后对照。摘要与实验两节尤其不能凭感觉改。

其他参考：

- `references/tells-en.md` — 英文论文体痕迹：形容词通胀、空承诺句式、动词越界、词表代际
- `references/tells-zh.md` — 中文 AI 味：词表、句式、结构、文献报告的量化差异
- `references/defensive.md` — 防御性写作判定与改写，含中文 SOP 专用规则
- `references/metrics.md` — 指标定义、阈值性质、脚本覆盖范围与已知局限
- `tests/run_cases.py` — 回归用例。改过脚本阈值、正则或词表后必须跑一遍

## 八、与相邻技能的分工

| 技能 | 管什么 | 不管什么 |
|---|---|---|
| 本技能 | 论文/技术/公文的信息密度、姿态校准、模板拆解、claim 锚点，中英双语 | 文学腔调、营销文案情绪设计 |
| humanizer | 英文博客科普的 AI 腔与"注入个性" | 证据强度、限定保留、论文结构 |
| anti-defensive-writing | 学术示弱与堆叠情态 | 空承诺句式、词表通胀、锚点缺失 |

顺序：本技能做结构与姿态 → humanizer 做语言质感。反过来会二次改写。

## 九、四种启动方式

**只改摘要素描**
> 读摘要 → `--paper` 体检 → 查数字数（<3 就停，先让作者定结论）→ 四态标注 → 改写 → 输出

**改实验段**
> 先查每条结果陈述是否有绝对数、比较条件、种子数 → 补锚点（Table N）→ 再动语言

**改贡献列表**
> 每条改成「做了什么 + 因此什么成立 + 见 §/Table」→ 把活动型条目（conduct experiments）改成发现型

**审稿回复**
> 先复述问题 → 给答案 → 给证据位置 → 删道歉与自曝 → 有证据的可用 `show`

**只诊断不改写**
> 体检摘要 + 四态标注 + 三条最该修的问题。不动原文。
