"""Exhaustive recursive search with budget/time pruning (at most 216 plans)."""
from collections import Counter

SLOTS = ('breakfast', 'lunch', 'dinner')


def totals(plan):
    return {field: sum(getattr(r, field) for r in plan)
            for field in ('cents', 'minutes', 'kcal', 'protein')}


def eligible(recipe, prefs):
    return ((not prefs.vegetarian or recipe.vegetarian)
            and not set(recipe.ingredients).intersection(prefs.excluded))


def shopping(plan, pantry=()):
    """Count recipe uses, not grams or supermarket package quantities."""
    counts = Counter(i for r in plan for i in r.ingredients if i not in pantry)
    return dict(sorted(counts.items()))


def rank(plan, prefs):
    """Lexicographic objective: energy gap, new ingredients, cost, recipe IDs.

    Pantry changes convenience ranking but never subtracts from meal cost.
    """
    t = totals(plan)
    return (abs(t['kcal'] - prefs.target), len(shopping(plan, prefs.pantry)),
            t['cents'], tuple(r.id for r in plan))


def search(recipes, prefs):
    """Return ALL feasible plans in deterministic best-first order.

    Base case: one recipe selected for each of the three slots.
    Recursive step: append one eligible recipe for the next slot.
    Prune when accumulated nonnegative price/time exceeds a hard limit.
    With n recipes per slot, time is O(n**3), depth is exactly 3.
    """
    choices = [[r for r in recipes if r.slot == slot and eligible(r, prefs)]
               for slot in SLOTS]
    results = []

    def visit(index, selected, cents, minutes):
        if index == len(SLOTS):
            results.append(tuple(selected))
            return
        for recipe in choices[index]:
            next_cost = cents + recipe.cents
            next_time = minutes + recipe.minutes
            if next_cost > prefs.budget_cents or next_time > prefs.minutes:
                continue
            selected.append(recipe)
            visit(index + 1, selected, next_cost, next_time)
            selected.pop()  # backtrack: sibling branches must start clean

    visit(0, [], 0, 0)
    return sorted(results, key=lambda p: rank(p, prefs))
