"""Original demonstration recipes: estimates per single-person serving.
Prices, energy and protein are fictional teaching data, not sourced nutrition.
Ingredient labels support exact matching; they are not certified allergen data.
"""
from models import Recipe


def catalogue():
    """Return a fresh immutable catalogue; prices are integer AUD cents."""
    rows = [
        ('b1','Banana oat bowl','breakfast',220,5,480,16,True,('oats','banana','milk'),'Combine oats and milk; cook, then top with sliced banana.'),
        ('b2','Egg toast','breakfast',280,10,450,23,True,('egg','bread','tomato'),'Cook eggs until set; serve with toast and sliced tomato.'),
        ('b3','Berry yoghurt bowl','breakfast',350,3,410,25,True,('yoghurt','berries','oats'),'Spoon yoghurt into a bowl and add berries and oats.'),
        ('b4','Peanut banana toast','breakfast',190,4,520,18,True,('peanut','banana','bread'),'Toast bread; add peanut butter and banana slices.'),
        ('b5','Tofu breakfast wrap','breakfast',320,12,540,27,True,('tofu','wrap','spinach'),'Heat crumbled tofu and spinach; fill a warmed wrap.'),
        ('b6','Apple cinnamon oats','breakfast',210,8,460,13,True,('oats','apple','soy milk','cinnamon'),'Simmer oats with soy milk, diced apple and cinnamon.'),
        ('l1','Chickpea rice bowl','lunch',390,18,650,24,True,('chickpea','rice','spinach','tomato'),'Cook rice; heat drained chickpeas and vegetables, then combine.'),
        ('l2','Chicken rice bowl','lunch',520,22,710,45,False,('chicken','rice','broccoli'),'Cook rice; cook chicken thoroughly and steam broccoli; combine.'),
        ('l3','Tuna pasta','lunch',460,15,670,38,False,('tuna','pasta','tomato'),'Boil pasta; drain and combine with heated canned tuna and tomato.'),
        ('l4','Lentil wrap','lunch',330,10,590,25,True,('lentil','wrap','tomato','spinach'),'Heat cooked lentils; fill wrap with lentils and vegetables.'),
        ('l5','Tofu noodle bowl','lunch',430,16,630,30,True,('tofu','noodles','carrot','soy sauce'),'Cook noodles; stir-fry tofu and carrot, add noodles and sauce.'),
        ('l6','Bean potato bowl','lunch',310,20,610,22,True,('bean','potato','tomato'),'Cook diced potato until tender; mix with heated canned beans and tomato.'),
        ('d1','Lentil tomato pasta','dinner',380,20,720,29,True,('lentil','pasta','tomato'),'Boil pasta; heat cooked lentils in tomato sauce and combine.'),
        ('d2','Chicken vegetable rice','dinner',580,25,760,48,False,('chicken','rice','carrot','broccoli'),'Cook rice; cook chicken thoroughly with vegetables and serve.'),
        ('d3','Tofu rice stir-fry','dinner',440,18,690,33,True,('tofu','rice','broccoli','soy sauce'),'Cook rice; stir-fry tofu and broccoli, then add sauce.'),
        ('d4','Bean chilli rice','dinner',350,22,740,28,True,('bean','rice','tomato','carrot'),'Cook rice; simmer canned beans, tomato and carrot, then serve.'),
        ('d5','Salmon potato plate','dinner',790,28,700,42,False,('salmon','potato','broccoli'),'Cook potatoes and broccoli; cook salmon thoroughly and serve.'),
        ('d6','Egg vegetable noodles','dinner',370,15,680,31,True,('egg','noodles','carrot','spinach'),'Cook noodles; scramble eggs until set, stir-fry vegetables and combine.'),
    ]
    return tuple(Recipe(*r) for r in rows)
