"""Versioned JSON persistence; invalid files fail without changing app state."""
import json
import os
import tempfile
from pathlib import Path
from dataclasses import asdict, fields
from models import Preferences
from planner import SLOTS, eligible, totals


def save(path, prefs, plan):
    """Write atomically in the destination directory; preserve old data on failure."""
    path = Path(path)
    payload = {'version': 1, 'preferences': asdict(prefs),
               'recipe_ids': [r.id for r in plan]}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load(path, recipes):
    """Validate schema, types, IDs, meal order and constraints before returning."""
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if type(data) is not dict or set(data) != {'version','preferences','recipe_ids'}:
            raise ValueError('Invalid file schema.')
        if type(data['version']) is not int or data['version'] != 1:
            raise ValueError('Unsupported file version.')
        raw = data['preferences']
        if type(raw) is not dict or set(raw) != {f.name for f in fields(Preferences)}:
            raise ValueError('Incomplete or unexpected preferences fields.')
        prefs = Preferences(**raw)
        known = {item for recipe in recipes for item in recipe.ingredients}
        if (set(prefs.excluded) | set(prefs.pantry)) - known:
            raise ValueError('Unknown ingredient labels in saved preferences.')
        ids = data['recipe_ids']
        if not isinstance(ids, list) or len(ids) != 3 or any(type(i) is not str for i in ids):
            raise ValueError('Expected three recipe IDs.')
        lookup = {r.id: r for r in recipes}
        plan = tuple(lookup[i] for i in ids)
        if tuple(r.slot for r in plan) != SLOTS or not all(eligible(r, prefs) for r in plan):
            raise ValueError('Plan violates meal or dietary constraints.')
        t = totals(plan)
        if t['cents'] > prefs.budget_cents or t['minutes'] > prefs.minutes:
            raise ValueError('Plan exceeds budget or time limit.')
        return prefs, plan
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f'Invalid MealWise file: {error}') from error
