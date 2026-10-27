"""Domain objects and validation, independent of terminal input/output."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
import math


def number(value, label, minimum, maximum):
    """Reject booleans, NaN, infinity and out-of-range numeric input."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be numeric.')
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{label} must be between {minimum} and {maximum}.')
    return value


def words(values):
    if not isinstance(values, (list, tuple)) or any(not isinstance(x, str) for x in values):
        raise ValueError('Ingredients must be a list of text values.')
    return tuple(sorted({x.strip().lower() for x in values if x.strip()}))


@dataclass(frozen=True)
class Recipe:
    id: str
    name: str
    slot: str
    cents: int
    minutes: int
    kcal: int
    protein: int
    vegetarian: bool
    ingredients: tuple
    method: str


@dataclass(frozen=True)
class Preferences:
    budget: float = 18
    minutes: int = 60
    target: int = 1800
    vegetarian: bool = False
    excluded: tuple = ()
    pantry: tuple = ()

    def __post_init__(self):
        number(self.budget, 'Budget', 0.01, 1000)
        number(self.minutes, 'Minutes', 1, 1440)
        number(self.target, 'Target', 1, 10000)
        if type(self.minutes) is not int or type(self.target) is not int:
            raise ValueError('Minutes and target must be integers.')
        if type(self.vegetarian) is not bool:
            raise ValueError('Vegetarian must be true or false.')
        object.__setattr__(self, 'excluded', words(self.excluded))
        object.__setattr__(self, 'pantry', words(self.pantry))

    @property
    def budget_cents(self):
        # Floor fractional cents so a hard budget can never be rounded upward.
        return int((Decimal(str(self.budget)) * 100).to_integral_value(rounding=ROUND_FLOOR))
