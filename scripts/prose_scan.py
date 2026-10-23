#!/usr/bin/env python3
"""Prose scan: dependency-free surface metrics for AI-tell diagnosis.

Usage:
    python3 prose_scan.py --file draft.tex --paper
    python3 prose_scan.py --file draft.md
    python3 prose_scan.py --text "..."
    cat draft.md | python3 prose_scan.py
    python3 prose_scan.py --file draft.tex --paper --json

--paper adds paper-specific metrics: number density, claim-verb tiers,
adjective inflation, hedge stacking, nominalisation, 'significantly' vs
statistical support, section word counts, abstract checks.

The script measures surfaces. It cannot detect fabricated citations,
causal overreach, or semantically empty sentences. Those require reading.
Thresholds are triage heuristics, not literature-derived cut-offs.
"""

import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter

# --- word lists -------------------------------------------------------------
# Dated 2026-10. Refresh against references/tells-*.md. Density matters, not
# single hits. Lists stay short on purpose: long lists buy false positives.

ZH_MARKERS = [
    "值得注意的是", "需要指出的是", "需要强调的是", "众所周知", "毋庸置疑",
    "综上所述", "总而言之", "总的来说", "归根结底", "简而言之", "换句话说",
    "总体而言", "由此可见", "正因如此", "与此同时", "不仅如此", "更重要的是",
    "具有重要意义", "发挥关键作用", "发挥重要作用", "至关重要", "不可或缺",
    "广阔的应用前景", "显著提升", "有效解决", "充分体现", "深刻反映",
    "标志着", "彰显", "折射出", "赋能", "助力", "护航", "闭环", "抓手",
    "底层逻辑", "护城河", "多维度", "深层次", "系统性", "协同性", "颗粒度",
    "在当今", "随着", "近年来", "当前", "当下",
    "仅仅是初步", "有限参考", "很大的提升空间", "不足之处", "抛砖引玉",
    "本文并不", "本文无意", "不意味着", "不应被理解",
]

ZH_CONNECTIVES = [
    "此外", "然而", "因此", "但是", "同时", "另外", "首先", "其次", "再次",
    "最后", "总之", "综上", "而且", "并且", "所以", "不过", "另一方面",
    "也就是说", "换言之", "与此同时", "由此可见", "值得注意的是",
]

EN_MARKERS = [
    "delve", "tapestry", "testament", "pivotal", "underscore", "intricate",
    "intricacies", "interplay", "vibrant", "meticulous", "garner", "bolster",
    "showcase", "landscape", "realm", "crucial", "robust", "leverage",
    "seamless", "holistic", "multifaceted", "paradigm", "nuanced",
    "moreover", "furthermore", "additionally", "it is worth noting",
    "it is important to note", "in conclusion", "in summary", "novel",
]

EN_CONNECTIVES = [
    "however", "moreover", "furthermore", "additionally", "therefore",
    "thus", "consequently", "meanwhile", "nevertheless", "in addition",
    "as a result", "in conclusion", "first", "second", "finally",
]

EN_HEDGES = [
    "may", "might", "could", "possibly", "potentially", "arguably",
    "seemingly", "apparently", "somewhat", "relatively", "fairly",
    "it seems", "suggests", "tends to", "to some extent", "appears to",
]

EN_COPULA_AVOID = [
    "serves as", "stands as", "functions as", "operates as", "marks a",
    "represents a", "boasts", "features a", "offers a",
]

# Paper-mode lists -----------------------------------------------------------

# Evaluative adjectives that substitute for numbers. High density is the
# single most common prose failure in ML papers.
PAPER_ADJ = [
    "novel", "significant", "significantly", "substantial", "substantially",
    "remarkable", "remarkably", "superior", "superiority", "comprehensive",
    "extensive", "effective", "effectiveness", "efficient", "efficiency",
    "robust", "robustness", "promising", "state-of-the-art", "dramatic",
    "drastic", "considerable", "notable", "unprecedented", "seamless",
    "powerful", "outstanding",
]

# Claim verbs by evidence tier. Used to spot over-claiming, not to grade.
CLAIM_TIERS = {
    "prove_guarantee": ["prove", "proves", "proved", "proven",
                        "validate", "validates", "validated",
                        "establish", "establishes", "certify"],
    "show_demonstrate": ["show", "shows", "showed", "shown", "demonstrate",
                         "demonstrates", "demonstrated"],
    "improve_observe": ["improve", "improves", "improved", "reduce", "reduces",
                        "reduced", "observe", "observes", "observed",
                        "achieve", "achieves", "achieved", "reach", "reaches"],
    "suggest_may": ["suggest", "suggests", "suggested", "indicate", "indicates",
                    "appears", "seems", "hint", "hints"],
}

