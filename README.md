# MealWise

**Good food. Smart budget.** An offline Python meal planner for students.

![MealWise promotional artwork](docs/promo.png)

*AI-generated promotional artwork, not a screenshot. Food imagery is illustrative.*

MealWise builds a day of breakfast, lunch and dinner around your budget, cooking time and preferences. Created by **Lujianyang Feng** for COMP9001.

## Run

Download this repository using **Code → Download ZIP**, extract it, and open a terminal in the extracted folder. Use Python 3.9 or later.

```bash
python3 main.py
```

For a repeatable example:

```bash
python3 main.py --demo
```

For the desktop interface:

```bash
python3 gui.py
```

The GUI requires Tkinter and a desktop display. It cannot open a window in a headless Ed terminal; use `main.py` there. Tkinter is included with many Python distributions, but some Linux installations require a separate OS Tkinter package. No third-party Python packages, API keys or internet connection are needed by the program.

## Features

- Enforce a daily AUD budget, total cooking-time limit, vegetarian preference and exact ingredient exclusions.
- Rank feasible days by energy preference, distinct missing pantry ingredients, cost and recipe IDs.
- Compare alternatives and view cooking instructions, energy and protein totals.
- Consolidate a shopping list, excluding labels already in your pantry.
- Save/load validated JSON and export a readable text plan.

Example with an $18 budget, a 60-minute limit and an 1800 kcal preference:

| Meal | Recipe |
| --- | --- |
| Breakfast | Egg toast |
| Lunch | Bean potato bowl |
| Dinner | Bean chilli rice |

Total: **$9.40 · 52 minutes · 1800 kcal · 73 g protein**, using demonstration estimates.

## Project structure

```text
MealWise/
├── main.py               # Terminal entry and shared report formatting
├── gui.py                # Tkinter desktop entry
├── models.py             # Recipe/preferences models and validation
├── catalogue.py          # 18 demonstration recipes
├── planner.py            # Recursive search, ranking and shopping aggregation
├── storage.py            # Validated JSON persistence
├── test_mealwise.py      # Core behaviour and independent search oracle
├── test_gui.py           # Headless GUI controller integration tests
├── assets/promo.ppm      # Runtime homepage image
├── docs/promo.png        # Repository promotional image
├── README.txt            # Assessment running instructions
├── README.md
├── LICENSE
└── .gitignore
```

## Advanced concepts and tests

**Recursion:** backtracking selects one recipe for each meal and prunes branches exceeding budget or time.

**File I/O:** versioned JSON stores preferences and recipe IDs, with schema checks and atomic file replacement.

**Testing:** boundary cases, invalid files, persistence and an independent Cartesian-product search oracle check behaviour.

```bash
python3 -m unittest -v test_mealwise
python3 -m unittest -v
```

GUI controller tests skip if Tkinter cannot be imported. They do not test rendered layout. Saved plans and text exports are created beside the scripts and are ignored by Git.

## Data and limitations

All 18 recipes are manually authored demonstration data. Prices, cooking times and nutrition are illustrative estimates, not verified prices or measured nutrition. Energy is a ranking preference, not a medical recommendation. Ingredient exclusions use exact labels and are not certified allergy screening. Shopping counts indicate how many meals use an ingredient, not grams or package quantities. Pantry ingredients remain included in estimated recipe costs.

The frosted-glass appearance is painted with Tkinter; it is not operating-system backdrop blur.

## Acknowledgements and license

Code and visual design were developed with AI assistance. Promotional artwork is AI-generated. The software source is available under the [MIT License](LICENSE). Promotional artwork is supplied as illustrative project material and does not depict guaranteed recipe results.
