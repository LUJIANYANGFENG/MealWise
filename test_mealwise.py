"""Run: python3 -m unittest -v. Tests use isolated temporary directories."""
import itertools
import json
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import asdict
from pathlib import Path
from catalogue import catalogue
from models import Preferences
from planner import search, eligible, totals, rank, shopping, SLOTS
from storage import save, load
from main import display


class MealWiseTests(unittest.TestCase):
    def setUp(self):
        self.recipes = catalogue()
        self.prefs = Preferences()
        self.plan = search(self.recipes, self.prefs)[0]

    def test_catalogue_unique_and_complete(self):
        self.assertEqual(len({r.id for r in self.recipes}), 18)
        for slot in SLOTS:
            self.assertEqual(sum(r.slot == slot for r in self.recipes), 6)
        for r in self.recipes:
            self.assertGreater(r.cents, 0)
            self.assertGreater(r.minutes, 0)

    def test_recursive_search_against_independent_cartesian_oracle(self):
        for prefs in [Preferences(), Preferences(10, 35, 1700, True),
                      Preferences(13, 50, 1900, False, ('egg', 'tofu'))]:
            groups = [[r for r in self.recipes if r.slot == s and eligible(r, prefs)] for s in SLOTS]
            expected = []
            for plan in itertools.product(*groups):
                if sum(r.cents for r in plan) <= prefs.budget_cents and sum(r.minutes for r in plan) <= prefs.minutes:
                    expected.append(tuple(r.id for r in plan))
            actual = search(self.recipes, prefs)
            self.assertEqual({tuple(r.id for r in p) for p in actual}, set(expected))
            self.assertEqual(len(actual), len(expected))
            self.assertEqual(actual, sorted(actual, key=lambda p: rank(p, prefs)))

    def test_vegetarian_and_exclusions(self):
        prefs = Preferences(20, 100, 1800, True, ('egg','milk','peanut'))
        plans = search(self.recipes, prefs)
        self.assertTrue(plans)
        for p in plans:
            self.assertTrue(all(r.vegetarian for r in p))
            self.assertFalse(set(i for r in p for i in r.ingredients) & set(prefs.excluded))

    def test_exact_boundary_is_allowed(self):
        t = totals(self.plan)
        prefs = Preferences(t['cents']/100, t['minutes'], t['kcal'])
        self.assertIn(self.plan, search(self.recipes, prefs))

    def test_fractional_cent_budget_never_rounds_up(self):
        self.assertEqual(Preferences(budget=9.399).budget_cents, 939)
        self.assertNotIn(self.plan, search(self.recipes, Preferences(budget=9.399)))
        self.assertIn(self.plan, search(self.recipes, Preferences(budget=9.40)))

    def test_impossible_budget_and_time(self):
        self.assertEqual(search(self.recipes, Preferences(.01)), [])
        self.assertEqual(search(self.recipes, Preferences(minutes=1)), [])

    def test_missing_slot(self):
        self.assertEqual(search([r for r in self.recipes if r.slot != 'dinner'], self.prefs), [])

    def test_normalisation(self):
        self.assertEqual(Preferences(excluded=(' EGG ', 'egg')).excluded, ('egg',))

    def test_invalid_inputs(self):
        for kwargs in [{'budget':float('nan')}, {'budget':float('inf')}, {'budget':-1},
                       {'budget':True}, {'minutes':1.5}, {'target':0}, {'vegetarian':'yes'},
                       {'pantry':'rice'}, {'excluded':[1]}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Preferences(**kwargs)

    def test_pantry_removes_items_not_cost(self):
        before = totals(self.plan)
        items = tuple(shopping(self.plan))
        self.assertEqual(shopping(self.plan, items), {})
        self.assertEqual(totals(self.plan), before)

    def test_shopping_counts(self):
        expected = sum(len(r.ingredients) for r in self.plan)
        self.assertEqual(sum(shopping(self.plan).values()), expected)

    def test_energy_is_soft(self):
        self.assertTrue(search(self.recipes, Preferences(target=9999)))

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'save.json'
            save(path, self.prefs, self.plan)
            self.assertEqual(load(path, self.recipes), (self.prefs, self.plan))
            save(path, self.prefs, self.plan)
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    def test_bad_saved_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'bad.json'
            for payload in ['{', '[]', json.dumps({'version':2,'preferences':{},'recipe_ids':[]}),
                            json.dumps({'version':1,'preferences':{},'recipe_ids':['x','l1','d1']}),
                            json.dumps({'version':1,'preferences':{'budget':.01},'recipe_ids':['b1','l1','d1']}),
                            json.dumps({'version':1,'preferences':{},'recipe_ids':['d1','l1','b1']})]:
                path.write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    load(path, self.recipes)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(OSError):
            load(Path(folder)/'absent.json', self.recipes)

    def test_saved_preferences_require_complete_known_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            for prefs in [{}, dict(asdict(self.prefs), pantry=['unknown']),
                          dict(asdict(self.prefs), excluded=['unknown']),
                          dict(asdict(self.prefs), extra=True)]:
                path.write_text(json.dumps({'version': 1, 'preferences': prefs,
                                            'recipe_ids': [r.id for r in self.plan]}))
                with self.subTest(prefs=prefs), self.assertRaises(ValueError):
                    load(path, self.recipes)

    def test_failed_atomic_replace_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'save.json'
            save(path, self.prefs, self.plan)
            original = path.read_bytes()
            with patch('storage.os.replace', side_effect=OSError('simulated failure')):
                with self.assertRaises(OSError):
                    save(path, self.prefs, self.plan)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_rank_priorities_independently(self):
        plans = search(self.recipes, self.prefs)
        prefs = Preferences(pantry=('rice', 'tomato'))
        ordered = search(self.recipes, prefs)
        keys = []
        for plan in ordered:
            missing = {i for r in plan for i in r.ingredients} - {'rice', 'tomato'}
            keys.append((abs(sum(r.kcal for r in plan)-1800), len(missing),
                         sum(r.cents for r in plan), tuple(r.id for r in plan)))
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(plans), len(ordered))

    def test_export_report(self):
        report = display(self.plan, self.prefs)
        for text in ['BREAKFAST', 'LUNCH', 'DINNER', 'SHOPPING', 'TOTAL', 'illustrative']:
            self.assertIn(text, report)


if __name__ == '__main__':
    unittest.main()
