# entitygate

### Your RAG pipeline isn't hallucinating. It's misattributing. That's worse, and nothing checks for it.

[![tests](https://img.shields.io/badge/tests-12%2F12%20passing-brightgreen)](#)
[![license](https://img.shields.io/badge/license-MIT-blue)](#license)
[![deps](https://img.shields.io/badge/dependencies-zero-brightgreen)](#)

```bash
pip install -e .
```

---

## The bug that started this

A real production AI pipeline asked Google: *"What is Prashanth Hospitals'
official Instagram account?"*

Google's AI Overview answered with a real, correctly-formatted, verbatim-present
Instagram handle: `timedical1`.

**It just wasn't Prashanth Hospitals' handle.** It was a random healthcare
account Google happened to cite as a market-trends source three sentences
earlier. The AI pipeline attributed it anyway — and so did an LLM-as-judge
"is this grounded in the context?" check, the exact thing most RAG teams
reach for to catch this.

**Neither caught it. One line of code does:**

```python
from entitygate import verify_claim

verify_claim("timedical1", "Prashanth Hospitals", source_text)
# VerificationResult(verified=False, reason='no_entity_match', ...)
```

Not because it's smarter than the LLM. Because `timedical1` doesn't contain
the word `Prashanth`, and that's the one question every groundedness
checker forgets to ask.

---

## Why your current hallucination tooling doesn't catch this

Guardrails, Instructor, RAGAS faithfulness, SelfCheckGPT, NLI-entailment
checkers — all excellent at one question: **"is this claim supported by the
retrieved text?"**

That's the wrong question for this bug. `timedical1` *is* supported by the
text. It's really there. The claim isn't fabricated — **it's attached to
the wrong entity**, and "is this grounded" and "is this about the right
entity" only look like the same question until they aren't.

| Failure mode | Caught by groundedness/faithfulness checks? | Caught by entitygate? |
|---|---|---|
| LLM invents a fact that doesn't exist anywhere | ✅ Yes | — (not what this is for) |
| Real fact, cited third party attributed to the subject | ❌ No — it's real, it's grounded | ✅ Yes |
| Name-collision competitor from an unrelated industry accepted as a peer | ❌ No | ⚠️ Partially — see Known Limitations |
| Lookalike/franchise account measured instead of the real one | ❌ No | ✅ Yes |

---

## See it for yourself — real cases, real LLM calls, no cherry-picking

```bash
python benchmark/run_benchmark.py   # needs GROQ_API_KEY
```

Three methods, run against the **identical real input**: a naive LLM
extraction, an LLM-as-judge faithfulness check, and `entitygate`.

```
case                           truth          naive      faithful   entitygate   reason
----------------------------------------------------------------------------------------------------
arun_icecreams_correct         correct        ACCEPT     ACCEPT     ACCEPT       ok
havmor_correct                 correct        ACCEPT     ACCEPT     ACCEPT       ok
kauvery_apollo_collision       misattributed  reject     reject     reject       no_entity_match
prashanth_timedical1           misattributed  ACCEPT ✗   ACCEPT ✗   reject ✓     no_entity_match
sundaram_residency_finance     misattributed  reject ✓   reject ✓   ACCEPT ✗     ok
zoho_gartner_citation          misattributed  reject     reject     reject       no_entity_match
```

**I'm not going to tell you this is a clean sweep, because it isn't, and a
benchmark that only shows wins isn't a benchmark.** On `sundaram_residency_finance`,
entitygate is *wrong* and the naive LLM is *right* — two real companies
share a distinctive brand word across unrelated industries, and a
name-anchor check alone can't see that (see Known Limitations below).

What the numbers *do* support: on the one real, documented bug this
project exists for, **both the naive extraction and the faithfulness
checker confidently failed, on identical input, and entitygate was the
only method of the three that caught it** — deterministically, for $0,
with zero added LLM calls. That's not "better at everything." That's "closes
one real, provable gap the other two structurally can't see."

Full results: [`benchmark/results/latest.json`](benchmark/results/latest.json).
Six cases isn't a statistic — don't read a percentage into it. It's a
reproducible demonstration you can rerun against the real APIs yourself.

---

## Who this is actually for

✅ **Competitive-intelligence / company-data SaaS** pulling a company's
handles, competitors, or contact info from search results that also
mention similarly-named or same-industry entities.

✅ **RAG/agent pipelines** extracting a structured fact about one named
entity from retrieval results that cover more than one entity — multi-tenant
support bots are the classic case.

⚠️ **KYC/due-diligence tooling** — real pain (name-collision false positives
in sanctions screening are notorious), but enterprise entity-resolution
platforms already exist here. This is a free, code-level first-pass gate,
not a replacement for them.

❌ **Not this**: entity resolution against a known knowledge base (deduping
customers, linking mentions to Wikidata). That's classical entity linking
(BLINK, REL) and it'll beat a substring-anchor check every time the entity
has a KB entry. entitygate exists for the opposite case — **small, unlisted,
not-yet-famous entities with no knowledge base to check against**, which is
most real businesses, and exactly who groundedness checks quietly fail.

---

## How it works

Three gates, in order, any one failing rejects the candidate:

1. **Shape** (optional) — does this even look like a real instance of what
   you're looking for (a profile URL, not a post link)?
2. **Verbatim** — does this candidate literally appear in the source text?
3. **Entity anchor match** (the actual point) — does the entity's own
   distinctive name-token occur inside the candidate?

```python
from entitygate import verify_claim

result = verify_claim(
    candidate="apollohospitals",
    entity="Kauvery Hospital",
    source_text="Apollo Hospitals official page: instagram.com/apollohospitals",
)
result.verified  # False — real handle, real text, wrong hospital
result.reason    # "no_entity_match"
```

Zero dependencies. Zero network calls. Zero LLM calls. It's a function, not
a service.

---

## Known limitations — disclosed, not buried in an appendix

- **Category/industry conflicts aren't caught.** `Sundaram Finance` and
  `Sundaram Residency` share a distinctive brand word across unrelated
  industries (financing vs. hospitality) — `matches_entity` incorrectly
  accepts this pair today. Needs a complementary category-conflict check.
  On the roadmap, not yet built.
- **This is a heuristic, generalized from real production fixes — not a
  formal proof.** It will have edge cases. Two of its six benchmark cases
  prove it already does.
- **The benchmark corpus is six real cases, not sixty.** Big enough to
  demonstrate the failure mode exists and is reproducible. Not big enough
  to report a catch rate with a straight face — a sample this small has a
  95% confidence interval wide enough to be meaningless as a percentage.
  Existence proof, not a statistic. More cases is the first roadmap item.

---

## Where this came from

Built inside 7th Sense, a real company-intelligence SaaS resolving client +
competitor social handles, contact info, and competitor lists from Google's
AI Overview and organic search results. `matches_entity`'s anchor rule is
the exact fix that shipped there after `timedical1` and a second real
collision (Kauvery Hospital vs. Apollo Hospitals, bridged by the shared word
"Hospital") were found live in production. This repo is that logic,
generalized, with the receipts.

## Roadmap

- [ ] Category/industry-conflict check (close the Sundaram-class gap)
- [ ] Bigger benchmark corpus (needs real API spend — tracked, not done)
- [ ] Real NLI entailment model as the faithfulness baseline, not just an LLM-as-judge prompt

## License

MIT.
