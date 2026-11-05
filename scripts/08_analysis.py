"""
Step 8: descriptive and inferential analysis (Report 4 - Results).

Run after 06_score.py:
    python scripts/08_analysis.py

Reads:
    data/scored/<name>_scored.csv      scored replies from script 06 (pilot files are skipped)
    data/questions/questions_final.csv question details (league, property, Malay Wikipedia page, site links)
    data/coarse_answer_keys.csv        birthplace answer keys that are a state or a country (sensitivity check)
Writes (results/analysis/; table numbers match the tables in Report 4, where Tables 1-3 are in the Methods):
    table04_accuracy.csv          accuracy per chatbot and group, 95% Wilson confidence intervals
    table05_h1_mcnemar.csv        H1: English vs Malay on the same questions, no fact (McNemar's exact test)
    table06_h2_league_gap.csv     H2: is the English-Malay gap wider for Malaysia Super League than for NBA?
    table06b_h2_logit.csv         H2: logistic regression correct ~ Malay * MSL (no fact, Wikidata)
    table07_h3_fact_gap.csv       H3: does adding the fact shrink the English-Malay gap?
    table08_h4_malay_wikipedia.csv H4: Malay Wikipedia page and accuracy (MSL players, no fact)
    table09_by_question_type.csv  accuracy by question type (no fact)
    reply_language.csv            share of replies in the language of the question (no table in the report)
    table10_sensitivity.csv       sensitivity checks: broader answer keys removed; "New York" replies counted correct
    figures/fig1_accuracy_no_fact.png, fig2_fact_effect.png, fig3_malay_wikipedia.png

Methods (also in README.md):
- Accuracy: share of replies scored correct, with 95% Wilson confidence intervals.
- H1 (English > Malay without the fact): each question is asked in both languages, so the two
  answers are paired. McNemar's exact test uses the discordant pairs (right in English only vs
  right in Malay only). The 95% CI of the paired difference uses the standard formula for paired
  proportions. Tested on all no-fact questions (main test) and for NBA, MSL and MKQA separately.
- H2 (gap wider for MSL than NBA): for each Wikidata question, d = correct in English - correct in
  Malay (-1, 0 or 1). The gap in a league is the mean of d; the gap difference (MSL - NBA) gets a
  normal-approximation CI and z-test. Also a logistic regression correct ~ malay * msl with
  standard errors clustered by question (the interaction term is the H2 test on the odds scale).
- H3 (the fact shrinks the MSL gap): for each MSL question, change = d(no fact) - d(with fact);
  a positive mean change means the gap shrank. Paired t-test on the per-question change. A logistic
  interaction model is not used here because several with-fact groups are 100% correct (the
  model cannot be estimated when a group has no wrong answers).
- H4 (Malay Wikipedia page helps Malay answers): Malaysia Super League player questions without the
  fact; logistic regression correct ~ has Malay Wikipedia page + log(1 + site links) + question
  type, standard errors clustered by player. Run for Malay (the H4 test) and English (comparison).
  NBA players are left out: only 3 of 500 have a Malay Wikipedia page.
"""
import argparse
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

try:
    import statsmodels.formula.api as smf
except ImportError:
    sys.exit("This script needs statsmodels: pip install -r requirements.txt")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
SCORED_DIR = ROOT / "data" / "scored"
QUESTIONS_PATH = ROOT / "data" / "questions" / "questions_final.csv"
COARSE_PATH = ROOT / "data" / "coarse_answer_keys.csv"
OUT_DIR = ROOT / "results" / "analysis"
FIG_DIR = OUT_DIR / "figures"

CHATBOTS = {  # file name stem -> label
    "gemini_gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite",
    "sealion_Qwen-SEA-LION-v4.5-27B-IT": "SEA-LION v4.5",
}
SETS = {"nba": "NBA", "msl": "MSL", "mixed": "MKQA"}
LANGS = {"en": "English", "ms": "Malay"}
CONDS = {"no_facts": "no fact", "with_facts": "with fact"}
Z = 1.959964

