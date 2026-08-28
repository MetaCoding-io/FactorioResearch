# VSM Book

This folder contains the narrative/book strand that grew out of the Viable System Model exploration in FISL.

The core idea is a hopeful, sim-constrained teaching novel about a remote industrial province learning to become viable: able to maintain its commitments in a changing environment without continual rescue from above. The fictional story, the VSM experiments, and the reader's playable Factorio/FISL scenarios are intended to form one learning object while remaining useful independently.

## Start here

### [`NARRATIVE_DESIGN_BIBLE.md`](NARRATIVE_DESIGN_BIBLE.md)

**Canonical narrative concept document.** This is the current source of truth for the book's premise, tone, characters, diegetic Factorio/FISL laboratory, generative-machine relationship, story structure, creative rules, and open questions.

When later brainstorming conflicts with this document, update the bible deliberately rather than letting the concept drift across conversations.

### [`WORLD_DESIGN.md`](WORLD_DESIGN.md)

**Compact structural setting document.** Establishes the newly independent country's inherited-but-orphaned technical base, decentralized political project, worker takeovers, embargo pressure, dissent and destabilization, ecological commitments, revolutionary industrial-solarpunk direction, shared-world principle, and the role of Factorio and generative software.

It is intentionally not a lore bible: build only enough world to make the next human and technical decision real.

### [`SOCIAL_AND_CULTURAL_LIFE.md`](SOCIAL_AND_CULTURAL_LIFE.md)

**Lived-world and movement-culture document.** Develops what independence feels like in ordinary life and the emerging culture of committed supporters: revolutionary willingness, legitimacy's half-life, work and family disruptions, movement values and status markers, symbols, clothing, holidays, songs, food, humor, equality, internal cultural arguments, multilingual life, media, apprenticeship, diaspora, and generational change.

Its purpose is to make the country feel inhabited rather than merely administered.

## Foundational memos

### [`VSM_EXPLORATION.md`](VSM_EXPLORATION.md)

The **evidence / systems-design memo**. It develops the idea of viability variants: identical factory physics and disturbances with different organizational control structures, measured through FISL. It contains the V0–V6 gallery, viability metrics, methodological cautions, and the bridge from in-silico VSM experiments to later human organizational exercises.

### [`VSM_NARRATIVE.md`](VSM_NARRATIVE.md)

The **original narrative daydream**. It first develops *The Province* as a teaching novel in the lineage of *The Goal*, *The Phoenix Project*, *Red Plenty*, and the history of Cybersyn, with three acts aligned to the curriculum and a rule of simulated-before-authored fiction.

This memo is preserved as an origin document. Some of its assumptions have since evolved; the narrative bible and world-design documents record the current position.

## Relationship among the documents

```text
VSM_EXPLORATION.md
    scientific / experimental case
           |
           v
VSM_NARRATIVE.md
    original dramatization idea
           |
           v
NARRATIVE_DESIGN_BIBLE.md
    current canonical narrative design
           |
           +--> WORLD_DESIGN.md
           |       structural setting constraints
           |          |
           |          +--> SOCIAL_AND_CULTURAL_LIFE.md
           |                 lived transition + movement culture
           |
           +--> novel / serialized fiction
           +--> Coordinator's Factorio/FISL models
           +--> recorded runs / lab notes
           +--> reader play-along and counterfactuals
```

The novel should never be required reading for the laboratory, and Factorio/FISL should never be required to enjoy the novel. The strongest version of the project lets each medium reveal something the others cannot.

## Parent project anchors

The book remains downstream of the larger FactorioResearch/FISL methodology. Relevant parent documents live one directory up, including `ARCHITECTURE.md`, `RESEARCH_NOTES.md`, `COURSE_II_SCOPE.md`, ADRs, and runtime/measurement validation material.

The book must consume and dramatize trustworthy laboratory machinery; it must not pressure the research platform into narrative-only features.

## Working principle

> **Measured before authored. Experience before vocabulary. Models are never the territory.**