# "guarantee" is a claim verb only in these frames; elsewhere it is the noun.
GUARANTEE_CLAIM = re.compile(
    r"\bguarantee[sd]?\s+(?:that|convergence|robustness|accuracy|correctness|"
    r"stability|generalization|performance)\b", re.I)

# Phrases that promise without informing. Each is a deletion candidate.
EMPTY_CLAIM_PATTERNS = [
    r"extensive experiments",
    r"comprehensive experiments",
    r"demonstrate the (effectiveness|superiority|advantage)",
    r"validates? the (effectiveness|superiority|importance)",
    r"outperforms? (the )?state[- ]of[- ]the[- ]art",
    r"simple yet effective",
    r"to this end",
    r"novel framework",
    r"open(s)? new (directions|avenues)",
    r"results are promising",
    r"has attracted (increasing|much|widespread) attention",
    r"in recent years",
    r"with the rapid development",
    r"plays? an? (important|crucial|key|vital) role",
    r"to the best of our knowledge",
    r"the future looks bright",
]

VAGUE_ATTRIBUTION = [
    r"recent (studies|work|research) (have|has|show|shows)",
    r"most existing (methods|approaches|works)",
    r"prior (work|methods|approaches) (ignore|overlook|lack)",
    r"it is widely (accepted|known|believed|recognized)",
    r"researchers have (shown|found|proposed)",
    r"many (studies|works|methods)",
    r"existing methods (still )?(have|suffer from|face) (limitations|challenges)",
]

# Markers that can support the word "significantly".
STAT_MARKERS = [
    r"p\s*[<>=]\s*0?\.\d+", r"p-value", r"±", r"\\pm", r"std",
    r"standard deviation", r"confidence interval", r"\bCI\b",
    r"\bseeds?\b", r"\bruns?\b", r"\d+\s*(random )?(seeds|runs|repetitions)",
    r"t-test", r"wilcoxon",
]

ZH_PARTICLES = "啊呢吧吗嘛呀哦哈"
ZH_PRONOUNS = ["我们", "我", "你", "你们", "咱们", "自己"]

PUNCT_GROUPS = {
    "逗号": "，,", "句号": "。.", "顿号": "、", "分号": "；;", "冒号": "：:",
    "问号": "？?", "叹号": "！!", "破折号": "—–", "省略号": "…",
    "括号": "（）()", "引号": "“”\"'‘’",
}

# Numbers that are pointers, not evidence.
POINTER_WORDS = (r"(table|tab\.|figure|fig\.|section|sec\.|§|eq\.?|equation|"
                 r"algorithm|theorem|lemma|appendix|step|line)")


# --- helpers ----------------------------------------------------------------

def detect_lang(text):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if cjk == 0:
        return "en"
    if latin == 0:
        return "zh"
    return "zh" if cjk >= latin * 2 else "en"


HEADING_ANY = re.compile(
    r"(?m)^[ \t]*(?:\\(section|subsection|subsubsection|paragraph)\*?[ \t]*\{|\#{1,6}[ \t]+)")


def _headings_to_md(text):
    """Turn every heading level into a #-line so prose stats skip it."""
    out, last = [], 0
    for m in HEADING_ANY.finditer(text):
        if m.group(0).lstrip().startswith("#"):
            continue
        title, after = _match_brace(text, m.end() - 1)
        out.append(text[last:m.start()])
        out.append("\n### " + _clean_heading(title) + "\n")
        last = after
    out.append(text[last:])
    return "".join(out)


def drop_heading_lines(text):
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def strip_comments(text):
    """Drop LaTeX comments; %----- separators were being read as em dashes."""
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


def strip_preamble(text):
    m = re.search(r"\\begin\{document\}", text)
    if m:
        text = text[m.end():]
    i = text.find("\\end{document}")
    return text[:i] if i >= 0 else text


def clean_tex(text):
    """Drop LaTeX scaffolding so word counts reflect prose."""
    t = re.sub(r"\\(cite|citep|citet|ref|eqref|autoref|label)\*?(\[[^\]]*\])?\{[^{}]*\}", " ", text)
    t = re.sub(r"\\begin\{(?:theorem|lemma|corollary|proposition|definition|"
               r"assumption|remark)\}\s*\[[^\]]*\]", " ", t)
    t = re.sub(r"\\(begin|end)\{[^{}]*\}", " ", t)
    t = _headings_to_md(t)
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    return re.sub(r"[{}]", " ", t)


