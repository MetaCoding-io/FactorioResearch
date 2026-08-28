# The Province — a Narrative Companion Daydream

**Status:** daydream (first written 2026-08-28), companion to
`VSM_EXPLORATION.md`. Not plan of record; changes nothing about
Course I/II or the gates. This memo explores a *second* format for the
same material: a long-form fictional narrative — a business novel in
the lineage of *The Goal* — with play-along Factorio scenarios, set in
a remote province being planned, built, and operated under a socialist
planning committee.

---

## 1. The pitch and its lineage

> A delegation is appointed by a national planning committee to plan,
> build, and operate a new set of facilities in a remote province:
> modernizing electrical production and expanding agriculture, within
> ecological constraints and standing plan commitments. Over three
> years they learn — by failure, measurement, and eventually design —
> what it takes for the province to become *viable*: able to keep its
> commitments in a changing world without being rescued.
>
> The reader can read it as a novel, watch each chapter's events as
> recorded runs, or load each chapter's situation in Factorio and live
> it.

The format has a distinguished genealogy, and this project sits at an
odd advantage inside it:

- **Goldratt, *The Goal*** — the original teaching novel, and it is
  *literally a Factory Physics novel*: bottlenecks, WIP, statistical
  fluctuations, the herd hike. Course I already teaches its physics;
  Hopp & Spearman is in part a rigorous reply to it.
- **Kim et al., *The Phoenix Project*** — proof that the format
  transplants to a new domain (DevOps) and can carry a framework (the
  Three Ways) to people who will never read the textbook.
- **Spufford, *Red Plenty*** — proof that *planned-economy economics
  itself* can be gripping fiction: linear programming, shadow prices,
  and Kantorovich rendered as human drama. The closest model for this
  book's setting and tone.
- **Medina, *Cybernetic Revolutionaries*** — the history: Beer,
  Allende's Chile, Cybersyn. Reads like a thriller because it was one.

The lineage has a missing third volume: *The Goal* taught factory
physics, *The Phoenix Project* taught flow in IT — nobody has written
the novel of **organizational cybernetics**. Beer's own books are
oracular monologues; the VSM has never been *dramatized*. That is the
open slot this book would occupy.

And this project holds one card none of those authors had: **a
simulator underneath the fiction** (§4).

---

## 2. Why a narrative at all

The variants gallery (`VSM_EXPLORATION.md` §4) and a novel are not two
pitches for the same thing; they are complements, and the seam between
them is exactly where the gallery is honest about being weak:

- **The gallery's S5 is thin by construction** — scripted policy, a
  declared constant. The memo says so. But S5 — contested identity,
  renegotiated purpose, the felt weight of arbitrating today against
  tomorrow — is precisely what *fiction is for*. Characters can carry
  what circuits cannot. The novel is where thin-S5 becomes thick.
- **Labs teach those who arrive; stories recruit.** A novel reaches
  readers who will never install Factorio — and quietly funnels the
  ones who would. Every chapter's "load this and try" is an on-ramp to
  the course platform.
- **Motivation.** The courses are scrupulous about evidence and
  deliberately dry about stakes. A narrative supplies the thing a lab
  cannot: a reason to care whether the province makes the winter.

One more alignment, almost too good: the repo's standing ethic —
objectives without scores, physical quantities before money, the §21
"cybernetic tradition of managing real operational variables rather
than accounting abstractions" — is, historically, *the planned-economy
information problem*. In a market novel, "we measure flows and
commitments, not profit" is a stylistic choice needing defense. In
this setting it is simply how the world works. **The setting makes the
course's methodology diegetic.** The plan targets, the physical
balances, the absence of a price signal, the committee asking for "the
number" — the fiction's furniture *is* the course's measurement
discipline.

On the politics: the socialist-planning frame is apt for honest
structural reasons (Cybersyn and GOELRO are the historical
anchors; non-market coordination makes plan commitments, physical
indicators, and the autonomy-versus-cohesion bargain natural plot
material, and Beer's actual argument to Allende — neither centralized
command nor abdication, but designed autonomy — *is the book's thesis
conflict*). The obligation that follows: the book is neither agitprop
nor Cold-War caricature. The politics is the setting; the subject is
viability. *Red Plenty* is the proof this tone is achievable — humane,
ironic, technically serious, tragic where the history was.

---

## 3. Setting and cast

**The Province** (working name; a secondary world with recognizable
1970s-adjacent technology — radio, telex, rail — rather than a named
real country; see open question 3). Remote, resource-rich,
under-electrified, agriculturally strained. The delegation's brief
from the committee: modernize power generation, expand and mechanize
agriculture, honor the province's delivery commitments to the national
plan, and stay inside declared ecological ceilings — watershed,
airshed, land.