# chart colours (validated two-slot categorical palette: blue = English, orange = Malay)
COLORS = {"en": "#2a78d6", "ms": "#eb6834"}
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e4df"


# ---------- helpers ----------

def wilson(k, n):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def pct(x, digits=1):
    return round(100 * x, digits) if pd.notna(x) else np.nan


def load():
    if not QUESTIONS_PATH.exists():
        sys.exit(f"Missing {QUESTIONS_PATH}. Run scripts/04_combine_questions.py first.")
    q = pd.read_csv(QUESTIONS_PATH, keep_default_na=False, dtype=str, encoding="utf-8-sig")
    q = q[["question_id", "entity_type", "entity_qid", "property", "answer_type",
           "has_malay_wikipedia", "sitelinks"]]
    frames = []
    for stem, label in CHATBOTS.items():
        path = SCORED_DIR / f"{stem}_scored.csv"
        if not path.exists():
            print(f"  Note: {path.relative_to(ROOT)} not found; {label} is skipped.")
            continue
        d = pd.read_csv(path, keep_default_na=False, dtype=str, encoding="utf-8-sig")
        d = d[d["score"].isin(["0", "1"])].copy()
        d["chatbot"] = label
        frames.append(d)
    if not frames:
        sys.exit("No scored files found. Run scripts/06_score.py first.")
    df = pd.concat(frames, ignore_index=True)
    df = df.merge(q, on="question_id", how="left", validate="many_to_one")
    df["correct"] = df["score"].astype(int)
    df["set"] = df["league"].map(SETS)
    df["malay"] = (df["language"] == "ms").astype(int)
    df["msl"] = (df["league"] == "msl").astype(int)
    df["has_ms_wiki"] = pd.to_numeric(df["has_malay_wikipedia"], errors="coerce")
    df["log_sitelinks"] = np.log1p(pd.to_numeric(df["sitelinks"], errors="coerce"))
    coarse = set()
    if COARSE_PATH.exists():
        coarse = set(pd.read_csv(COARSE_PATH, dtype=str, encoding="utf-8-sig")["question_id"])
    df["coarse_key"] = df["question_id"].isin(coarse)
    return df


def save(table, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_DIR / name, index=False, encoding="utf-8-sig")
    return table


# ---------- descriptive ----------

def accuracy_table(df):
    rows = []
    for (bot, s, lang, cond), g in df.groupby(["chatbot", "set", "language", "condition"]):
        k, n = int(g["correct"].sum()), len(g)
        lo, hi = wilson(k, n)
        rows.append({"chatbot": bot, "set": s, "language": LANGS[lang], "condition": CONDS[cond],
                     "n": n, "correct": k, "accuracy_pct": pct(k / n), "ci_low_pct": pct(lo),
                     "ci_high_pct": pct(hi)})
    order = {"NBA": 0, "MSL": 1, "MKQA": 2}
    t = pd.DataFrame(rows)
    t = t.sort_values(["chatbot", "condition", "set", "language"], key=lambda c: c.map(order) if c.name == "set" else c)
    return t.reset_index(drop=True)


# ---------- H1: paired English vs Malay ----------

def paired(df, cond="no_facts"):
    """One row per question with English and Malay correctness (0/1)."""
    d = df[df["condition"] == cond]
    w = d.pivot_table(index=["chatbot", "question_id", "set", "property"], columns="language",
                      values="correct", aggfunc="first").dropna().reset_index()
    w["d"] = w["en"] - w["ms"]
    return w


