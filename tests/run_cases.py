#!/usr/bin/env python3
"""Regression cases for prose_scan.py.

Each case fixes a text and the signal profile it must produce. Run after any
threshold or regex change:

    python3 tests/run_cases.py

Exit 0 = all pass. Exit 2 = at least one regression.

Cases are deliberately small. They guard against false negatives on obvious
slop and false positives on clean academic prose, in that order of priority.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAN = HERE.parent / "scripts" / "prose_scan.py"

BAD_EN = r"""
\section{Abstract}
In recent years, federated learning has attracted increasing attention due to growing privacy concerns. However, client heterogeneity remains a significant challenge. To this end, we propose a novel framework that addresses this issue comprehensively. Our method is simple yet effective. Extensive experiments on three datasets demonstrate the effectiveness and superiority of our proposed approach. The results are promising and open new directions for future research.

\section{Introduction}
Federated learning has attracted much attention recently. Most existing methods suffer from limitations. Prior work ignores the staleness problem. It is widely accepted that staleness hurts convergence. However, these methods still have limitations. In this paper, we propose a novel framework. We validate the superiority of our design through extensive experiments. Our approach significantly outperforms state-of-the-art methods. We conduct comprehensive experiments on three datasets to demonstrate effectiveness.

\section{Experiments}
We evaluate our method on three datasets. The results show that our method achieves superior performance. Our method significantly improves accuracy over baselines. Ablation studies demonstrate the effectiveness of each component. Our method is robust and efficient. Table 2 reports the results.
"""

GOOD_EN = r"""
\section{Abstract}
Client drift makes federated averaging converge slowly when local updates point in conflicting directions. We bound that drift by capping update staleness at the client, which lets the server keep its aggregation unchanged. The cap is set from the observed update norm, so it needs no per-task tuning. On CIFAR-10 with Dirichlet $\alpha=0.1$, our method reaches 71.4% accuracy in 200 rounds against 66.9% for the strongest staleness-aware baseline, at 1.3$\times$ the wall-clock per round. The gain disappears below $\alpha=0.01$, where fewer than 40 samples per client remain.

\section{Experiments}
We run all methods for 200 communication rounds with 20 clients, 5 local epochs, and report the mean and standard deviation over 3 seeds (Table~\ref{tab:main}). Our method reaches 71.4%$\pm$0.3 against 66.9%$\pm$0.5 for FedAsync, a 4.5-point gap that is larger than the seed variance. Removing the cap raises staleness to 12 rounds and drops accuracy to 67.1%, which is consistent with the drift bound in Section~3.2. At $\alpha=0.01$ both methods fall below 52%, and the gap narrows to 0.8 points; we do not claim an advantage in that regime.
"""

BAD_ZH = """
随着人工智能技术的不断发展，大模型在学术写作中的应用日益广泛。值得注意的是，这一趋势不仅提升了研究效率，也带来了新的挑战。

首先，在当今快速发展的时代背景下，AI写作工具能够有效提升研究者的写作效率。其次，这些工具显著改善了文本的组织结构。最后，它们在一定程度上促进了学术交流的便利性。综上所述，AI写作具有广阔的应用前景。

然而，需要指出的是，AI生成文本在一定程度上可能存在一些问题。值得注意的是，这些问题不仅涉及语言层面，也涉及内容层面。本文并不试图全面解决这些问题，仅仅是初步尝试，只能提供有限参考。

总而言之，AI写作技术的发展具有重要意义。相信在不久的将来，这一技术必将推动学术研究的深刻变革，具有广阔的发展前景。
"""

GOOD_ZH = """
我们先把 buffer 大小固定在 B=4。原因不复杂：上一轮 B=3 的时候，SST2 三个种子的最终准确率分别是 0.939、0.941、0.943，波动在万分之一量级，但 QNLI 掉到 0.795，比基线低 4 个点。B=4 跑 200 轮，QNLI 回到 0.83 附近，代价是单轮延迟从 1.9 s 涨到 2.6 s。

这意味着在 8 卡 NPU 上，一轮 20 个 client 的墙钟时间大约是 5 分钟。如果按 200 轮算，一次完整实验要 17 小时左右——比 B=3 多 3 小时。

