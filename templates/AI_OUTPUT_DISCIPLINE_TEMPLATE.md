# AI-Generated Output Discipline — template

Read `FRAMEWORK.md` §III.10 first for how this fits the rest of the
framework (why it's gated, what it borrows from III.8/III.9/IV.3); this file
is the concrete starting kit — rationale, prompt skeletons, and checklists.
Copy it into your project as `docs/design/AI_OUTPUT_DISCIPLINE.md` and adapt
the bracketed sections to your product.

Generalized from a public write-up on AI-assisted design workflows (Anshu
Chimala, via *Lenny's Newsletter*, "How to turn your AI into a world-class
designer," Sept 2026). The techniques below are stripped of any specific
model/vendor names — this framework is agnostic to which agent or model runs
each role — and reordered around the three problems they actually solve:
generic defaults, self-review blindness, and over-addition.

## Why this exists

Language models are next-token predictors: at each decision point in
generating an open-ended artifact, the model fills in whatever is
statistically most likely to satisfy the average reader. That produces safe,
broadly acceptable output — and, for anything meant to feel distinctive,
"design-by-committee" results. The source material puts it plainly:

> "Whenever it needs to make a design decision—what colors to use, or how to
> arrange elements—the model fills in the tokens it thinks are most likely
> to please everyone. As a result, the design usually ends up being
> repetitive and bland... Great design is exactly the opposite of what an
> LLM does naturally, which is to make the most predictable choice at every
> step."

Two things follow from this, and they're the spine of §III.10:

1. **You can't fix it by asking for creativity.** Asking a model to "be
   random" or "be unique" still runs through the same most-likely-token
   process — it produces its most-likely *idea* of randomness, which turns
   out to be just as repeatable as its default:
   > "The results are different from before, but they're still not varied.
   > The model always uses the same color scheme, structure, and even the
   > same awkward pottery metaphors. It's predicting tokens that sound
   > random but aren't actually random... If we want variety, we have to
   > bring it from outside the model."
2. **You can't fix it by asking the model to grade its own homework either.**
   A model reviewing its own prior output is anchored to the choices and
   rationale it already committed to:
   > "Simply asking our agent to look at the design and improve it won't
   > work, because the agent isn't objective: it reviews its own code, past
   > decisions, and previous rationale. AI can't easily zoom out, look at
   > the big picture, and 'think different.'"

Everything below is process built around those two constraints, plus a third
pattern that shows up independently at delivery time: models reliably add
decorative or explanatory elements and rarely remove them without being
told to.

## Stage 1 — Push off the default (before the first draft)

Pick one of two techniques, applied *before* work starts, not as a later
correction:

**External-entropy seeding.** Have the agent generate an artifact outside
its own token-prediction loop (a random alphanumeric string, a timestamp, a
dice roll) and derive creative direction — palette, structure, tone — from
patterns in that artifact, without revealing it in the final output. This
works because the entropy genuinely comes from outside the model, unlike
asking it to "act random":

> "We make the AI generate a random string and use it as design inspiration.
> That way, the model is truly making different decisions each time...
> These designs are one-of-a-kind; no two runs ever produce the same
> result."

**Concrete reference anchoring.** Supply a specific, vivid creative
reference — a genre, an era, a physical object, an unrelated discipline —
and ask the model to reinterpret the mission through that lens, rather than
inventing a direction unprompted:

> "The best way to find a unique idea is by bringing your own taste into the
> equation. You first imagine the inspiration—a video game, an interior
> design trend, an art installation—and describe how you'd like that
> inspiration to influence the AI's outputs."

If you need the reference itself, ask for a broad, shallow list first
("go broad, not deep"), react to what resonates, then have the model sharpen
just that one direction — don't ship the first list verbatim, since anyone
else asking the same question gets the same list.

## Stage 2 — Critic Loop (deepen the direction)

Prompt skeleton — adapt the bracketed parts, keep the shape:

```
I want you to improve [this artifact]. Use a separate critic agent/session
to decide what to focus on.

At each iteration:
1. Capture the current output as a fixed artifact (screenshot, rendered
   text, exported file) — not source, not implementation notes.
2. Invoke the critic in a FRESH context: give it only the artifact, never
   the process, prior rationale, or earlier critiques.
3. Ask the critic to name the aesthetic/intent the artifact is going for,
   imagine how a top practitioner in that space would execute it, and list
   the biggest concrete gaps.
4. Have the critic score the artifact against that bar on a fixed scale.

Critic guidance:
- Evaluate both overall structure/composition and fine detail.
- Flag anything that reads as overdone, excessive, or a known
  [this project's] AI-output tell (see checklist below), and penalize it.
- Give tight, specific feedback — no vague prose.
- Be opinionated. Don't default to the safest option.

Stop when the critic independently scores [target, e.g. 9/10] or higher, on
[target max iterations, e.g. 3] iterations. Don't tell the critic the target
score — keep its scoring criteria objective. Use the identical critic prompt
every iteration.
```

Rubric quality determines whether this loop actually converges. From worst
to best:

- **Bad:** "Judge if this looks good, not AI-generated." Too subjective;
  results vary run to run.
- **OK:** "Review the intended aesthetic, imagine how a top practitioner
  would execute it, judge this against that bar." Mushy but gives a
  consistent frame.
- **Great:** "Here are N reference examples and 1 draft of ours. Rank them
  by polish and taste." Concrete, comparative, and gives the critic a
  visual/textual baseline instead of an abstract standard. Provide
  reference examples as a baseline/moodboard, not a copy target.

Set the stopping condition *before* the loop starts, and bound the iteration
count — otherwise the critic may never be satisfied and the implementing
agent burns budget indefinitely chasing it (the same two-attempt-rule logic
as II.3, applied here as an iteration cap instead of an escalation trigger).
Prefer a stronger/more expensive model for the critic role — it runs
infrequently and the judgment call matters — and a cheaper model for the
implementer, provided it's still capable of executing a stated direction
competently. Don't go so cheap the implementer can't follow the brief.

## Stage 3 — Delivery checklist (before shipping)

Run all four before marking a design-facing mission complete:

- [ ] **Subtraction pass.** For every element in the artifact, ask "what
  does this add — and does the artifact still work if it's removed?" AI
  output tends to accumulate decoration and explanation it was never asked
  for:
  > "AI loves to add more, but it rarely takes away... Look over your design
  > and ask yourself what really needs to be there. Often, putting less on
  > the screen communicates more."
  Cutting effective, unprompted additions (glow effects, redundant labels,
  custom components that reimplement a platform default worse) is normal
  and expected, not a sign the first draft failed.
- [ ] **Tells checklist.** Maintain a short, living list of *this project's*
  recognizable AI-output patterns below and check new output against it.
  Don't ban the patterns outright — a blanket ban just pushes the model
  toward new, equally mannered substitutes; instead, prompt for a deliberate
  alternative on the specific instance and compare:

  | Pattern observed | Where it showed up | Alternative tried | Kept / reverted |
  |---|---|---|---|
  | *(e.g. purple gradient CTA background)* | | | |
  | | | | |

- [ ] **Richer media before cheaper primitives.** If the mission calls for
  visual or motion richness, check whether the agent reached for generated
  imagery/video/audio or settled for the cheapest code-only stand-in
  (gradients, basic shapes, CSS-only motion) by default. The latter is a
  strong AI-output tell on its own; prompt explicitly for the richer option
  if the mission's quality bar calls for it.
- [ ] **Human copy edit.** Every line of user-facing copy the model wrote
  gets read and, where needed, rewritten by a human before ship. Treat
  generated copy as structural placeholder, not final text:
  > "Think of AI-generated copy the way designers think of 'Lorem ipsum'
  > text: it's there to help you visualize the structure, but it's a
  > placeholder that needs to be rewritten."

## Adopting this into a project

1. Copy this file to `docs/design/AI_OUTPUT_DISCIPLINE.md`, filling in the
   tells checklist as you observe your own project's recurring patterns —
   it starts empty and grows from real review sessions, not a generic list
   borrowed from elsewhere.
2. Fold a pointer to it into `AGENTS.md`/`CLAUDE.md` so any agent picks it
   up before starting a mission with a user-facing creative surface.
3. Reference `FRAMEWORK.md` §III.10 from any mission packet (§III.5) whose
   scope includes UI, visual design, or user-facing copy.
