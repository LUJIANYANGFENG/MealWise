"""RUN THIS FILE: python3 main.py (Python 3.9+, standard library only).
MealWise — COMP9001 Final Project. By Lujianyang Feng.
Use python3 main.py --demo for a repeatable non-interactive demonstration.
"""
import sys
from pathlib import Path
from catalogue import catalogue
from models import Preferences
from planner import search, totals, shopping
from storage import save, load

BASE = Path(__file__).resolve().parent


def display(plan, prefs):
    """Produce the same human-readable report for terminal and text export."""
    t = totals(plan)
    lines = ['MEALWISE | Spend less. Plan with purpose.',
             'One day / one person | AUD | illustrative estimates',
             f"Budget ${prefs.budget_cents/100:.2f}; time limit {prefs.minutes} min; energy preference {prefs.target} kcal"]
    for recipe in plan:
        lines += [f'\n{recipe.slot.upper()}: {recipe.name}',
                  f'  ${recipe.cents / 100:.2f} | {recipe.minutes} min | {recipe.kcal} kcal | {recipe.protein} g protein',
                  f'  Ingredients: {", ".join(recipe.ingredients)}',
                  f'  Method: {recipe.method}']
    lines += [f"\nTOTAL: ${t['cents']/100:.2f} | {t['minutes']} min | {t['kcal']} kcal | {t['protein']} g protein",
              f"Budget remaining: ${(prefs.budget_cents-t['cents'])/100:.2f}",
              f"Energy difference: {t['kcal']-prefs.target:+d} kcal (soft preference)",
              '\nSHOPPING: ingredient / number of meals using it (not quantities)']
    lines += [f'  {item}: {count}' for item, count in shopping(plan, prefs.pantry).items()]
    if not shopping(plan, prefs.pantry):
        lines.append('  All ingredient labels are already in your pantry.')
    lines += ['\nDemo data: prices and nutrition are illustrative, not verified.',
              'Exclusions match exact labels only; check product labels for allergens.',
              'Meal costs include pantry items. Time is summed active/preparation estimates.']
    return '\n'.join(lines)


def ask_number(prompt, convert, low, high):
    while True:
        raw = input(prompt).strip()
        try:
            value = convert(raw)
            from models import number
            return number(value, 'Input', low, high)
        except (ValueError, OverflowError):
            print(f'Enter a finite number from {low} to {high}.')


def ask_preferences(recipes):
    budget = ask_number('Daily budget AUD (e.g. 15): ', float, 0.01, 1000)
    minutes = ask_number('Total cooking minutes (e.g. 60): ', int, 1, 1440)
    target = ask_number('Energy preference kcal (not a medical recommendation): ', int, 1, 10000)
    while True:
        answer = input('Vegetarian only? y/n: ').strip().lower()
        if answer in ('y', 'n'):
            break
        print('Please enter y or n.')
    known = {i for r in recipes for i in r.ingredients}
    print('Ingredient labels: ' + ', '.join(sorted(known)))

    def read_labels(prompt):
        while True:
            labels = tuple(x.strip().lower() for x in input(prompt).split(',') if x.strip())
            unknown = set(labels) - known
            if not unknown:
                return labels
            print('Unknown labels: ' + ', '.join(sorted(unknown)) + '. Use labels above.')

    excluded = read_labels('Exclude labels (comma separated, Enter for none): ')
    pantry = read_labels('Already in pantry (comma separated, Enter for none): ')
    return Preferences(budget, minutes, target, answer == 'y', excluded, pantry)


def main():
    recipes = catalogue()
    prefs = Preferences()
    plans = search(recipes, prefs)
    index = 0
    if '--demo' in sys.argv:
        print(display(plans[0], prefs))
        print(f'\n{len(plans)} feasible combinations searched; best energy match shown.')
        return
    print('Welcome to MealWise. Offline daily meal planning, no installation needed.')
    print('Illustrative data only. Choose 1 to set your preferences.')
    while True:
        print('\n1 Plan a day | 2 View | 3 Next alternative | 4 Save | 5 Load | 6 Export | 7 Catalogue | 0 Exit')
        try:
            command = input('Choose: ').strip()
            if command == '0':
                print('Goodbye!')
                return
            if command == '1':
                candidate_prefs = ask_preferences(recipes)
                candidates = search(recipes, candidate_prefs)
                if not candidates:
                    print('No feasible plan. Increase budget/time or reduce exclusions. Previous plan retained.')
                    continue
                prefs, plans, index = candidate_prefs, candidates, 0
                print(f'{len(plans)} feasible combinations. Ranked by energy gap, new ingredients, then cost.')
                print(display(plans[index], prefs))
            elif command == '2':
                print(display(plans[index], prefs))
            elif command == '3':
                index = (index + 1) % len(plans)
                print(f'Alternative {index + 1}/{len(plans)}')
                print(display(plans[index], prefs))
            elif command == '4':
                save(BASE / 'mealwise_saved.json', prefs, plans[index])
                print('Saved to mealwise_saved.json beside main.py.')
            elif command == '5':
                candidate_prefs, candidate = load(BASE / 'mealwise_saved.json', recipes)
                candidates = search(recipes, candidate_prefs)
                new_index = candidates.index(candidate)
                prefs, plans, index = candidate_prefs, candidates, new_index
                print('Loaded saved preferences and selected plan.')
                print(display(plans[index], prefs))
            elif command == '6':
                (BASE / 'mealwise_plan.txt').write_text(display(plans[index], prefs) + '\n', encoding='utf-8')
                print('Exported to mealwise_plan.txt beside main.py.')
            elif command == '7':
                for r in recipes:
                    print(f'{r.id} | {r.slot:9} | {r.name:27} | ${r.cents/100:.2f} | {r.minutes} min | {", ".join(r.ingredients)}')
            else:
                print('Choose a menu number from 0 to 7.')
        except (OSError, ValueError) as error:
            print(f'Could not complete action: {error}')
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye!')
            return


if __name__ == '__main__':
    main()