我倾向接受这个代价。根因在于 staleness 上限被 buffer 撑大了；把 B 压回 3 用更小的学习率补偿，其实是在用调参掩盖调度问题，后面换任务还得重调一遍。
"""

# (name, text, paper_mode, min_flags, min_high, max_high)
CASES = [
    ("bad-en-paper",   BAD_EN,  True,  8, 4, None),
    ("good-en-paper",  GOOD_EN, True,  0, 0, 0),
    ("bad-zh",         BAD_ZH,  False, 4, 1, None),
    ("good-zh",        GOOD_ZH, False, 0, 0, 0),
]

# Invariants found by running the scanner on real manuscripts (LaTeX, two-column).
# Each asserts one measurement that used to be wrong for a LaTeX source.
NESTED_HEAD = r"""
\section{Method: \method{}}
We introduce the estimator and state when it is exact.

\subsection{Cache refresh}
The cache is refreshed after aggregation.
"""

COMMENT_RULE = r"""
\section{Analysis}
The bound follows from the triangle inequality.

%------------------------------------------------------------------------
%   section separator written as a comment
%------------------------------------------------------------------------

The constant is absorbed into the step size.
"""

TABLE_DIGITS = r"""
\section{Experiments}
We report every configuration in Table 1 and discuss the trend below.

\begin{table}[t]
\caption{Validation accuracy.}
\begin{tabular}{lrr}
\toprule
Method & 51.234 & 62.876 \\
Ours & 71.403 & 66.912 \\
\bottomrule
\end{tabular}
\end{table}

The trend is monotone across the sweep.
"""

THEOREM_CLAIM = r"""
\section{Analysis}
\begin{lemma}[Exact correction]
\label{lem:exact}
Under the stated condition the estimator equals the population gradient.
\end{lemma}

We prove that refill cancels the mixture-weight error in this case.

\begin{theorem}[Convergence]
The iterates converge to a stationary point at the stated rate.
\end{theorem}
"""

NOUN_GUARANTEE = r"""
\section{Scope}
The sketch is a surrogate for direction comparison, not a guarantee of globally
optimal clustering. The bound is a fixed-pair diagnostic rather than a guarantee
for the full procedure. We therefore check clustering stability empirically.
"""

# (name, text, predicate, expectation)
INVARIANTS = [
    ("tex-nested-heading", NESTED_HEAD,
     lambda r: "method" in r["paper"]["sections"],
     "section title containing \\method{} must still be counted"),
    ("tex-comment-rule", COMMENT_RULE,
     lambda r: r["punctuation"]["em_dash_per_k"] == 0.0,
     "%----- comment rules must not count as em dashes"),
    ("tex-table-digits", TABLE_DIGITS,
     lambda r: r["paper"]["numbers"] == 0,
     "digits inside tabular must not count as prose evidence"),
    ("tex-theorem-claim", THEOREM_CLAIM,
     lambda r: not any(f["level"] == "高" for f in r["flags"]),
     "prove next to a lemma/theorem must not raise a high flag"),
    ("tex-noun-guarantee", NOUN_GUARANTEE,
     lambda r: not any(f["level"] == "高" for f in r["flags"]),
     "'not a guarantee of' is a limitation, not an over-claim"),
]



def run(text, paper):
    cmd = [sys.executable, str(SCAN), "--json"]
    if paper:
        cmd.append("--paper")
    p = subprocess.run(cmd, input=text, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)


def main():
    failures = []
    for name, text, paper, min_flags, min_high, max_high in CASES:
        r = run(text, paper)
        flags = r["flags"]
        high = sum(1 for f in flags if f["level"] == "高")
        ok = len(flags) >= min_flags and high >= min_high
        if max_high is not None and high > max_high:
            ok = False
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: flags={len(flags)} high={high} "
              f"(need flags>={min_flags}, high>={min_high}"
              + (f", high<={max_high}" if max_high is not None else "") + ")")
        if not ok:
            for f in flags:
                print(f"        [{f['level']}] {f['finding']}")
            failures.append(name)

    for name, text, predicate, expectation in INVARIANTS:
        r = run(text, True)
        ok = predicate(r)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}"
              + ("" if ok else f"\n        expected: {expectation}"))
        if not ok:
            failures.append(name)

    print()
    if failures:
        print(f"{len(failures)} regression(s): {', '.join(failures)}")
        return 2
    print(f"all {len(CASES) + len(INVARIANTS)} cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