def split_paragraphs(text):
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


ABBREV = re.compile(
    r"\b(e\.g|i\.e|cf|vs|resp|approx|Eq|Eqs|Fig|Figs|Sec|Secs|Tab|Alg|"
    r"Thm|Lem|Cor|Def|Assum|Prop|No|Ref|Ch|Vol|pp|al)\.", re.I)


def split_sentences(para, lang):
    if lang == "zh":
        pieces = re.split(r"(?<=[。！？…；])", para)
    else:
        # Protect abbreviations so "e.g." / "Eq." do not split a sentence.
        guarded = ABBREV.sub(lambda m: m.group(1) + "\x00", para)
        pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"'(\[])", guarded)
        if len(pieces) == 1:
            pieces = re.split(r"(?<=[.!?])", guarded)
        pieces = [p.replace("\x00", ".") for p in pieces]
    # A sentence must contain at least one letter; drop table/row debris.
    return [p.strip() for p in pieces
            if p.strip() and re.search(r"[A-Za-z\u4e00-\u9fff]", p)]


def sentence_len(s, lang):
    if lang == "zh":
        return len(re.sub(r"\s", "", s))
    return len(re.findall(r"[A-Za-z0-9']+", s))


def count_all(text, patterns):
    hits = Counter()
    for p in patterns:
        if re.search(r"[\u4e00-\u9fff]", p):
            n = text.count(p)
        else:
            n = len(re.findall(r"\b" + re.escape(p) + r"\b", text, re.I))
        if n:
            hits[p] = n
    return hits


def ngram_repeat_rate(text, n, lang):
    if lang == "zh":
        seq = re.sub(r"[\s\W]+", "", text)
        grams = [seq[i:i + n] for i in range(len(seq) - n + 1)]
    else:
        words = re.findall(r"[a-z0-9']+", text.lower())
        grams = [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
    if len(grams) < 20:
        return 0.0, 0
    c = Counter(grams)
    dup = sum(v - 1 for v in c.values() if v > 1)
    return dup / len(grams), len(grams)


def entropy(counts):
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = 0.0
    for v in counts:
        if v:
            p = v / total
            h -= p * math.log2(p)
    return h


def data_numbers(text):
    """Numeric tokens carrying evidence, excluding table/section pointers."""
    out = []
    for m in re.finditer(r"\d+(?:\.\d+)?\s*(?:%|x|×|ms|s\b|pp|points?)?", text):
        pre = text[max(0, m.start() - 14):m.start()].lower()
        if re.search(POINTER_WORDS, pre):
            continue
        out.append(m.group(0).strip())
    return out


def has_stat_marker(s):
    return any(re.search(p, s, re.I) for p in STAT_MARKERS)


# --- paper metrics ----------------------------------------------------------

SECTION_HEAD = re.compile(r"(?m)^[ \t]*(?:\\section\*?[ \t]*\{|\#{2,}[ \t]+)")

FLOAT_ENVS = ("table*", "table", "tabular*", "tabular", "figure*", "figure",
              "algorithm*", "algorithm", "algorithmic*", "algorithmic",
              "equation*", "equation", "align*", "align", "eqnarray*",
              "eqnarray", "gather*", "gather", "cases", "aligned", "split")

THEOREM_ENVS = ("theorem", "lemma", "corollary", "proposition")


def _match_brace(text, i):
    """Return (content, index_after) for a balanced group at text[i]=='{'."""
    start, depth, n = i, 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return text[start + 1:], n


def _clean_heading(t):
    t = re.sub(r"\\texorpdfstring\{([^{}]*)\}\{[^{}]*\}", r"\1", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\{[^{}]*\})?", "", t)
    t = re.sub(r"[${}\\]", "", t)
    return re.sub(r"\s+", " ", t).strip().strip(":").strip()


def strip_floats(text):
    """Remove tables/figures/algorithms/display math: they are data, not prose."""
    for env in FLOAT_ENVS:
        e = re.escape(env)
        text = re.sub(r"\\begin\{%s\}.*?\\end\{%s\}" % (e, e), " ", text, flags=re.S)
    return text


def split_sections(text):
    """Return {normalised heading: body}. Handles nested macros in titles."""
    marks = []
    for m in SECTION_HEAD.finditer(text):
        tail = m.group(0).lstrip()
        if tail.startswith("#"):
            eol = text.find("\n", m.end())
            eol = len(text) if eol < 0 else eol
            marks.append((m.start(), text[m.end():eol].strip(), eol))
        else:
            title, after = _match_brace(text, m.end() - 1)
            marks.append((m.start(), title, after))
    out = {}
    for i, (pos, name, after) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        key = _clean_heading(name).lower()
        if key:
            out[key] = text[after:end]
    return out


def abstract_text(raw):
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.S)
    if m:
        return m.group(1)
    for k, v in split_sections(raw).items():
        if "abstract" in k:
            return v
    return ""