def mcnemar_row(w, bot, subset):
    n = len(w)
    b = int(((w["en"] == 1) & (w["ms"] == 0)).sum())   # right in English only
    c = int(((w["en"] == 0) & (w["ms"] == 1)).sum())   # right in Malay only
    diff = (b - c) / n
    se = math.sqrt(max(b + c - (b - c) ** 2 / n, 0)) / n
    p = stats.binomtest(b, b + c, 0.5).pvalue if b + c > 0 else 1.0
    p_one = stats.binomtest(b, b + c, 0.5, alternative="greater").pvalue if b + c > 0 else 1.0
    return {"chatbot": bot, "questions": subset, "n_pairs": n,
            "english_pct": pct(w["en"].mean()), "malay_pct": pct(w["ms"].mean()),
            "diff_pct_points": pct(diff, 2), "diff_ci_low": pct(diff - Z * se, 2), "diff_ci_high": pct(diff + Z * se, 2),
            "right_in_english_only": b, "right_in_malay_only": c,
            "mcnemar_p_two_sided": round(p, 4), "mcnemar_p_english_better": round(p_one, 4)}


def h1_table(df):
    w = paired(df)
    rows = []
    for bot, g in w.groupby("chatbot"):
        rows.append(mcnemar_row(g, bot, "All (no fact)"))
        for s in ["NBA", "MSL", "MKQA"]:
            rows.append(mcnemar_row(g[g["set"] == s], bot, s))
    return pd.DataFrame(rows)


# ---------- H2: is the gap wider for MSL? ----------

def mean_ci(x):
    x = np.asarray(x, dtype=float)
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(len(x))
    return m, se


def h2_tables(df, label="main"):
    w = paired(df[df["source"] == "wikidata"])
    rows, coefs = [], []
    for bot, g in w.groupby("chatbot"):
        nba, msl = g[g["set"] == "NBA"]["d"], g[g["set"] == "MSL"]["d"]
        m_n, se_n = mean_ci(nba)
        m_m, se_m = mean_ci(msl)
        diff, se = m_m - m_n, math.sqrt(se_n ** 2 + se_m ** 2)
        p = 2 * stats.norm.sf(abs(diff / se)) if se > 0 else 1.0
        rows.append({"analysis": label, "chatbot": bot, "n_nba": len(nba), "n_msl": len(msl),
                     "gap_nba_pct_points": pct(m_n, 2), "gap_msl_pct_points": pct(m_m, 2),
                     "gap_difference_msl_minus_nba": pct(diff, 2),
                     "ci_low": pct(diff - Z * se, 2), "ci_high": pct(diff + Z * se, 2), "p_two_sided": round(p, 4)})
        if label != "main":
            continue
        d = df[(df["chatbot"] == bot) & (df["source"] == "wikidata") & (df["condition"] == "no_facts")]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = smf.logit("correct ~ malay * msl", data=d).fit(
                    disp=False, cov_type="cluster", cov_kwds={"groups": pd.factorize(d["question_id"])[0]})
            ci = fit.conf_int()
            names = {"Intercept": "Intercept (NBA, English)", "malay": "Malay", "msl": "MSL",
                     "malay:msl": "Malay x MSL (H2)"}
            for term in fit.params.index:
                coefs.append({"chatbot": bot, "term": names.get(term, term), "log_odds": round(fit.params[term], 4),
                              "odds_ratio": round(math.exp(fit.params[term]), 3),
                              "or_ci_low": round(math.exp(ci.loc[term, 0]), 3),
                              "or_ci_high": round(math.exp(ci.loc[term, 1]), 3),
                              "p": round(fit.pvalues[term], 4), "n_replies": int(fit.nobs)})
        except Exception as e:  # noqa: BLE001
            coefs.append({"chatbot": bot, "term": f"model failed: {e}"})
    return pd.DataFrame(rows), pd.DataFrame(coefs)


# ---------- H3: does the fact shrink the gap? ----------

