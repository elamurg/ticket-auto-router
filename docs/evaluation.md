# Evaluation: keyword baseline vs. semantic classifier

Produced by `python -m router.evaluation.runner --classifier <name>` against the
145-ticket golden set (`data/golden.jsonl`, methodology in `data/LABELGUIDE.md`).
Full machine-readable reports: `results/keyword-20261020T172830Z.json` and
`results/semantic-20261020T172851Z.json`.

## Headline numbers

| Classifier | Accuracy | Mean confidence (correct) | Mean confidence (incorrect) |
|---|---|---|---|
| Keyword baseline | 50.3% | 0.32 | 0.22 |
| Semantic (all-MiniLM-L6-v2) | 72.4% | 0.73 | 0.30 |

The semantic classifier is a clear, substantial improvement, not a marginal one:
22 percentage points of accuracy on a 145-ticket set is roughly 32 tickets that
flipped from wrong to right, far more than the ~2% noise floor the dataset's own
known-weaknesses section (`data/LABELGUIDE.md`) warns about.

## Where it improved

**`COMPLAINT` recall went from 0.05 to 0.63**, the single biggest category-level
change in either direction. The keyword baseline essentially never found a
complaint: its keyword list (`dissapointed`, `angry`, `terrible`, `worst`,
`unacceptable`, `frustrated`) only catches a complaint if the sender used one of
those exact words, and most of the golden set's complaints are expressed through
sentence structure and tone ("this is the second time this has happened") rather
than an angry-word vocabulary. Embedding similarity picks up on the *shape* of a
complaint even without a matching keyword, which is exactly the gap a baseline
with literal keyword matching can't close.

**Calibration is meaningfully better.** The gap between mean confidence on
correct versus incorrect predictions is 0.10 for keyword (0.32 vs 0.22) but 0.43
for semantic (0.73 vs 0.30). This matters beyond the headline accuracy number:
TR-05's `decide_route` sends low-confidence classifications to human review.
A classifier whose confidence barely distinguishes right from wrong makes that
threshold nearly useless, cases worth routing to a human and cases that aren't
get similar confidence scores either way. Semantic's wider gap means the
confidence threshold is actually doing its intended job here.

## Where it got worse, or didn't help

**`OTHER` recall dropped, from 0.93 to 0.57.** The keyword baseline's fallback
rule (no keyword matched -> `OTHER`) is accidentally a decent `OTHER` detector:
most non-support text genuinely doesn't contain billing/technical/account
keywords. The semantic classifier always picks *some* nearest category by
construction, so a sales inquiry or a feature request with no real match to any
of the five canonical `OTHER` examples still gets forced into whichever category
happens to be closest, often wrongly.

**`BILLING` precision dropped, from 0.89 to 0.65.** The semantic classifier
over-predicts `BILLING` on several of the deliberately ambiguous and edge-case
tickets (empty/near-empty bodies, punctuation-only input) that have essentially
no real content to embed, `BILLING`'s canonical examples happen to sit in a
region of embedding space that several low-information inputs drift toward by
default, rather than any of them being a genuine billing signal.

## A specific failure mode, named

**Cross-lingual generalisation is inconsistent, not a capability.** Of the
golden set's three clearly non-English edge cases I checked directly:

- `t131` (French, a technical complaint): keyword predicted `OTHER` (no English
  keywords present), semantic correctly predicted `TECHNICAL` with a real margin
  (confidence 0.54).
- `t129` (Spanish, an account request) and `t130` (German, a billing query):
  **both classifiers predicted `OTHER`**, incorrectly, on both.

It would be a mistake to read `t131`'s success as "the semantic classifier
handles non-English tickets." `all-MiniLM-L6-v2` was trained predominantly on
English text; whatever cross-lingual signal let it get `t131` right didn't
generalise to the other two non-English cases in the same small sample. The
honest conclusion is narrower: embeddings *can* occasionally succeed on
non-English input where keyword matching structurally cannot, but this is not a
reliable capability to design around, and a production system handling
multilingual tickets would need either a multilingual embedding model or an
explicit language-detection step before classification, neither of which this
baseline has.

## A second observation worth recording

On the lowest-information edge cases (gibberish, punctuation-only, an
all-caps empty-content ticket), the semantic classifier's wrong predictions
consistently came with very low confidence (0.01-0.22 in the cases checked),
while its correct predictions on clear tickets sit much higher (0.5-1.0). This
is the calibration finding above showing up concretely: even where the
classifier is wrong, the confidence score is honest about *being* wrong, which
means TR-05's human-review threshold would catch most of these specific
failures in the full pipeline, rather than silently misrouting them.

## Conclusion

The semantic classifier is a real improvement over the keyword baseline on
accuracy, on the one category (`COMPLAINT`) that most needed better
understanding of tone rather than vocabulary, and on calibration, which is the
property the whole system's human-review threshold actually depends on. It is
not a universal improvement: `OTHER` recall and `BILLING` precision both
regressed, and non-English handling remains unreliable rather than solved. Both
of those are reasonable things to re-examine once the LLM stage (Sprint 4)
exists and gets measured against this same baseline.
