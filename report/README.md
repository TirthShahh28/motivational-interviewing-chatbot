# Capstone Final Report (LaTeX)

This directory contains the LaTeX source for the M.Eng. capstone final
report. It compiles to a single PDF and is structured to match the ENGR 5315
final-report outline.

## Layout

```
report/
  main.tex              Master file -- compile this
  references.bib        Bibliography (IEEEtran style)
  sections/
    01_abstract.tex
    02_introduction.tex
    03_literature.tex
    04_methodology.tex
    05_analysis.tex
    06_experiments.tex
    07_results.tex
    08_conclusions.tex
    09_future_work.tex
  figures/              PNGs referenced from sections/
```

## How to compile

You need a TeX distribution (TeX Live, MiKTeX, or use Overleaf). The build is
the standard four-pass dance because of the bibliography and `\Cref` references:

```bash
cd report
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Output: `main.pdf`.

### Easier: Overleaf

Upload the entire `report/` folder to a new Overleaf project, set
`main.tex` as the main document, and Overleaf will run the four passes
automatically. Compiler: pdfLaTeX. Bibliography: BibTeX (already declared in
`main.tex`).

### Easier on Windows: latexmk (if installed with TeX Live / MiKTeX)

```bash
cd report
latexmk -pdf main.tex
```

`latexmk` runs the right number of passes automatically.

## Section-to-rubric mapping

The ENGR 5315 final-report outline asks for:

| Rubric section            | Source file                       |
| ------------------------- | --------------------------------- |
| Abstract                  | `sections/01_abstract.tex`        |
| Introduction & Background | `sections/02_introduction.tex`    |
| Survey of Related Lit.    | `sections/03_literature.tex`      |
| Methodology               | `sections/04_methodology.tex`     |
| Analysis                  | `sections/05_analysis.tex`        |
| Experimental data         | `sections/06_experiments.tex`     |
| Results                   | `sections/07_results.tex`         |
| Conclusions               | `sections/08_conclusions.tex`     |
| Future work               | `sections/09_future_work.tex`     |
| References                | `references.bib`                  |

## Figures

`figures/` contains the six pre-generated evaluation visuals copied from
`docs/visuals/`:

- `01_model_comparison.png` -- per-dimension bar chart across configs
- `02_radar_chart.png` -- radar plot of the five MI dimensions
- `03_improvement_over_base.png` -- delta of v2_rag over base, per dimension
- `04_technique_distribution.png` -- detected MI techniques per config
- `05_overall_average.png` -- overall mean score per config
- `06_heatmap.png` -- config x dimension heatmap

To regenerate them after rerunning the eval, run:

```bash
python scripts/generate_visuals.py
cp docs/visuals/*.png report/figures/
```

## Notes

- The pipeline diagram in `04_methodology.tex` is drawn in TikZ -- it is the
  LaTeX-native equivalent of the Mermaid flowchart in the project README.
  Compiles cleanly with stock pdfLaTeX (no extra packages beyond those already
  loaded in `main.tex`).
- The bibliography uses `IEEEtran` style for citation numbering. If your
  professor wants a different style (ACM, APA), change the line
  `\bibliographystyle{IEEEtran}` in `main.tex`.
- Line spacing is `\onehalfspacing`; set in `main.tex` via the `setspace`
  package. Switch to `\doublespacing` if a stricter format is required.