def paper_metrics(raw, cleaned):
    low = cleaned.lower()
    words = len(re.findall(r"[A-Za-z0-9']+", cleaned))
    per100 = lambda n: round(n * 100.0 / words, 2) if words else 0.0

    nums = data_numbers(cleaned)
    adjs = count_all(cleaned, PAPER_ADJ)
    adj_total = sum(adjs.values())
    tiers = {k: sum(count_all(cleaned, v).values()) for k, v in CLAIM_TIERS.items()}
    # "a/the/no ... guarantee" is a limitation statement, not an over-claim.
    guarantee_all = len(re.findall(r"\bguarantee[sd]?\b", cleaned, re.I))
    guarantee_verb = len(GUARANTEE_CLAIM.findall(cleaned))
    tiers["prove_guarantee"] += guarantee_verb
    vague = Counter()
    for p in VAGUE_ATTRIBUTION:
        n = len(re.findall(p, low))
        if n:
            vague[p] = n

    sents = []
    for para in split_paragraphs(cleaned):
        if para.lstrip().startswith("#"):
            continue
        sents.extend(split_sentences(para, "en"))

    hedge_words = set(EN_HEDGES)
    hedge_hits, hedge_stack = 0, []
    for s in sents:
        hs = [w for w in hedge_words if re.search(r"\b" + re.escape(w) + r"\b", s, re.I)]
        hedge_hits += len(hs)
        if len(hs) >= 2:
            hedge_stack.append(s[:110])

    sig_total, sig_unpaired = 0, []
    for i, s in enumerate(sents):
        if re.search(r"\bsignificant(ly)?\b", s, re.I):
            sig_total += 1
            window = " ".join(sents[max(0, i - 1):i + 2])
            if not has_stat_marker(window):
                sig_unpaired.append(s[:110])

    # An "empty claim" is only empty if its own paragraph carries no data.
    paras_txt = [p for p in split_paragraphs(cleaned)
                 if not p.lstrip().startswith("#")]
    empty = Counter()
    for pat in EMPTY_CLAIM_PATTERNS:
        unsupported = 0
        for para in paras_txt:
            hits = len(re.findall(pat, para, re.I))
            if hits and not data_numbers(para):
                unsupported += hits
        if unsupported:
            empty[pat] = unsupported

    theorem_envs = sum(
        len(re.findall(r"\\begin\{%s\*?\}" % e, raw)) for e in THEOREM_ENVS)

    nominal = len(re.findall(
        r"\b\w+(?:tion|sions?|ments?|ance|ence|ity|ness|ization)\b", low))

    sec_words = {k: len(re.findall(r"[A-Za-z0-9']+", clean_tex(v)))
                 for k, v in split_sections(raw).items()}

    ab = clean_tex(abstract_text(raw))
    ab_words = len(re.findall(r"[A-Za-z0-9']+", ab))
    ab_nums = data_numbers(ab)
    ab_bad_open = bool(re.search(
        r"(in recent years|has attracted|with the rapid development|recently,)", ab, re.I))

    anchors = len(re.findall(
        r"(?:table|tab\.|figure|fig\.)\s*~?\s*\d+"
        r"|(?:table|figure|section|appendix)\s*~?\s*\\?[a-z]*\{?[\w:.-]*"
        r"|\\(?:ref|autoref|cref|Cref)\{|§\s*\d", raw, re.I))

    band = [x for x in (sentence_len(s, "en") for s in sents)]
    band_ratio = round(sum(1 for x in band if 8 <= x <= 20) / len(band), 2) if band else 0.0

    return {
        "words": words,
        "band_8_20": band_ratio,
        "numbers": len(nums),
        "number_density_per100": per100(len(nums)),
        "adjectives": {"total": adj_total, "per100": per100(adj_total),
                        "top": adjs.most_common(8)},
        "claim_tiers": tiers,
        "guarantee": {"all": guarantee_all, "verb": guarantee_verb,
                      "noun": max(0, guarantee_all - guarantee_verb)},
        "theorem_envs": theorem_envs,
        "empty_claims": {"total": sum(empty.values()), "patterns": empty.most_common(8)},
        "vague_attribution": {"total": sum(vague.values()),
                               "patterns": vague.most_common(6)},
        "hedges": {"total": hedge_hits,
                    "per1000": round(hedge_hits * 1000.0 / words, 1) if words else 0.0,
                    "stacked": hedge_stack[:5]},
        "nominalisation": {"count": nominal, "per100": per100(nominal)},
        "significantly": {"total": sig_total, "unpaired": sig_unpaired[:5],
                           "unpaired_count": len(sig_unpaired)},
        "we_propose": len(re.findall(r"\bwe (propose|present|introduce|develop)\b", low)),
        "anchors": anchors,
        "sections": dict(sorted(sec_words.items(), key=lambda kv: -kv[1])[:8]),
        "abstract": {"words": ab_words, "numbers": len(ab_nums),
                      "bad_opening": ab_bad_open},
    }