def h3_table(df):
    d = df[df["source"] == "wikidata"]
    nf, wf = paired(d, "no_facts"), paired(d, "with_facts")
    m = nf.merge(wf[["chatbot", "question_id", "d"]], on=["chatbot", "question_id"], suffixes=("_nf", "_wf"))
    m["change"] = m["d_nf"] - m["d_wf"]
    rows = []
    for (bot, s), g in m.groupby(["chatbot", "set"]):
        g_nf, se_nf = mean_ci(g["d_nf"])
        g_wf, se_wf = mean_ci(g["d_wf"])
        ch, se_ch = mean_ci(g["change"])
        p = stats.ttest_1samp(g["change"], 0).pvalue if g["change"].std() > 0 else 1.0
        rows.append({"chatbot": bot, "league": s, "n_questions": len(g),
                     "gap_no_fact_pct_points": pct(g_nf, 2), "gap_no_fact_ci": f"[{pct(g_nf - Z * se_nf, 2)}, {pct(g_nf + Z * se_nf, 2)}]",
                     "gap_with_fact_pct_points": pct(g_wf, 2), "gap_with_fact_ci": f"[{pct(g_wf - Z * se_wf, 2)}, {pct(g_wf + Z * se_wf, 2)}]",
                     "gap_shrinks_by_pct_points": pct(ch, 2), "ci_low": pct(ch - Z * se_ch, 2),
                     "ci_high": pct(ch + Z * se_ch, 2), "p_paired_t": round(float(p), 4)})
    t = pd.DataFrame(rows)
    return t.sort_values(["chatbot", "league"], ascending=[True, False]).reset_index(drop=True)


# ---------- H4: Malay Wikipedia page ----------

def h4_table(df):
    d = df[(df["league"] == "msl") & (df["entity_type"] == "player") & (df["condition"] == "no_facts")]
    rows = []
    for (bot, lang), g in d.groupby(["chatbot", "language"]):
        row = {"chatbot": bot, "language": LANGS[lang], "test": "H4" if lang == "ms" else "comparison"}
        for has, label in [(1, "with_page"), (0, "without_page")]:
            h = g[g["has_ms_wiki"] == has]
            lo, hi = wilson(int(h["correct"].sum()), len(h))
            row.update({f"n_{label}": len(h), f"acc_{label}_pct": pct(h["correct"].mean()),
                        f"ci_{label}": f"[{pct(lo)}, {pct(hi)}]"})
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = smf.logit("correct ~ has_ms_wiki + log_sitelinks + C(property)", data=g).fit(
                    disp=False, cov_type="cluster", cov_kwds={"groups": pd.factorize(g["entity_qid"])[0]})
            ci = fit.conf_int()
            for term, name in [("has_ms_wiki", "page"), ("log_sitelinks", "log_sitelinks")]:
                row.update({f"or_{name}": round(math.exp(fit.params[term]), 3),
                            f"or_{name}_ci": f"[{math.exp(ci.loc[term, 0]):.3f}, {math.exp(ci.loc[term, 1]):.3f}]",
                            f"p_{name}": round(fit.pvalues[term], 4)})
            row["n_replies"] = int(fit.nobs)
        except Exception as e:  # noqa: BLE001
            row["model"] = f"failed: {e}"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------- more descriptive tables ----------

def by_type_table(df):
    d = df[df["condition"] == "no_facts"].copy()
    d["question_type"] = d["property"].replace("", "MKQA (mixed)")
    rows = []
    for (bot, s, qt, lang), g in d.groupby(["chatbot", "set", "question_type", "language"]):
        rows.append({"chatbot": bot, "set": s, "question_type": qt, "language": LANGS[lang],
                     "n": len(g), "accuracy_pct": pct(g["correct"].mean())})
    t = pd.DataFrame(rows)
    w = t.pivot_table(index=["chatbot", "set", "question_type"], columns="language",
                      values=["n", "accuracy_pct"]).reset_index()
    w.columns = [" ".join(c).strip() if isinstance(c, tuple) else c for c in w.columns]
    return w


def reply_language_table(df):
    rows = []
    for (bot, lang, cond), g in df.groupby(["chatbot", "language", "condition"]):
        known = g[g["reply_language"] != "unknown"]
        rows.append({"chatbot": bot, "question_language": LANGS[lang], "condition": CONDS[cond],
                     "replies": len(g), "language_detectable": len(known),
                     "in_question_language_pct": pct((known["reply_language"] == lang).mean()) if len(known) else np.nan,
                     "unknown_pct": pct(1 - len(known) / len(g))})
    return pd.DataFrame(rows)


