MEALWISE — COMP9001 FINAL PROJECT

ENTRY POINTS
Run main.py for the terminal interface (works without graphics).
Run gui.py for the desktop graphical interface (requires Tkinter and a display).
Python 3.9+; Python standard library only. No pip install, internet or API key.

Terminal / Ed:
 python3 main.py
Repeatable terminal demonstration:
 python3 main.py --demo
Desktop GUI (outside Ed):
 python3 gui.py
Core tests, including when Tkinter is unavailable:
 python3 -m unittest -v test_mealwise
All tests (GUI controller tests skip if Tkinter is absent):
 python3 -m unittest -v

REQUIRED FILE STRUCTURE
main.py
gui.py
models.py
catalogue.py
planner.py
storage.py
test_mealwise.py
test_gui.py
README.txt
assets/promo.ppm
Keep all .py files together. Keep promo.ppm in the assets subfolder.
The GUI homepage uses this image. No other images or personal save files are needed.

GUI DISCLOSURE
This project includes a Tkinter graphical application. Run gui.py outside Ed.
The tutor can run the terminal interface via main.py in Ed and the same core
planning engine is used by both interfaces. Graphics use Tk Canvas/PhotoImage.
Frosted-glass styling is painted by the application, not OS backdrop blur.
No third-party libraries, audio/video processing or networking are used.

FEATURES AND USE
Plan breakfast, lunch and dinner for one person using a daily AUD budget,
cooking-time limit, energy preference, vegetarian choice and excluded ingredient
labels. Budget/time/diet exclusions are hard constraints. Energy is a soft
ranking preference, followed by distinct missing pantry labels, cost and IDs.
Pantry labels reduce the shopping list but do not reduce estimated meal costs.
Browse alternatives, read cooking instructions, save/load a plan and export text.

Terminal menu: 1 preferences, 2 view, 3 alternative, 4 save, 5 load,
6 export, 7 catalogue, 0 exit.
GUI: enter via Plan my day; edit the left-hand preferences and select Generate
my day. Daily menu, Shopping list and Full report switch views. Bottom buttons
provide alternatives, save, load and export. Home returns to the welcome screen.
Save/export create or replace mealwise_saved.json and mealwise_plan.txt beside
the main script. Missing/corrupt save files and infeasible plans are reported.

DESIGN AND ADVANCED CONCEPTS
models.py: immutable recipe/preferences objects and validation.
catalogue.py: 18 built-in demonstration recipes.
planner.py: recursive backtracking, budget/time pruning, deterministic ranking.
storage.py: versioned JSON, schema validation and atomic replacement.
main.py/gui.py: independent terminal and graphical interfaces.
test_mealwise.py/test_gui.py: boundary, persistence, error handling and independent
Cartesian-product oracle tests, plus headless GUI controller integration.
Advanced topics: File I/O, Testing, Recursion. Classes are not counted as Advanced.

DATA AND ACKNOWLEDGEMENT
Costs, cooking times and nutrition are manually defined illustrative estimates,
not verified supermarket prices or measured nutrition. Shopping counts mean meal
uses, not grams or package quantities. Exclusions match exact labels and do not
provide certified allergy screening. No dietary/medical target is prescribed.
Code/design were developed with AI assistance; promotional artwork is AI-generated.
