# Course text (Quarto book)

The written course for the FISL labs: markdown/Quarto sources that render to
the course site/book.

```sh
# https://quarto.org/docs/get-started/
quarto render course/     # output in course/_book/
quarto preview course/    # live-reload authoring
```

Conventions:

- One `labs/lab-NN-*.qmd` chapter per lab, following **scenario before
  theory** (ARCHITECTURE.md §3): encounter the system → measure → intervene
  → then the formal concept → debrief.
- Every numeric claim in a chapter should be reproducible from a committed
  scenario + (where scripted) a reference solution under
  `scenarios/.../solutions/`; cite the run report values, not folklore.
- Instructor-only material (solution discussion, expected numbers) lives in
  clearly marked *Instructor notes* sections until the course tooling gains
  a proper split.
- Register new chapters in `_quarto.yml`.