def paper_flags(p):
    f = []
    a = p["abstract"]
    if a["words"]:
        if a["words"] > 250:
            f.append(("中", f"摘要 {a['words']} 词", "超过 250 词基本是引言压缩版，删背景"))
        if a["numbers"] < 3:
            f.append(("高", f"摘要只有 {a['numbers']} 个数字",
                      "少于 3 个说明结论强度未量化；先定结论再改文"))
        if a["bad_opening"]:
            f.append(("高", "摘要以领域背景开头",
                      "改为具体缺口；'in recent years' 类开头零信息"))
    if p["significantly"]["unpaired_count"]:
        f.append(("高", f"significantly 无检验支撑 {p['significantly']['unpaired_count']} 处",
                  "没有 ±/seeds/p 值就不能用，改写为 improves/reduces"))
    thm = p.get("theorem_envs", 0)
    n_claim = p["claim_tiers"]["prove_guarantee"]
    if n_claim and thm:
        f.append(("低", f"claim 动词 {n_claim} 次，文中有 {thm} 个定理类环境",
                  "形式化结果支撑时属正常；只需逐处核对 prove 指向具体定理编号"))
    elif n_claim:
        f.append(("高", f"prove/validate/guarantee 出现 {n_claim} 次，但全文无定理环境",
                  "只有实验结论时必须降级为 show/suggest"))
    if p["adjectives"]["per100"] > 3:
        f.append(("高", f"评价性形容词 {p['adjectives']['total']} 个（{p['adjectives']['per100']}/百词）",
                  "每个都需邻句有数字，否则删"))
    elif p["adjectives"]["per100"] > 1.5:
        f.append(("中", f"评价性形容词 {p['adjectives']['total']} 个（{p['adjectives']['per100']}/百词）",
                  "逐个查邻句是否有数字"))
    if p["empty_claims"]["total"]:
        f.append(("中", f"空承诺句式 {p['empty_claims']['total']} 处",
                  "；".join(k for k, _ in p["empty_claims"]["patterns"][:3])))
    if p["vague_attribution"]["total"]:
        f.append(("中", f"虚指归因 {p['vague_attribution']['total']} 处",
                  "能写出具体文献+年份吗？写不出就是虚指"))
    if p["hedges"]["stacked"]:
        f.append(("中", f"同一句内 hedge 堆叠 {len(p['hedges']['stacked'])} 句",
                  "合并为一个情态词，把不确定性锚到具体条件"))
    if p["words"] > 400 and p["number_density_per100"] < 1.0:
        f.append(("中", f"数字密度 {p['number_density_per100']}/百词",
                  "论文正文数字过少，检查结果陈述是否只有形容词"))
    if p["nominalisation"]["per100"] > 8:
        f.append(("低", f"名词化密度 {p['nominalisation']['per100']}/百词",
                  "动词还原（the improvement of -> improves）"))
    if p["we_propose"] > 2:
        f.append(("低", f"'we propose' 类 {p['we_propose']} 次", "留 1–2 次即可"))
    if p["band_8_20"] > 0.8 and p["words"] > 300:
        f.append(("中", f"句长集中在 8–20 词带 ({p['band_8_20']:.0%})",
                  "2026 年后新模型被压制破折号后的典型节奏；用长句承载限定、短句承载结论"))
    if p["words"] > 800 and p["anchors"] < 3:
        f.append(("中", f"claim 锚点仅 {p['anchors']} 处",
                  "长文应有多个 Table/Fig/§ 指针；锚不上说明 claim 无证据位置"))
    return f


# --- main scan --------------------------------------------------------------

