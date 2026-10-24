# paper-prose-calibration

一个给英文学术写作去 AI 味的技能，配一个零依赖的检查脚本。能吃 LaTeX 源码、Markdown 和中文稿。

A skill for stripping AI-writing tells out of academic prose. It triages sentences before rewriting, and ships a zero-dependency scanner that understands LaTeX.

## 一段对照

输入 45 词，脚本报 5 条：

> In recent years, federated learning has attracted increasing attention due to growing privacy concerns. However, client heterogeneity remains a significant challenge. To this end, we propose a novel framework that addresses this issue comprehensively. Extensive experiments demonstrate the effectiveness and superiority of our proposed approach.

| 指标 | 值 |
|---|---|
| 空承诺句式 | 6 处 |
| 评价性形容词 | 11.1 / 百词 |
| 名词化 | 11.1 / 百词 |
| 数字 | 0 |

改后 79 词，0 条：

> When clients hold different label distributions, their local updates point in conflicting directions and averaged progress stalls. We cap how far a client's update may drift from the current global model before it is down-weighted, which leaves the server aggregation unchanged. On CIFAR-10 with Dirichlet α=0.3, this reaches 68.4% in 200 rounds against 64.1% for FedAvg, at 1.08× the wall clock. The gap closes to 0.5 points below α=0.05.

四项全动，都在信息层：数字 0 → 10.1/百词，形容词 11.1 → 0，空承诺 6 → 0。句长几乎没变（CV 0.24 → 0.31）。把换同义词和删破折号做一遍，这四个数一个都不会动。

## 四根轴

| 轴 | 查什么 | 典型病 |
|---|---|---|
| A 信息密度 | 每句是否推进 | 「随着……的发展」开篇、三段式总—分—总、挑战与展望段 |
| B 姿态校准 | 断言强度对得上证据等级吗，两个方向都调 | 欠断言：`might possibly suggest`；过断言：单种子写 `prove`、`significantly` 无检验 |
| C 形式 | 结构、句法、标点、词表 | 连接词起句、三项并列、否定平行、`-ing` 解释尾巴、copula 回避 |
| D 可溯性 | claim 能不能指到 Table、Figure、§ 或定理 | `extensive experiments demonstrate the effectiveness`、贡献条目指不到节表 |

D 轴是论文体独有的，通用 AI 味清单不管这一维，而审稿人扣分主要扣在这里。

B 轴有个反向的漏项：连续自我限缩。单看每句都诚实，连读下来等于先替审稿人否定了稿子。技能里区分了限定条件和自我贬低。`At α=0.01 the gain disappears` 是信息，留；`the main claim remains narrow` 是贬低，删。

现成的 AI 味清单基本是词表，而词表会过期。`delve` 在 2025 年的语料里已经消失，GPT-5 期换成 `emphasizing`、`highlight`。另一头，破折号被压制之后，句长挤在 8–20 词成了更强的指纹，于是「删光破折号」本身又在制造新痕迹。所以这里把词表当版本化快照用，判据放在结构和证据上，脚本会专门查 8–20 词带占比是否超过 80%。

## 安装

```bash
git clone https://github.com/CyberStaZJU/paper-prose-calibration.git \
  ~/.workbuddy/skills/prose-calibration
```

Claude Code 换目标路径 `~/.claude/skills/prose-calibration`。目录名保持 `prose-calibration`，跟 `SKILL.md` 里的自引用对得上。其他能读 SKILL.md 的 agent 直接指过去就行。

触发：说「帮我把这段改得像人写的」「这段太 AI 了」「审一下我论文的摘要」，或敲 `/prose-calibration`。

## 用法

```bash
python3 scripts/prose_scan.py --file paper.tex --paper    # 体检，不改文件
python3 scripts/prose_scan.py --file paper.tex --paper --json   # 接 CI
python3 scripts/prose_scan.py --file draft.md            # 中文，或英文非论文体
```

`--paper` 追加论文指标：数字密度、8–20 词带占比、评价性形容词密度、动词阶梯分布、空承诺句式、虚指归因、hedge 堆叠、名词化密度、`significantly` 有无检验、claim 锚点数、分节词数、摘要专项。

只要 Python 3.8+，不装依赖，不写文件。

## 测什么，测不出什么

能算：句长分布与变异系数、标点类别数、词表命中、数字密度、动词分层、空承诺、虚指归因、锚点数。

测不出：语义空转、虚构引用、因果越界、论证能不能成立。`references/metrics.md` 列了 9 项必须人工看的清单，也写明了阈值是启发式，没有文献依据支撑成普适判据。

一个具体的边界：脚本分不清「引号里举反例」和「真的这么写」。改写稿里残留的那 1 处 `显著提升` 是被当作反例引用的，照样报。

## 在真实 LaTeX 上踩过的坑

第一版直接在 `.tex` 源码上统计，数字全错。这是拿两篇在投稿件跑过之后才发现的：

| 指标 | 错的值 | 真实值 | 原因 |
|---|---|---|---|
| 极短句占比 | 43% | 1% | 表格行被当成了句子 |
| 数字密度 | 7.0/百词 | 2.6/百词 | 表格里的准确率被当成证据 |
| 破折号 | 24.2/千词 | 1.1/千词 | `%---------` 注释分隔线被算成破折号 |
| Method 节词数 | 整节消失 | 2380 词 | `\section{Method: \method{}}` 嵌套花括号让正则失配 |
| 正文字数 | 9485 | 7181 | 每节首段因标题粘连被整段丢掉 |

后两个不容易发现，因为分节词数看着差不多对，实际整节并进了上一节。

现在是固定预处理链：

```
strip_preamble → strip_comments → strip_floats → clean_tex → drop_heading_lines
```

也修了三处判定误报：`guarantee` 的名词用法（`not a guarantee of global optimality`）被当成越界声明；有定理环境时 `prove` 仍报高危；`To validate the effectiveness of X` 后面两句就跟着具体数字，却判成空承诺（现在看同段有没有数字）。

写这份 README 时又撞上两个同类问题：Markdown 表格的分隔线 `|---|` 和列表项的 `- ` 被算成破折号，把这一项从真实的 13/千词抬到 48/千词；另一个只在代码块里引用 `\section` 的文档被当成 LaTeX 解析，连带触发前一个 bug。

`tests/run_cases.py` 把这些固定成 11 条回归用例，5 条是上面的 LaTeX 不变量，2 条是 Markdown 结构。动阈值之前先跑这个。

## 已知局限

- 中文的词性比例、四字格密度要分词。脚本故意不装 jieba，免得污染环境，留给人工判断，扩展方法写在 `metrics.md`。
- 阈值按论文体和中文技术写作标定，换体裁得重新标定。
- 破折号、句长这类指标还在代际漂移，词表需要定期更新。结构层和证据层的判据相对稳。

## 文件

```
SKILL.md                      主规范：四轴、四态、四手术、改写流水线
references/paper-sections.md  分节作战手册（Abstract/Intro/Method/Exp/Related/Rebuttal）
references/tells-en.md        英文论文体痕迹清单 + 动词阶梯
references/tells-zh.md        中文 AI 味特征（含语料对比参考值）
references/defensive.md       防御性写作判定与改写
references/metrics.md         指标定义、阈值性质、脚本覆盖范围与已知局限
scripts/prose_scan.py         零依赖体检脚本
tests/run_cases.py            回归用例
```

## License

MIT
