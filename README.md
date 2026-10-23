# paper-prose-calibration

一个面向**英文论文写作**的「去 AI 味」技能（WorkBuddy / Claude skill），附带一个零依赖的体检脚本。

不是换同义词。是先在句子层面标出哪句在承载信息、哪句在空转，再决定删、换、并拆还是补。纯样式改写会被拒交付——那样只是把问题藏得更深。

A skill that removes AI-writing tells from academic prose. It classifies every sentence as load-bearing / needs-evidence / vague-reference / filler before rewriting, and refuses pure style edits.

---

## 为什么不是又一份「AI 词表」

现存的 AI 味清单有三个问题，这个技能是按修这三个问题设计的：

**1. 词表按模型代际漂移。** `delve` 是 GPT-4 时代的标志，2025 年已经消失；GPT-5 期换成 `emphasizing` / `highlight`；再往后是 `practical` / `steady` / `quietly` 这类看起来无害的词。一份固定的词表半年就过期一半。所以本技能把词表当**版本化快照**用，真正的判据放在结构层和证据层。

**2. 表层修完会制造新痕迹。** 破折号从 GPT-5.1 起被硬性压制，2026 年的语料里 ChatGPT 用破折号比专业作家还少。结果是标点只剩逗号句号、句长挤在 8–20 词——这成了比破折号更强的指纹。「删光破折号去味」正是这条因果链的产物。脚本会专门检查 `8–20 词带占比 > 80%`。

**3. 把迹象当待修问题，只会让检测更难，文本不会更好。** 真问题是没来源、过度概括、无据断言。所以技能的核心不是改写，是**逐句定级 + 补证据或砍范围**，并有一条硬护栏：至少一处必须是信息补强或范围校准。

## 四根轴

| 轴 | 查什么 | 典型病 |
|---|---|---|
| A 信息密度 | 每句是否推进 | 「随着……的发展」开篇、三段式总—分—总、挑战与展望段 |
| B 姿态校准 | 断言强度 vs 证据等级，**两个方向都调** | 欠断言：`might possibly suggest`；过断言：单种子写 `prove`、`significantly` 无检验 |
| C 形式 | 结构·句法·标点·词表 | 连接词起句、三项并列、否定平行、`-ing` 解释尾巴、copula 回避 |
| D 可溯性 | claim 能否指到 Table / Figure / § / 定理 | `extensive experiments demonstrate the effectiveness`、贡献条目指不到节表 |

D 轴是论文体独有的，通用的 AI 味清单完全不管，但它是审稿人扣分最狠的一维。

轴 B 里有个容易漏的**反向**问题：连续自我限缩。单看每句都诚实，连读的效果是先替审稿人否定了稿子。技能里区分了「限定条件」（`At α=0.01 the gain disappears` 是信息，要留）和「自我贬低」（`the main claim remains narrow`，要删）。

## 安装

```bash
git clone https://github.com/CyberStaZJU/paper-prose-calibration.git \
  ~/.workbuddy/skills/prose-calibration
```

Claude Code 用户把目标路径换成 `~/.claude/skills/prose-calibration` 即可。目录名保持 `prose-calibration`，与 `SKILL.md` 里的自引用一致。

触发方式：直接说「帮我把这段改得像人写的」「这段太 AI 了」「审一下我论文的摘要」，或手动 `/prose-calibration`。

## 用法

```bash
# 体检（不修改文件）
python3 scripts/prose_scan.py --file paper.tex --paper

# JSON 输出，便于接 CI
python3 scripts/prose_scan.py --file paper.tex --paper --json

# 中文文本
python3 scripts/prose_scan.py --file draft.md
```

`--paper` 追加论文专用指标：数字密度、8–20 词带占比、评价性形容词密度、动词阶梯分布、空承诺句式、虚指归因、hedge 堆叠、名词化密度、`significantly` 与检验的配对、claim 锚点数、分节词数、摘要专项。

零依赖，只要 Python 3.8+。不写文件，不改你的稿子。

## 脚本能算的与算不出的

**能算**：句长分布与变异系数、标点类别数、词表命中、数字密度、动词分层、空承诺、虚指归因、锚点数。

**算不出**：语义空转、虚构引用、因果越界、论证是否成立。`references/metrics.md` 列了 9 项「必须人工」的清单，并明确写了阈值是启发式、没有文献依据支撑为普适判据。

一个具体的边界案例：脚本分不清「引号内举反例」和「真实使用」。改写稿里残留的 1 处 `显著提升` 是作为反例被引用的，脚本仍会报。

## 在真实 LaTeX 上踩过的坑

这份技能的价值有一半来自**拿真实投稿跑过**。第一版直接在 `.tex` 源码上统计，数字全错：

| 指标 | 错的值 | 真实值 | 原因 |
|---|---|---|---|
| 极短句占比 | 43% | 1% | 表格行被当成了句子 |
| 数字密度 | 7.0/百词 | 2.6/百词 | 表格里的准确率被当成「证据」 |
| 破折号 | 24.2/千词 | 1.1/千词 | `%---------` 注释分隔线被算成破折号 |
| Method 节词数 | 整节消失 | 2380 词 | `\section{Method: \method{}}` 嵌套花括号导致正则失配 |
| 正文字数 | 9485 | 7181 | 每节首段因标题粘连被整段丢弃 |

后两个最隐蔽——分节词数看起来「差不多对」，实际上整节被并进了上一节。不拿真稿跑，这几个错误永远发现不了。

现在是固定的预处理链：

```
strip_preamble → strip_comments → strip_floats → clean_tex → drop_heading_lines
```

另外修了三处判定误报：`guarantee` 的名词用法（`not a guarantee of global optimality`）被当成越界声明；有定理环境时 `prove` 仍报高危；`To validate the effectiveness of X` 后面两句就跟着具体数字，却被判成空承诺（现在按同段是否有数字判定）。

`tests/run_cases.py` 把这些固定成 9 条回归用例，其中 5 条是上述 LaTeX 不变量。改阈值前先跑这个。

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

## 已知局限

- 中文的词性比例、四字格密度需要分词，脚本故意不装 jieba（避免污染环境），留给人工判断，扩展方法写在 `metrics.md`。
- 阈值是按论文体和中文技术写作标定的，换体裁（新闻、营销文案）需要重新标定。
- 破折号、句长这类指标处在代际漂移中，词表需要定期更新；结构层和证据层判据相对稳定。

## License

MIT