def scan(text, paper_mode=False):
    lang = detect_lang(text)
    raw = text
    is_tex = bool(re.search(r"\\begin\{|\\section", raw))
    body = strip_comments(strip_preamble(raw)) if is_tex else raw
    body = strip_floats(body) if is_tex else body
    cleaned = clean_tex(body) if lang == "en" else body
    if is_tex:
        cleaned = drop_heading_lines(cleaned)
    chars = len(re.sub(r"\s", "", cleaned))
    words = len(re.findall(r"[A-Za-z0-9']+", cleaned))
    units = chars if lang == "zh" else words

    paras = [p for p in split_paragraphs(cleaned)
             if not p.lstrip().startswith("#")]
    sents = []
    for p in paras:
        sents.extend(split_sentences(p, lang))
    # Display-math removal leaves fragments ("Then", "and"). They are not
    # sentences, so they must not skew the length distribution.
    min_len = 1 if lang == "zh" else 4
    frags = [s for s in sents if sentence_len(s, lang) < min_len]
    sents = [s for s in sents if sentence_len(s, lang) >= min_len]
    lens = [sentence_len(s, lang) for s in sents] or [0]

    mean = statistics.fmean(lens)
    std = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    cv = (std / mean) if mean else 0.0
    short_cut = 8 if lang == "zh" else 5
    long_cut = 80 if lang == "zh" else 35

    pcounts = {name: sum(cleaned.count(c) for c in cs) for name, cs in PUNCT_GROUPS.items()}
    # Spaced hyphens (" - ") and LaTeX "--" are em-dash substitutes.
    pcounts["破折号"] += len(re.findall(r"\s--\s|\s-\s", cleaned))
    if is_tex:
        pcounts["破折号"] += len(re.findall(r"---|(?<=\w)--(?=\w)", cleaned))
    ptotal = sum(pcounts.values())
    p_used = sum(1 for v in pcounts.values() if v)
    p_entropy = entropy(list(pcounts.values()))
    per_k = lambda n: round(n * 1000.0 / units, 2) if units else 0.0

    markers = count_all(cleaned, ZH_MARKERS if lang == "zh" else EN_MARKERS)
    conns = ZH_CONNECTIVES if lang == "zh" else EN_CONNECTIVES
    conn_start = 0
    for s in sents:
        head = s[:12].lower() if lang == "en" else s[:8]
        if any(head.startswith(c) for c in conns):
            conn_start += 1
    conn_ratio = conn_start / len(sents) if sents else 0.0

    md = {
        "bold": len(re.findall(r"\*\*[^*]+\*\*", text)),
        "heading": len(re.findall(r"(?m)^#{1,6}\s", text)),
        "bullet": len(re.findall(r"(?m)^\s*[-*+]\s", text)),
        "numbered": len(re.findall(r"(?m)^\s*\d+[.)]\s", text)),
        "inline_code": len(re.findall(r"`[^`]+`", text)),
    }

    rep_rate, gram_n = ngram_repeat_rate(cleaned, 5 if lang == "zh" else 4, lang)

    extra = {}
    if lang == "zh":
        extra["语气词"] = sum(text.count(c) for c in ZH_PARTICLES)
        extra["第一/第二人称"] = sum(text.count(p) for p in ZH_PRONOUNS)
        extra["三项并列"] = len(re.findall(r"[^，。；]{2,}、[^，。；]{2,}、[^，。；]{2,}", text))
        extra["否定平行"] = len(re.findall(r"不是.{1,20}?而是", text))
        extra["伪列表"] = len(re.findall(r"第[一二三四五]个(原因|方面|问题|层次)", text))
    else:
        extra["hedge"] = sum(count_all(cleaned, EN_HEDGES).values())
        extra["copula回避"] = sum(count_all(cleaned, EN_COPULA_AVOID).values())
        extra["否定平行"] = len(re.findall(r"\bnot (just|only|merely)\b.{0,60}?\bbut\b",
                                           cleaned, re.I))
        extra["三连修饰"] = len(re.findall(r"\b\w+ly,\s+\w+ly,?\s+and\s+\w+ly\b", cleaned, re.I))
        extra["-ing 尾巴"] = len(re.findall(
            r",\s+\w+ing\s+(the|its|a|an|this|these|how)\b", cleaned, re.I))

    para_lens = [len(re.sub(r"\s", "", p)) for p in paras] or [0]
    p_cv = (statistics.pstdev(para_lens) / statistics.fmean(para_lens)) \
        if len(para_lens) > 1 and statistics.fmean(para_lens) else 0.0

    paper_on = bool(paper_mode) or (lang == "en" and bool(re.search(r"\\section|(?m)^##\s", text)))
    cv_hi, cv_mid = (0.20, 0.26) if paper_on else (0.30, 0.40)

    flags = []
    if len(lens) >= 8:
        if cv < cv_hi:
            flags.append(("高", f"句长过于齐整 (CV={cv:.2f})", "长短句被抹平，是最稳的机器节奏特征"))
        elif cv < cv_mid:
            flags.append(("中", f"句长偏齐整 (CV={cv:.2f})", "检查是否存在连续同构段"))
    punct_floor = 4 if lang == "zh" else 3
    if ptotal > 8 and p_used < punct_floor:
        flags.append(("中", f"标点只用了 {p_used} 类 (H={p_entropy:.2f})",
                      "标点种类单调，常见于过度压制破折号后的输出"))
    mk_per_k = (sum(markers.values()) * 1000.0 / units) if units else 0
    if mk_per_k > 8:
        flags.append(("高", f"AI 词表密度 {mk_per_k:.1f}/千单位",
                      f"命中 {sum(markers.values())} 次；词表随代际漂移，需人工确认语境"))
    elif mk_per_k > 4:
        flags.append(("中", f"AI 词表密度 {mk_per_k:.1f}/千单位", "密度偏高，逐条查是否可用更具体说法"))
    if conn_ratio > 0.30:
        flags.append(("中", f"连接词起句率 {conn_ratio:.0%}", "中文段落关系多数靠语义衔接，不靠连接词缝合"))
    md_total = md["bold"] * 2 + md["heading"] + md["bullet"] + md["numbered"]
    if md_total > 12:
        flags.append(("中", f"Markdown 脚手架 {md_total}", "粗体、小标题、列表堆叠；正文类文本应改为散文"))
    if rep_rate > 0.02:
        flags.append(("中", f"重复 n-gram 占比 {rep_rate:.1%}", "同一说法被反复复述，检查是否为单点稀释"))
    if lang == "zh" and chars > 400 and extra["语气词"] == 0:
        flags.append(("低", "语气词为 0", "书面文本正常；汇报与科普类会显得冰冷"))
    if lang == "en" and words and extra["hedge"] * 1000.0 / words > 25:
        flags.append(("中", f"hedge 密度 {extra['hedge']*1000.0/words:.1f}/千词",
                      "情态词堆叠，检查是否可用具体条件替代"))
    if lang == "en" and extra["copula回避"] >= 3:
        flags.append(("中", f"copula 回避 {extra['copula回避']} 处",
                      "serves as / represents / boasts 替代 is/has，是稳定的英文指纹"))
    if p_cv < 0.25 and len(paras) >= 5:
        flags.append(("低", f"段落长度齐整 (CV={p_cv:.2f})", "每段体量接近，是'总分总'模板的副产品"))

    result = {
        "lang": lang,
        "chars": chars,
        "words": words,
        "unit_count": units,
        "units": "字" if lang == "zh" else "词",
        "sentences": len(sents),
        "paragraphs": len(paras),
        "sentence_len": {
            "mean": round(mean, 1), "std": round(std, 1), "cv": round(cv, 2),
            "min": min(lens), "max": max(lens),
            "short_ratio": round(sum(1 for x in lens if x < short_cut) / len(lens), 2),
            "long_ratio": round(sum(1 for x in lens if x > long_cut) / len(lens), 2),
        },
        "punctuation": {
            "counts": pcounts, "entropy": round(p_entropy, 2), "categories_used": p_used,
            "em_dash_per_k": per_k(pcounts["破折号"]),
            "semicolon_per_k": per_k(pcounts["分号"]),
            "paren_per_k": per_k(pcounts["括号"]),
            "question_per_k": per_k(pcounts["问号"]),
        },
        "markers": {"total": sum(markers.values()), "per_k": round(mk_per_k, 1),
                     "top": markers.most_common(8)},
        "connectives": {"start_ratio": round(conn_ratio, 2), "count": conn_start},
        "markdown": md,
        "repeat_ngram": {"rate": round(rep_rate, 4), "n": gram_n},
        "paragraph_cv": round(p_cv, 2),
        "extra": extra,
    }

    if paper_mode or (lang == "en" and re.search(r"\\section|(?m)^##\s", text)):
        p = paper_metrics(raw, cleaned)
        result["paper"] = p
        flags.extend(paper_flags(p))

    result["flags"] = [{"level": l, "finding": f, "note": n} for l, f, n in flags]
    return result