# ---------- sensitivity checks ----------

NYC_WORDS = ["new york", "brooklyn", "bronx", "queens", "manhattan", "staten island"]


def h1_text(r, with_ci=False):
    t = f"{r['diff_pct_points']}"
    if with_ci:
        t += f" [{r['diff_ci_low']}, {r['diff_ci_high']}]"
    return f"{t} (p = {r['mcnemar_p_two_sided']})"


def h1_rows(check, h1_main, h1_sens, subsets):
    """H1 rows for a sensitivity check: 'All (no fact)' is the overall H1 test (shown with its 95% CI)."""
    rows = []
    for _, r in h1_main[h1_main["questions"].isin(subsets)].iterrows():
        s = h1_sens[(h1_sens["chatbot"] == r["chatbot"]) & (h1_sens["questions"] == r["questions"])].iloc[0]
        overall = r["questions"] == "All (no fact)"
        name = "overall" if overall else r["questions"]
        rows.append({"check": check, "chatbot": r["chatbot"],
                     "measure": f"H1 {name}: English - Malay (points){' [95% CI]' if overall else ''}, McNemar p",
                     "main": h1_text(r, overall), "sensitivity": h1_text(s, overall),
                     "n_main": r["n_pairs"], "n_sensitivity": s["n_pairs"]})
    return rows


def h2_rows(check, h2_main, h2_sens):
    """H2 rows for a sensitivity check; n = NBA + MSL Wikidata questions."""
    rows = []
    for _, r in h2_main.iterrows():
        s = h2_sens[h2_sens["chatbot"] == r["chatbot"]].iloc[0]
        rows.append({"check": check, "chatbot": r["chatbot"],
                     "measure": "H2 gap difference MSL - NBA (points), z-test p",
                     "main": f"{r['gap_difference_msl_minus_nba']} (p = {r['p_two_sided']})",
                     "sensitivity": f"{s['gap_difference_msl_minus_nba']} (p = {s['p_two_sided']})",
                     "n_main": int(r["n_nba"] + r["n_msl"]), "n_sensitivity": int(s["n_nba"] + s["n_msl"])})
    return rows


def sensitivity_table(df):
    rows = []
    h1_main = h1_table(df)
    h2_main, _ = h2_tables(df, label="sensitivity")   # same numbers as table 6; skips refitting the logit

    # (a) leave out birthplace questions whose answer key is a state or a country
    check = "broader answer keys removed"
    keep = df[~df["coarse_key"]]
    for bot in df["chatbot"].unique():
        for s in ["NBA", "MSL"]:
            for lang in ["en", "ms"]:
                a = df[(df["chatbot"] == bot) & (df["set"] == s) & (df["language"] == lang) & (df["condition"] == "no_facts")]
                b = keep[(keep["chatbot"] == bot) & (keep["set"] == s) & (keep["language"] == lang) & (keep["condition"] == "no_facts")]
                rows.append({"check": check, "chatbot": bot,
                             "measure": f"{s} accuracy, {LANGS[lang]}, no fact",
                             "main": pct(a["correct"].mean()), "sensitivity": pct(b["correct"].mean()),
                             "n_main": len(a), "n_sensitivity": len(b)})
    rows += h1_rows(check, h1_main, h1_table(keep), ["All (no fact)", "NBA", "MSL"])
    rows += h2_rows(check, h2_main, h2_tables(keep, label="sensitivity")[0])

    # (b) count "New York" and borough replies as correct for New York City answers
    check = "\"New York\" replies counted correct"
    ny = df.copy()
    is_nyc = ny["answer_en"].eq("New York City")
    mentions = ny["response"].str.lower().apply(lambda t: any(w in t for w in NYC_WORDS))
    changed = is_nyc & mentions & ny["correct"].eq(0)
    ny.loc[changed, "correct"] = 1
    for bot in df["chatbot"].unique():
        mine = changed & (ny["chatbot"] == bot)
        rows.append({"check": check, "chatbot": bot,
                     "measure": "replies changed from incorrect to correct",
                     "main": 0, "sensitivity": int(mine.sum()), "n_main": "", "n_sensitivity": ""})
        for lang in ["en", "ms"]:
            rows.append({"check": check, "chatbot": bot,
                         "measure": f"replies changed from incorrect to correct, {LANGS[lang]} questions",
                         "main": 0, "sensitivity": int((mine & (ny["language"] == lang)).sum()),
                         "n_main": "", "n_sensitivity": ""})
        for lang in ["en", "ms"]:
            a = df[(df["chatbot"] == bot) & (df["set"] == "NBA") & (df["language"] == lang) & (df["condition"] == "no_facts")]
            b = ny[(ny["chatbot"] == bot) & (ny["set"] == "NBA") & (ny["language"] == lang) & (ny["condition"] == "no_facts")]
            rows.append({"check": check, "chatbot": bot,
                         "measure": f"NBA accuracy, {LANGS[lang]}, no fact",
                         "main": pct(a["correct"].mean()), "sensitivity": pct(b["correct"].mean()),
                         "n_main": len(a), "n_sensitivity": len(b)})
    rows += h1_rows(check, h1_main, h1_table(ny), ["All (no fact)", "NBA"])
    rows += h2_rows(check, h2_main, h2_tables(ny, label="sensitivity")[0])
    return pd.DataFrame(rows)


