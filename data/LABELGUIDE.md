# Labelling Guide

How every label in `data/golden.jsonl` was decided. This document exists so the
labels are reproducible rather than intuitive — if two people apply these rules
to the same ticket they should reach the same answer, and where they don't, the
guide is wrong and gets fixed.

Every row carries a `note` field giving the rationale for that specific label.
This file gives the rules those notes apply.

---

## The categories

**BILLING** — money. Charges, refunds, invoices, pricing, payment methods, tax,
plan costs. If resolving it requires someone to look at a payment or an invoice,
it is BILLING.

**TECHNICAL** — the product is not behaving as designed. Errors, defects,
performance, integrations, API behaviour, data correctness. If a fix would be a
code change or an incident, it is TECHNICAL.

**ACCOUNT** — who can do what. Access, login, users, permissions, profile and
workspace settings, account lifecycle. If resolving it means changing a user,
a permission or an account setting, it is ACCOUNT.

**COMPLAINT** — dissatisfaction with how they have been treated. The request is
for accountability, escalation, apology or compensation rather than a fix.

**OTHER** — everything that is not a support request: sales, partnerships,
press, recruitment, feature requests, research, misdirected mail, and anything
with too little content to classify.

---

## The decision rules, in order

Apply these in sequence. The first one that resolves the case wins.

**1. What outcome does the sender want?**
Not what the ticket is about — what they are asking for. "I was charged twice
because your checkout is broken" is BILLING, because they want their money back,
not a bug fix.

**2. Which team resolves it?**
If finance resolves it, BILLING. If engineering resolves it, TECHNICAL. If
account administration resolves it, ACCOUNT. This is the test that routing
actually exists for.

**3. Is the primary ask accountability rather than a fix?**
If so, COMPLAINT, regardless of subject matter. A broken feature is TECHNICAL;
being angry that it was broken for three weeks and nobody replied is COMPLAINT.
The distinguishing question: would fixing the thing, silently, satisfy them?
If no, COMPLAINT.

**4. Is this a support request at all?**
Sales, press, recruitment, partnerships, feature requests and research are
OTHER. A feature request is not a defect: the product is working as designed and
they want it designed differently.

**5. First stated intent wins.**
Multi-intent tickets take the category of the first concrete ask, flagged for
splitting. See `t139`.

**6. When still undecided, prefer the category whose team can act first.**
A ticket in the wrong queue costs one handoff. A ticket nobody can act on costs
days.

---

## Judgement calls, recorded

These are the decisions a second labeller could reasonably make differently.
They are written down so disagreement is a conversation about the rule rather
than about the ticket.

**Cancel and refund** → BILLING. Cancellation is ACCOUNT, refund is BILLING. The
money is the thing they actually want; the cancellation is the mechanism.

**Locked out because payment failed** → BILLING. Classify by root cause when the
cause is unambiguous, because fixing the payment fixes the access.

**Permissions changed but not taking effect** → TECHNICAL. Permissions are
ACCOUNT, but "I did the thing and it didn't work" is a defect.

**SSO redirect loop** → TECHNICAL. Authentication is ACCOUNT territory, but a
loop is a bug in the integration.

**Setting up SSO** → ACCOUNT. Configuration of access, not a defect. Note that
this and the previous rule put SSO in two different categories depending on
whether something is broken. That is deliberate, and it is the kind of thing a
classifier finds genuinely hard.

**Session expires too fast** → TECHNICAL. Presented as a defect, not as an
access request.

**Price rise with no notice** → COMPLAINT, not BILLING. They are not disputing
the charge, they are objecting to how it was communicated.

**Outage cost us money** → COMPLAINT, not TECHNICAL. The incident is over. The
ask is compensation.

**Data loss** → COMPLAINT, highest priority. A severe technical incident, but
the sender wants an explanation and accountability, and routing it to an
engineering queue would be experienced as a brush-off.

**GDPR data request** → ACCOUNT. Defensible as OTHER (legal). Chosen because
account administration executes it in most organisations.

**Security questionnaire** → OTHER. Procurement process, not a technical issue.

**Bug bounty / vulnerability report** → OTHER with escalation. TECHNICAL is
defensible; chosen as OTHER because it needs a specific disclosure process
rather than the normal defect queue. **This is the weakest label in the set.**

**Charity pricing** → OTHER, not BILLING. No account and no charge exists yet,
so it is pre-sales.

**Integration capability questions** → OTHER when pre-sales, TECHNICAL when an
existing integration is broken.

---

## Edge cases and what they test

| Case | Tests |
|---|---|
| `t125` empty subject and body | Does not crash; routes to triage rather than guessing |
| `t127` empty subject, clear body | The classifier reads the body, not just the subject |
| `t128`–`t131` Slovenian, Spanish, German, French | Non-English handling. A keyword baseline will fail all four, which is the point: it shows what the embedding and LLM tiers are buying |
| `t132` punctuation only | No semantic content |
| `t133` all caps, no information | Urgency without content; must not be mistaken for severity |
| `t134` forwarded chain | Quoted text with no retained content |
| `t135` gibberish | Nonsense input |
| `t136` signature and disclaimer only | Boilerplate stripping |
| `t139` four separate intents | Multi-intent policy |
| `t140` four categories plus anger | Tone versus content |
| `t141` 5,000 characters, issue in the last sentence | Truncation strategy — truncating the start loses the answer |
| `t142` emoji only | Sentiment without content |
| `t144` HTML-wrapped body | Markup stripping |
| `t145` praise plus a real defect | Sentiment must not override the actual issue |

Expect your keyword baseline to score close to zero on the non-English cases and
on anything requiring the body to be read properly. That contrast is what makes
the later comparison meaningful.

---

## Known weaknesses of this dataset

Say these out loud in an interview before anyone asks.

- **The labels are one person's judgement.** The accuracy figures are internally
  consistent, not externally valid.
- **The tickets are invented.** Real support text is messier, more repetitive,
  and contains far more boilerplate than this.
- **The distribution is chosen, not observed.** Real queues are usually dominated
  by a handful of recurring issues; this set is deliberately more varied.
- **145 cases is small.** A single misclassification moves accuracy by 0.7%, so
  changes under about 2% are noise.
- **COMPLAINT is under-represented** at 19 cases, which makes its per-class
  recall the least reliable number in any report.

---

## Changing a label

Labels are not frozen, but changes are deliberate:

1. Edit both `category` **and** `note` in `data/golden.jsonl`.
2. If the change reflects a rule rather than a one-off, update this guide.
3. Re-run the evaluation and record the new baseline.
4. Note the change in the commit message. A silent label change invalidates
   every score recorded before it.

Run `python golden.py relabel` to label a sample blind and measure your
agreement with the file. Your agreement rate is roughly the ceiling any
classifier can fairly be held to — record it in the README.
