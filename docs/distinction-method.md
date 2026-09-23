# From distinction to usefulness

LAVREA's job is to discover the strongest case the evidence supports, preserve it, and make it useful to people who need the work. The unit is not an adjective or a repository. It is a **claim, its proof, the capability it demonstrates, and the problem that capability can address**.

## The positioning thesis

The working thesis is **human intent into executable, inspectable systems and expressive experiences**. It connects language, formalization, orchestration, implementation, verification and creative practice. It is an editorial synthesis to develop and test, not a new population percentile.

The public presentation has three depths: a clear headline; a small selection of relevant accomplishments; then sources, dates and limits. Precision should make the accomplishment durable, not hide it under disclaimers.

## What is implemented

`evidence/2026-09-22-distinction-atlas.json` contains nine claim families, twelve sources, four audience pathways and six discovery lanes. `scripts/build_distinction_atlas.py` checks source-reference integrity, URL structure and claim structure, verifies the unchanged canonical evidence digest, excludes restricted claims and unverified leads, and renders audience-specific Markdown. It does not judge the truth of prose, fetch new sources or initiate background work.

```bash
python scripts/build_distinction_atlas.py --output DISTINCTIONS.md
python scripts/build_distinction_atlas.py --check
python scripts/build_distinction_atlas.py --audience applied-ai
python scripts/build_distinction_atlas.py --audience creative-technology
python scripts/build_distinction_atlas.py --audience learning-design
python scripts/build_distinction_atlas.py --audience research
python -m unittest discover -s tests -p 'test_distinction_atlas.py' -v
```

The default public report is committed as `DISTINCTIONS.md`. CI verifies deterministic regeneration and tests the new code. Those checks demonstrate structural integrity, not external validation of every source or a successful real-world outcome.

## Discovery that increases value

Start with source-bearing traces: an accepted upstream change, credited publication, released artwork, client delivery, learner outcome, deployment receipt, independent use, or an unexpected connection between these. Identify Anthony's role and separate original design, maintained/adapted work, inherited components and agent assistance.

Recover primary evidence before turning a lead into a headline. An old resume can point to analytics or credits but does not independently establish them. Do not erase a previously evidenced achievement because a new read fails: retain the dated observation and report the read failure separately.

Classify what is actually established: measured comparison, external acceptance, inspected implementation, independent credit, published artifact, or research lead. These are different kinds of evidence, not a hierarchy of human worth. A release credit can be the relevant proof for an artistic collaboration even when it says nothing about engineering rank.

For a promising connection, ask who has the corresponding problem. Produce a small proof object that lets that person inspect the claim: a reproducer and accepted patch; source language plus a structured model; an artwork plus its instrument; an onboarding exercise plus a rubric. Measure outcomes against a baseline rather than simply adding more portfolio entries.

## The outward-to-inward comparison

Compare the work with the closest alternatives: how do other builders solve the same problem, where do their methods fit better, and where does this implementation add something useful? Capture the relevant difference, not a global claim of superiority. Reuse or simplify when that improves the work. Do not multiply unrelated percentile estimates to invent a one-in-a-million identity, or infer quality from commit volume.

Keep historical evidence append-only. A corrected interpretation needs an explicit explanation; a new observation gets a dated record. A true performance comparison must use a defined metric, matched population and period. Artistic judgment and research originality need their own stated criteria rather than an imported GitHub score.

## Publication and privacy

A public repository is not a private archive. Never commit private client correspondence, student records, personal circumstances, secrets or proprietary implementation details and assume a `restricted` label protects them. Keep that material outside this repository; publish only approved excerpts or aggregate results. The renderer's visibility checks are an additional safeguard, not a confidentiality system.

Preserve the fixed-window push ranking and the separately attributed recruiter Python finding. Preserve the creative identity as well as the engineering practice. Do not reduce Anthony to a teacher transitioning into engineering, and do not erase his language, educational and artistic work to make him fit a conventional technical profile.

## Evidence still to recover

The six discovery lanes cover learning outcomes, artistic reception, client/institutional value, research originality, external adoption and additional matched-cohort comparisons. They are questions, not promises that every investigation will yield a new distinction. The next improvement should either add useful proof, clarify the best audience, improve an actual outcome, or simplify the presentation. More claims are not automatically more value.
