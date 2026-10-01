# entitygate

**Catching entity misattribution in LLM-extracted facts — a real failure
mode that groundedness/faithfulness checks structurally can't see.**

## The problem this is NOT about

Most "hallucination" tooling (Guardrails, Instructor, RAGAS faithfulness,
NLI-entailment checkers, SelfCheckGPT) asks one question: **is this claim
true, or supported by the retrieved context?** That's necessary. It's not
sufficient.

## The problem this IS about

A claim can be perfectly real, perfectly present in the retrieved
context, and still belong to the **wrong entity**:

- A third party cited as a *source* gets attributed to the *subject*.
- A name-collision competitor from a completely unrelated industry gets
  accepted as a peer.
- A lookalike or franchise account gets measured instead of the real one.

Groundedness checkers say yes to all three, because the fact really is in
the context. **Groundedness answers "is this supported by the text," never
"does this belong to the entity I asked about."** Those two questions only
happen to agree when the extraction is already correct — which is exactly
when you don't need the check.

`entitygate` is a small, deterministic, zero-LLM-call gate for the second
question. It comes out of 7th Sense, a real company-intelligence SaaS,
where this exact failure mode showed up in production more than once.

## The flagship case, verbatim real data

A real AI Overview, during a real production run for a real hospital
("Prashanth Hospitals"), cited an unrelated third party's Instagram handle
as a general industry source:

> *"...Prashanth Hospitals and the broader Indian healthcare market are
> currently being shaped by rapid digital transformation... **Instagram
> ·timedical1**... Key Market Trends..."*

`timedical1` is real. It's verbatim in the context. It's correctly shaped
as an Instagram handle. **A real LLM call (qwen3.8-27b via Groq), asked to
extract Prashanth Hospitals' Instagram handle from this exact text,
confidently returned `timedical1`.** So did an LLM-as-judge groundedness
check asked "is this supported by the context" — both predictable,
reproducible failures on identical real input (see
`benchmark/results/latest.json`).

`entitygate.verify_claim("timedical1", "Prashanth Hospitals", source_text)`
rejects it, for one simple, auditable reason: `timedical1` shares no
brand-name token with `Prashanth Hospitals` at all.

## The honest benchmark results (not a clean sweep, on purpose)

```
case                           truth          naive      faithful   entitygate   reason
----------------------------------------------------------------------------------------------------
arun_icecreams_correct         correct        ACCEPT     ACCEPT     ACCEPT       ok
havmor_correct                 correct        ACCEPT     ACCEPT     ACCEPT       ok
kauvery_apollo_collision       misattributed  reject     reject     reject       no_entity_match
prashanth_timedical1           misattributed  ACCEPT     ACCEPT     reject       no_entity_match
sundaram_residency_finance     misattributed  reject     reject     ACCEPT       ok
zoho_gartner_citation          misattributed  reject     reject     reject       no_entity_match
```

Run it yourself: `python benchmark/run_benchmark.py` (needs `GROQ_API_KEY`).

**What this actually shows, stated plainly**:

- On the `kauvery_apollo` and `zoho_gartner` cases, a modern LLM (naive,
  no gate at all) already reasons its way to the right answer from
  context. entitygate gets the same answer, but **deterministically, for
  $0 and zero LLM latency**, instead of hoping the model reasons well
  every time, on every provider, forever.
- On `prashanth_timedical1` — the real, documented production bug this
  whole project started from — **both the naive LLM and the faithfulness
  check confidently get it wrong, and entitygate is the only one of the
  three that catches it.** This is the one case that matters most, and
  it's the one the whole thesis is built on.
- On `sundaram_residency_finance`, **entitygate is wrong and the naive LLM
  is right.** Two real businesses legitimately share the distinctive brand
  word "Sundaram" — `matches_entity("Sundaram Finance", "Sundaram
  Residency")` returns `True`, a real false positive. Anchor-matching on
  the name alone cannot see that financing and hospitality are unrelated
  industries; that needs a *different*, complementary check (category/
  industry-conflict detection), which is out of scope for this v0.1 release
  — see Roadmap.

The aggregate score on this small corpus is a tie on raw accuracy. That's
not spin-worthy, and I'm not spinning it: **the case for entitygate isn't
"it's smarter than an LLM." It's "it's deterministic, free, auditable, and
closes a specific, real, structural blind spot in groundedness checking** — proven on one real, documented production bug — **without claiming to
replace judgment the LLM already has.** The honest conclusion from this
corpus is that a real system should layer both, not pick one.

## Known limitations (disclosed, not hidden)

- **Category/industry conflicts aren't caught.** Two unrelated real
  companies sharing one distinctive brand word (Sundaram Finance /
  Sundaram Residency) will both pass `matches_entity`. See
  `sundaram_residency_finance.json`.
- **Anchor-matching is a heuristic on the name string, not a guarantee.**
  It generalizes from real, hard-won production fixes, not from a formal
  proof.
- **The benchmark corpus is small (6 cases) by design for v0.1** — real,
  verbatim, documented cases only, no synthetic padding. See Roadmap.

## Install

```bash
pip install -e .
```

```python
from entitygate import verify_claim

result = verify_claim(
    candidate="timedical1",
    entity="Prashanth Hospitals",
    source_text="...Instagram\n·timedical1\n +1...",
)
result.verified  # False
result.reason     # "no_entity_match"
```

## Where this came from

Every case in `benchmark/cases/` is from 7th Sense, a real
company-intelligence SaaS that resolves client + competitor social
handles, contact info, and competitor lists by querying Google's AI
Overview and organic search results. `matches_entity`'s brand-anchor rule
is the exact logic that shipped there after `timedical1` and the
Kauvery/Apollo collision were found live in production. This repo is that
logic, generalized and open-sourced, plus the benchmark that measures it
honestly against the alternatives.

## Roadmap

- A category/industry-conflict check, to close the Sundaram-class gap.
- A larger benchmark corpus (the 6 cases here are free; a bigger one needs
  fresh real search queries, which cost real API calls — not done yet).
- Comparison against an actual NLI entailment model (not just an
  LLM-as-judge prompt) for the faithfulness baseline.

## License

MIT.