The cast is the org chart, and the org chart is the model. Characters
*are* subsystems, which is how the book teaches the VSM without ever
drawing the five-box diagram until late:

| Character (role) | Function carried |
|---|---|
| **The Coordinator** (protagonist; engineer, reluctantly appointed) | The learner; eventually the designer of the metasystem |
| **District managers** (power, agriculture, workshops, logistics) | S1s — each locally sensible, each with its own environment |
| **The Dispatcher** (rail & grid scheduling, standards, conventions) | S2 — anti-oscillation made human |
| **The Operations Chief** (inside-and-now; the resource bargain) | S3 — and one half of the Act III war |
| **The Development Chief** (surveys, prospecting, next year's province) | S4 — the other half |
| **The Veteran Operator** (walks the lines, trusts no dashboard) | S3\* — the audit channel; ground truth on legs |
| **The Ecologist** (holds the ceilings; the constraint that doesn't negotiate) | The environment, given a voice and a veto |
| **The Committee Liaison** (the plan above; arrives quarterly) | Recursion upward — the province is an S1 of the nation |
| **The Radio Operator** (night shift; the one who hears it first) | The algedonic channel |
| **The Old Cyberneticist** (the Jonah/Erik figure: a half-retired telephone-exchange engineer, exiled to the province years ago) | The mentor who asks questions and refuses to answer them |

The Jonah archetype is load-bearing in this genre and worth doing
differently: not a visiting guru but someone already *in* the
province, formed by switching networks and war logistics, who has read
Ashby and never once says "cybernetics" until the Coordinator has
earned each idea in scars first. Vocabulary always arrives *after*
experience — the same pedagogical principle as the courses
(`ARCHITECTURE.md` §3), now as a rule of dialogue.

---

## 4. The rule that makes it different: sim-constrained fiction

The card no predecessor held. *The Goal*'s plant exists only in prose;
its numbers are illustrative. This book's province can *actually
exist*, and that permits a discipline worth stating as a law:

> **Nothing happens in the story that cannot happen in the save
> file.**

Every operational plot beat — the deadlock, the death spiral, the
depletion cliff, the storm — corresponds to a FISL scenario in which
that event *actually occurs*, with the telemetry to prove it. Which
gives the writing process a method, and it is the Course I discipline
extended to fiction: **simulated before authored.** Build the
chapter's situation, run it, watch what the system really does, write
*that*. Factorio becomes the continuity editor; the plot cannot cheat
the physics, because the physics is checkable. When the Dispatcher
says the queue doubled, the queue doubled — the reader can go count.

Three reading tiers fall out of the same artifacts:

1. **Read** — the novel stands alone (it must; see §7).
2. **Watch** — each chapter's run, recorded; the province's actual
   map, the actual jam, the actual recovery.
3. **Play** — load the chapter scenario: the province *as of this
   chapter*, plus the chapter's open question. The platform's whole
   reason for existing (`RESEARCH_NOTES.md` §9 — reproducible
   scenarios, not hand-edited saves) is what makes "the save file as
   of chapter 12" a distributable, hashable object rather than a
   maintenance nightmare.

The play-along scenarios are not new engineering: they are the course
scenarios wearing narrative clothes — in the best case literally the
same packages, cross-referenced ("Chapter 9 is Lab II-2's situation;
the lab is the debrief of the chapter").

---

## 5. Three acts = three courses

The arc of the book is the arc of the curriculum, which means one
novel can serve as the narrative companion to *all three* courses —
each act's chapters keyed to labs the way interludes are keyed now.

**Act I — The Plan** (Course I: deterministic physics). The delegation
arrives, surveys, builds. The comedy and tragedy of plan arithmetic
meeting line behavior.

1. *Arrival.* The brief, the map, the targets. First act of
   measurement: what does the province actually produce today?
   (Lab 0.)
2. *The Plan's Arithmetic.* First power line up; nameplate capacity
   versus what the line delivers; the plan assumed the former.
   (Lab 1.)
3. *The Slowest Machine.* The workshop supplying the whole build has
   one saturated station nobody notices, because it isn't the biggest
   or loudest. An open homage to Herbie. (Lab 2.)
4. *The Auditor Counts.* Material everywhere, completions nowhere; a
   committee auditor walks the yards counting WIP, and the Coordinator
   discovers the law relating what the auditor counted to the lead
   times the districts are ashamed of. (Lab 3.)
5. *The Expediter.* The trunk line starves and blocks in waves; a
   heroic expediter makes it worse; pull discipline arrives as an
   affront to everyone's work ethic. (Labs 4–5.)
6. *The Warehouse of Victory* (Act I climax). The annual target is
   met — by overproducing the measurable and starving the needed. The
   celebration scene and the warehouse of unusable surplus, in the
   same chapter. POSIWID, unnamed. (Lab 6; objectives without
   scores as dramatic irony.)

**Act II — The Weather** (Course II: variability and buffering). The
second year: the world stops being deterministic and the plan's
assumptions rot.

7. *The Same Province, Twice.* Two seasons, same plan, different
   numbers; the Liaison demands "the number" and the Coordinator has
   only a distribution. The death of the point estimate as a scene at
   a formal hearing. (II-0.)
8. *The Imported Turbine.* The one machine that cannot fail, fails;
   spare-parts politics; availability arithmetic learned in a machine
   hall at 3 a.m. (II-1.)
9. *Everything at Full.* To catch up, the province runs everything
   flat out — and waits explode. The utilization cliff experienced as
   a province-wide slow-motion panic. (II-2.)
10. *Harvest.* Agriculture arrives as a physics problem: seasonality,
    perishability, wobble upstream of everything. Where the
    variability sits matters more than how much. (II-3.)
11. *The Buffer Hearing* (the chapter the whole act aims at). Three
    factions before the committee: grain stores (**inventory** — but
    stockpiling reads as hoarding, and hoarding is a crime), spare
    generators (**capacity** — investment the plan won't grant), and
    rationing-by-queue (**time** — the buffer the populace pays).
    The Buffering Law as *political theater*: the three currencies are
    three constituencies, and "no buffer" is not on the ballot.
    (II-4; `ARCHITECTURE.md` §21.)
12. *The Storm* (Act II climax). Winter storm plus the ecological
    ceiling: the push-planned districts collapse and the one
    pull-disciplined district degrades gracefully; catch-up production
    would breach the airshed ceiling the Ecologist holds. First
    appearance of a cost that is a *constraint*, not a price.
    (II-5, II-6.)

**Act III — The Organization** (Course III / the variants gallery).
The third year: the committee's attention moves to a newer province.
No more rescues. The province must become viable — and the gallery's
variants (`VSM_EXPLORATION.md` §4) become the plot beats.

13. *The Mob of Districts.* Autonomy without coordination: the
    death spiral and the deadlock, districts individually healthy,
    collectively dying. (V0 → the Dispatcher's chapter; S2.)
14. *The Bargain and the Audit.* The resource bargain formalized; a
    district's honest-but-miscalibrated reporting caught only by the
    Veteran Operator walking the line. Dashboards versus census.
    (V2; S3/S3\*.)
15. *The Two Captains.* Operations and Development at open war over
    the same iron: expand now and fail deliveries, or deliver now and
    die when the ore runs out. Discovered almost too late (the
    depletion cliff), resolved not by a winner but by the province
    writing its *constitution* — the standing arbitration. S5 earned
    as the peace treaty. (V3/V4.)
16. *The Ops Room.* They build it: the Cybersyn homage — indicator
    boards from the triad (actuality, capability, potentiality),
    filtering by exception, an algedonic drill that everyone
    resents... until the night the Radio Operator's alarm jumps three
    levels of hierarchy and the flood response starts eleven minutes
    earlier than it otherwise would. The telemetry shows the eleven
    minutes. (V5.)
17. *The Visit* (coda). The Coordinator tours a single district and
    finds the whole model again in miniature — and then the Liaison
    arrives to review the province, which is itself one operational
    unit of the nation's model. Recursion seen twice in one chapter.
    The final scene is the renegotiation: the province presents not
    plan-fulfillment numbers but its *viability* — and asks for the
    autonomy that cohesion can afford. (V6; the recursion bargain;
    Beer's "designing freedom" as the closing note.)

---

## 6. What Factorio natively gives the story

The premise was chosen well for the engine — nearly every story
element has a native mechanic to be *true in*:

- **Electrification** — the power network is Factorio's most legible
  system: generation, load, brownouts, priority; the GOELRO-flavored
  plot is playable out of the box. The death spiral is native.
- **Ecological ceilings** — **pollution is a base-game mechanic** with
  sources, spread, and absorption; a watershed/airshed ceiling is a
  measurable, declarable constraint, not narrative hand-waving.
  (Biter response to pollution even gives ecology a *consequence*,
  used carefully.)
- **Depletion** — ore patches running out is native and is the S4 plot
  engine.
- **Rail, radar, circuits** — the Dispatcher's schedules, the
  Development Chief's surveys, and the entire Ops Room are buildable
  in-world; the algedonic channel is a programmable speaker.
- **Agriculture** — the stretch. Base game has no farming; options in
  ascending fidelity: (a) stylized — greenhouse-as-assembler recipes
  with seasonal supply schedules (Course II machinery does
  seasonality); (b) Space Age's agricultural mechanics with
  **spoilage** — which is almost indecently perfect for perishables
  (a time buffer that *rots* — the II-3/II-4 material dramatized by
  the engine itself) but buys an expansion dependency that
  `ARCHITECTURE.md` §23 says to avoid unless a scenario requires it;
  (c) a light content mod, which `fisl-factory-physics` already
  establishes the pattern for. Lean: (a) for the book's claims, note
  (b) as a tantalizing option to revisit.
- **Weather/harvest wobble** — not native; exactly what Course II's
  seeded streams are for. The storm of chapter 12 is a declared
  disturbance schedule, which means it is *reproducible* — every
  reader's storm is the same storm.

---

## 7. Honesty section

- **Didactic fiction is mostly bad.** The failure mode is a lecture
  wearing a trench coat. *The Goal* survives because its crises are
  *real system behavior* and its characters want things. The
  sim-constrained rule (§4) handles the first half mechanically —
  the plot literally cannot assert physics that doesn't happen — but
  nothing mechanical produces characters worth following. This is a
  craft project, and the repo's engineering discipline does not
  transfer to prose. It needs a writer's loop: drafts, readers,
  revision — the external-learner gate's literary cousin.
- **The book must stand alone.** If it only works as course marketing,
  it fails as both. Test: would someone who never opens Factorio
  finish it and press it on a colleague? *The Phoenix Project* passes
  that test; that is the bar.
- **The politics needs adult supervision.** §2's tone commitment,
  restated as a risk: the setting invites both romanticism and
  caricature, and the historical anchors (Cybersyn ended in a coup;
  Soviet planning ended how it ended) deserve the *Red Plenty*
  treatment — technically serious, humane, unsentimental. The book's
  argument is Beer's, not a manifesto: viability is about structure,
  and structure is a choice available to any polity honest enough to
  measure itself.
- **Scope gravity, narrative edition.** The book consumes scenarios;
  it must not *drive* engineering. If a chapter needs machinery no
  course needs, rewrite the chapter. (Suspected to bind rarely —
  §5's beats were all drawn from existing course/gallery material,
  which is the point.)
- **Sequencing reality.** Acts II and III lean on Course II/III
  machinery that doesn't exist yet. The book cannot outrun the
  laboratory it is constrained by — by design.

---

## 8. Cheapest possible spike

As with the gallery memo, there is a probe that costs almost nothing
and would teach almost everything:

> **Novelize one existing lab.** Take fp02 (the constraint) or fp03
> (Little's Law) — scenarios that exist *today* — and write chapter 3
> or 4 as a standalone short story (five to eight pages), with the
> existing scenario as its play-along and one recorded run as its
> "watch" tier. The Herbie chapter and the Auditor chapter are both
> sitting on finished machinery.

That spike tests the entire premise at once: does sim-constrained
prose read as story or as lab report with dialogue? Does the
play-along link land? It also produces a reusable artifact either
way — worst case, a narrative interlude for the existing course;
best case, chapter one of the missing third volume. And it respects
every gate: no new code, no course changes, one short story.

---

## 9. Open questions

1. **One book or serialized?** Chapters could ship with their courses
   (Act I alongside Course I's completion, etc.) and be bound later.
   Serialization matches the project's measured-before-authored
   cadence and de-risks the craft problem; a bound book is the
   stronger cultural object. Lean: serialize, bind later.
2. **Relationship to the variants gallery.** The gallery
   (`VSM_EXPLORATION.md`) is the *evidence*; the book is the
   *dramatization*; Act III's beats are the gallery's variants. If
   both proceed, the gallery is built first and the chapters are its
   write-ups in costume — measured before authored, again.
3. **Secondary world or historical fiction?** A named 1971 Chile or
   USSR buys resonance and buys every historian's quarrel; a
   *Red-Plenty*-adjacent secondary world (recognizable tech level,
   invented nation) keeps the physics honest and the politics
   breathable. Lean: secondary world, with the historical anchors
   honored in an afterword.
4. **Who writes it?** The genuinely open one. Sim-constrained fiction
   wants a tight loop between the scenario author and the prose
   author; whether that is one person, a pair, or prose drafted
   against run transcripts is undecided and decisive for feasibility.
5. **Videos.** The "watch" tier needs a production answer eventually
   (recorded headless runs with camera scripting? narrated
   playthroughs?); irrelevant until a chapter exists.
6. **Naming.** "The Province" is a placeholder doing double duty
   (the gallery memo uses it too — deliberately: same world, two
   formats). Book title candidates deferred until there's a book.
