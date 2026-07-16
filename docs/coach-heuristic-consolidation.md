# Coach heuristic consolidation recommendation (#30)

**Status:** Spike complete. Recommendation: **phased consolidation**, not a big-bang rewrite.  
**Date:** 2026-07-16  
**Related:** Epic #26, follow-up implementation issue (filed from this doc).

## Verdict

Treat `shared/coach-rules/*.json` as the **sole source of truth for detect/repair grammar rules**, and get **Swift** onto that engine first. Do **not** force CEFR salvage, hallucination detection, or register-conflict into per-rule `detect` entries. Those stay as shared policy code (Python reference → optional Swift codegen later).

Python training already runs JSON via `training/coach_rules.py`. Web/Firebase already sync from the same JSON. **Swift is the critical gap:** `ParlanceSLMFeedbackValidator.swift` and `FeedbackSanitizer.swift` still hardcode a small regex subset and duplicate sanitizer algorithms.

## Current overlap

| Category | JSON (`shared/coach-rules/`) | Python (`coach_rules` + `parlance_slm_validate`) | Swift validator | `FeedbackSanitizer` |
|----------|------------------------------|--------------------------------------------------|-----------------|---------------------|
| Detect/repair grammar | Full (ES ~20, FR ~18) | Full via JSON | Partial hardcoded (~5 ES, ~2 FR) | Partial hardcoded |
| CEFR plausibility / salvage | Metadata only | Full | Full | Plausibility filter only |
| Hallucination | — | Yes (+ verb lemmas) | Yes | Yes |
| Register conflict | FR in-sentence rule only | Yes | ES mainly | ES + FR |
| Excellent / invent-error heuristics | — | Yes | Yes | Partial |

Sync today: `scripts/sync_coach_rules.sh` → web JS + Firebase. **No Swift sync.**

## What moves to JSON easily

- Remaining detect/repair rules (stop hand-porting regex into Swift)
- Pack helpers already in JSON (`feminine_nouns`, mention strings)
- Regression corpora as the contract for any new runtime

## What should stay code (or a separate policy schema)

- CEFR salvage / confident inference (`_coach_salvage_assessed_level`, Swift mirrors)
- Hallucination with lemma tables (`find_hallucinated_terms`)
- Register conflict across sentence vs correction vs `register` field
- Excellent-path / model-invented-error / tip heuristics

Encoding those as rule `detect` patterns is the wrong abstraction and would create schema creep.

## Phased plan

### Phase 1 — Swift CoachRulesEngine (recommended next, ~M / 2–3 weeks)

1. Bundle `shared/coach-rules/{es,fr}.json` in the iOS target (or generate a Swift resource at build time).
2. Implement `CoachRulesEngine` mirroring `training/coach_rules.py` / `Parlance/web/coach-rules-engine.js` (detect + repair + feminine-noun helper).
3. Point `knownSpanishErrorFeedback` / French known-error paths in `ParlanceSLMFeedbackValidator` and `FeedbackSanitizer` at the engine; delete hardcoded regex blocks.
4. CI: run the same `regression_{es,fr}.jsonl` cases against the Swift engine (or a shared fixture dump) so NSRegularExpression vs Python `re` drift fails loudly.

**Risks:** backref / flag differences between Python `re` and `NSRegularExpression`; on-device performance; accidental behavior change on edge cases that golden regression does not cover.

### Phase 2 — One Swift sanitizer path (~M)

Collapse cloud `FeedbackSanitizer` and on-device validator onto the same ordering: known errors → hallucination → register → CEFR filter → tips. Align with Python `sanitize_feedback` + `merge_with_ai`.

### Phase 3 — Optional shared policies (~L)

Introduce `shared/coach-policies/` (YAML/JSON) for CEFR thresholds, hallucination field lists, register marker sets; codegen Swift from a Python reference. Keep excellent/heuristic fallbacks in code.

## Effort summary

| Scope | Effort | Do now? |
|-------|--------|---------|
| Phase 1 Swift JSON engine | M | **Yes** |
| Phase 2 unify Swift sanitizers | M | After Phase 1 |
| Phase 3 policy codegen | L | Only before English on-device (#11) multiplies the copies again |
| Full single-schema for everything | L+ | **No** |

## Why this matters for English (#11)

An on-device English model would otherwise need a third hand-ported validator. Phase 1 means English rules (when they exist) land as JSON + tests, not another 1.6k-line Swift fork.

## Out of scope for the spike

No production code changes in this recommendation. Implementation is tracked in the follow-up GitHub issue.