# ---------- figures ----------

def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=10, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 105)
    ax.set_yticks(range(0, 101, 20))
    ax.set_yticklabels([f"{v}%" for v in range(0, 101, 20)])


def grouped_bars(ax, labels, values, title):
    """values: {lang: [(acc, lo, hi), ...]} in label order; bars English then Malay."""
    x = np.arange(len(labels))
    width = 0.36
    for i, lang in enumerate(["en", "ms"]):
        acc = np.array([v[0] for v in values[lang]])
        err = np.array([[a - lo for a, lo, hi in values[lang]], [hi - a for a, lo, hi in values[lang]]])
        pos = x + (i - 0.5) * (width + 0.02)
        ax.bar(pos, acc, width, color=COLORS[lang], edgecolor=SURFACE, linewidth=2, label=LANGS[lang], zorder=2)
        ax.errorbar(pos, acc, yerr=err, fmt="none", ecolor=INK, elinewidth=1, capsize=3, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=INK, fontsize=10)
    ax.set_title(title, color=INK, fontsize=12, loc="left", fontweight="bold")
    style(ax)


def acc_ci(g):
    k, n = int(g["correct"].sum()), len(g)
    lo, hi = wilson(k, n)
    return 100 * k / n, 100 * lo, 100 * hi


def figures(df):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    bots = [b for b in CHATBOTS.values() if b in set(df["chatbot"])]
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE})

    # Figure 1: no-fact accuracy, English vs Malay
    fig, axes = plt.subplots(1, len(bots), figsize=(5.2 * len(bots), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, bot in zip(axes, bots):
        d = df[(df["chatbot"] == bot) & (df["condition"] == "no_facts")]
        vals = {lang: [acc_ci(d[(d["set"] == s) & (d["language"] == lang)]) for s in ["NBA", "MSL", "MKQA"]]
                for lang in ["en", "ms"]}
        grouped_bars(ax, ["NBA", "Malaysia\nSuper League", "MKQA"], vals, bot)
    axes[0].set_ylabel("Accuracy (no fact in prompt)", color=INK2)
    axes[-1].legend(frameon=False, loc="upper right", fontsize=10)
    fig.text(0.01, 0.01, "Error bars: 95% Wilson confidence intervals.", color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_DIR / "fig1_accuracy_no_fact.png", dpi=200)
    plt.close(fig)

    # Figure 2: effect of adding the fact (Wikidata questions)
    fig, axes = plt.subplots(1, len(bots), figsize=(5.6 * len(bots), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    groups = [("NBA", "no_facts"), ("NBA", "with_facts"), ("MSL", "no_facts"), ("MSL", "with_facts")]
    for ax, bot in zip(axes, bots):
        d = df[df["chatbot"] == bot]
        vals = {lang: [acc_ci(d[(d["set"] == s) & (d["condition"] == c) & (d["language"] == lang)]) for s, c in groups]
                for lang in ["en", "ms"]}
        grouped_bars(ax, ["NBA\nno fact", "NBA\nwith fact", "MSL\nno fact", "MSL\nwith fact"], vals, bot)
    axes[0].set_ylabel("Accuracy", color=INK2)
    axes[-1].legend(frameon=False, loc="upper left", fontsize=10, bbox_to_anchor=(0, 0.93))
    fig.text(0.01, 0.01, "MSL = Malaysia Super League. Error bars: 95% Wilson confidence intervals.", color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_DIR / "fig2_fact_effect.png", dpi=200)
    plt.close(fig)

    # Figure 3: Malay Wikipedia page (MSL players, no fact)
    fig, axes = plt.subplots(1, len(bots), figsize=(5.2 * len(bots), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, bot in zip(axes, bots):
        d = df[(df["chatbot"] == bot) & (df["league"] == "msl") & (df["entity_type"] == "player") & (df["condition"] == "no_facts")]
        vals = {lang: [acc_ci(d[(d["has_ms_wiki"] == h) & (d["language"] == lang)]) for h in [0, 1]] for lang in ["en", "ms"]}
        grouped_bars(ax, ["No Malay\nWikipedia page", "Has a Malay\nWikipedia page"], vals, bot)
    axes[0].set_ylabel("Accuracy, MSL players (no fact)", color=INK2)
    axes[-1].legend(frameon=False, loc="upper right", fontsize=10)
    fig.text(0.01, 0.01, "Error bars: 95% Wilson confidence intervals. Not adjusted for site links (see Table 8).", color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG_DIR / "fig3_malay_wikipedia.png", dpi=200)
    plt.close(fig)


# ---------- main ----------

def show(title, table, cols=None):
    print(f"\n{title}")
    with pd.option_context("display.width", 200, "display.max_columns", 30, "display.max_colwidth", 60):
        print((table[cols] if cols else table).to_string(index=False))


def main():
    argparse.ArgumentParser(description="Descriptive and inferential analysis for Report 4").parse_args()
    df = load()
    print(f"Loaded {len(df)} scored replies: " + ", ".join(f"{b} {n}" for b, n in df["chatbot"].value_counts().items()))

    t1 = save(accuracy_table(df), "table04_accuracy.csv")
    t2 = save(h1_table(df), "table05_h1_mcnemar.csv")
    t3, t3b = h2_tables(df)
    save(t3, "table06_h2_league_gap.csv")
    save(t3b, "table06b_h2_logit.csv")
    t4 = save(h3_table(df), "table07_h3_fact_gap.csv")
    t5 = save(h4_table(df), "table08_h4_malay_wikipedia.csv")
    save(by_type_table(df), "table09_by_question_type.csv")
    t7 = save(reply_language_table(df), "reply_language.csv")
    t8 = save(sensitivity_table(df), "table10_sensitivity.csv")
    figures(df)

    show("Table 4 (no fact): accuracy %", t1[t1["condition"] == "no fact"],
         ["chatbot", "set", "language", "n", "accuracy_pct", "ci_low_pct", "ci_high_pct"])
    show("H1: English vs Malay, same questions, no fact (McNemar)", t2)
    show("H2: English-Malay gap, MSL vs NBA (percentage points)", t3)
    show("H2: logistic regression (odds ratios, clustered by question)", t3b)
    show("H3: English-Malay gap without and with the fact", t4)
    show("H4: Malay Wikipedia page (MSL players, no fact)", t5)
    show("Reply language", t7)
    show("Sensitivity checks", t8)
    print(f"\nSaved tables in {OUT_DIR.relative_to(ROOT)}/ and figures in {FIG_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
