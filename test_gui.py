"""Headless GUI controller integration tests; no display server required.

These verify state transitions and file operations, not visual layout or Tk rendering.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

try:
    import gui
except ImportError:
    gui = None


class Value:
    """Small form value stand-in so controller tests do not open windows."""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


@unittest.skipIf(gui is None, 'Optional Tkinter module is unavailable')
class GuiControllerTests(unittest.TestCase):
    def setUp(self):
        self.app = object.__new__(gui.MealWiseApp)
        app = self.app
        app.recipes = gui.catalogue()
        app.prefs = gui.Preferences()
        app.plans = gui.search(app.recipes, app.prefs)
        app.index = 0
        app.inputs = {k: Value(v) for k, v in dict(budget='15', minutes='60', target='1800',
                                                 excluded='', pantry='rice, tomato').items()}
        app.vegetarian = Value(True)
        app.summary, app.status = Value(''), Value('')
        app.report = Mock()
        app.render_dashboard = Mock()

    def test_generate_and_failed_changes_retain_selected_plan(self):
        app = self.app
        app.generate()
        self.assertTrue(app.prefs.vegetarian)
        self.assertEqual(app.prefs.pantry, ('rice', 'tomato'))
        app.next_plan()
        previous = app.plans[app.index]
        for key, value, message in [('budget', '0.01', 'No feasible'),
                                    ('budget', 'nan', 'Budget'),
                                    ('budget', 'text', 'could not convert')]:
            app.inputs[key].set(value)
            app.generate()
            self.assertEqual(app.plans[app.index], previous)
            self.assertIn(message, app.status.get())
        app.inputs['budget'].set('15')
        app.inputs['excluded'].set('unknown')
        app.generate()
        self.assertIn('Unknown labels', app.status.get())
        self.assertEqual(app.plans[app.index], previous)

    def test_save_load_export_and_damaged_file(self):
        app = self.app
        app.generate()
        app.next_plan()
        selected = app.plans[app.index]
        with TemporaryDirectory() as folder, patch.object(gui, 'BASE', Path(folder)):
            app.save_plan()
            app.export()
            self.assertIn(selected[0].name, (Path(folder)/'mealwise_plan.txt').read_text())
            app.inputs['budget'].set('100')
            app.generate()
            app.load_plan()
            self.assertEqual(app.plans[app.index], selected)
            self.assertEqual(app.inputs['budget'].get(), '15.0')
            (Path(folder)/'mealwise_saved.json').write_text('{')
            app.load_plan()
            self.assertIn('Could not load', app.status.get())
            self.assertEqual(app.plans[app.index], selected)


if __name__ == '__main__':
    unittest.main()