def render(r):
    L = []
    u = r["units"]
    L.append(f"语言={r['lang']}  长度={r['unit_count']}{u}"
             + (f"（{r['chars']}字符）" if r["lang"] == "en" else "")
             + f"  句={r['sentences']}  段={r['paragraphs']}")
    s = r["sentence_len"]
    L.append(f"句长({u}) 均值={s['mean']} 标准差={s['std']} CV={s['cv']} "
             f"最短={s['min']} 最长={s['max']} 极短句={s['short_ratio']:.0%} 超长句={s['long_ratio']:.0%}")
    p = r["punctuation"]
    L.append(f"标点={p['categories_used']}类 熵={p['entropy']}  "
             f"破折号/千{u}={p['em_dash_per_k']}  分号={p['semicolon_per_k']}  "
             f"括号={p['paren_per_k']}  问号={p['question_per_k']}")
    m = r["markers"]
    L.append(f"AI词表命中={m['total']} ({m['per_k']}/千{u})  top: "
             + (", ".join(f"{k}×{v}" for k, v in m["top"]) if m["top"]
                else f"AI词表命中=0{'（样本短，密度不稳定）' if r['unit_count'] < 300 else ''}"))
    L.append(f"连接词起句={r['connectives']['count']} ({r['connectives']['start_ratio']:.0%})  "
             f"段落长度CV={r['paragraph_cv']}  重复n-gram={r['repeat_ngram']['rate']:.2%}")
    L.append(f"Markdown: 粗体={r['markdown']['bold']} 标题={r['markdown']['heading']} "
             f"列表={r['markdown']['bullet']}/{r['markdown']['numbered']}")
    if r["extra"]:
        L.append("其他: " + "  ".join(f"{k}={v}" for k, v in r["extra"].items()))

    if "paper" in r:
        q = r["paper"]
        L.append("")
        L.append("— 论文指标 —")
        L.append(f"数字 {q['numbers']} 个 ({q['number_density_per100']}/百词)  "
                 f"评价性形容词 {q['adjectives']['total']} 个 ({q['adjectives']['per100']}/百词)  "
                 f"名词化 {q['nominalisation']['per100']}/百词")
        t = q["claim_tiers"]
        L.append(f"动词阶梯: prove/guarantee={t['prove_guarantee']}  "
                 f"show/demonstrate={t['show_demonstrate']}  "
                 f"improve/observe={t['improve_observe']}  suggest/may={t['suggest_may']}"
                 + (f" ｜ guarantee 名词={q['guarantee']['noun']}/动词={q['guarantee']['verb']}"
                    if q['guarantee']['all'] else ""))
        L.append(f"significantly={q['significantly']['total']}"
                 f"（无检验 {q['significantly']['unpaired_count']}）  "
                 f"空承诺={q['empty_claims']['total']}  虚指={q['vague_attribution']['total']}  "
                 f"hedge={q['hedges']['total']}（堆叠 {len(q['hedges']['stacked'])}）  "
                 f"锚点={q['anchors']}  定理类环境={q['theorem_envs']}")
        a = q["abstract"]
        if a["words"]:
            L.append(f"摘要: {a['words']} 词 / {a['numbers']} 个数字"
                     + ("  ⚠ 以背景开头" if a["bad_opening"] else ""))
        if q["sections"]:
            L.append("分节词数: " + ", ".join(f"{k}={v}" for k, v in q["sections"].items()))
        if q["empty_claims"]["patterns"]:
            L.append("空承诺样例: " + "；".join(f"{k}×{v}" for k, v in q["empty_claims"]["patterns"][:4]))
        if q["significantly"]["unpaired"]:
            L.append("无检验的 significantly: " + " | ".join(q["significantly"]["unpaired"][:2]))

    L.append("")
    if r["flags"]:
        L.append("提示（启发式，不是判定）:")
        for f in r["flags"]:
            L.append(f"  [{f['level']}] {f['finding']} — {f['note']}")
    else:
        L.append("提示: 未触发阈值。这不代表文本没问题；语义空转、虚构来源、无据断言脚本查不出。")
    if r["unit_count"] < 300:
        L.append("样本 <300 单位：千字密度类指标不稳定，只看方向。")
    L.append("本脚本只测量表层。必须人工判断：承重句 / 待补 / 虚指 / 空转。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Surface metrics for AI-tell triage (no deps).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--file", "-f", help="path to text file (.tex/.md/.txt)")
    g.add_argument("--text", "-t", help="text passed inline")
    ap.add_argument("--paper", action="store_true", help="add paper-specific metrics")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("empty input", file=sys.stderr)
        return 2

    r = scan(text, paper_mode=args.paper)
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
