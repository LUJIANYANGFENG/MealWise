"""MealWise desktop dashboard. Run: python3 gui.py (standard library only).

Rounded cards use native Tk Canvas; the planner and persistence are shared with
main.py. Colour choices are explicit so macOS dark mode cannot reduce contrast.
"""
from pathlib import Path
import math
import tkinter as tk
from tkinter import ttk
from catalogue import catalogue
from models import Preferences
from planner import search, totals, shopping
from storage import save, load
from main import display

BASE = Path(__file__).resolve().parent
BG = '#263d2d'
PANEL = '#476255'
INK = '#203526'
TEXT = '#f5faef'
MUTED = '#d0ddd3'
LIME = '#d5f6a4'
PALE = '#ecf4df'
ORANGE = '#ff783f'


class RoundedPanel(tk.Canvas):
    """Painted frosted surface: diffuse edges, fine grain and a bright rim.

    This is an app-rendered visual effect, not operating-system backdrop blur.
    A normal Tk frame keeps controls accessible and text crisp.
    """
    def __init__(self, parent, colour=PANEL, padding=18, radius=22, **kwargs):
        super().__init__(parent, background=parent.cget('background'),
                         highlightthickness=0, borderwidth=0, **kwargs)
        self.colour,self.padding,self.radius=colour,padding,radius
        self.inner=tk.Frame(self,background=colour)
        self.window=self.create_window(padding,padding,anchor='nw',window=self.inner)
        self.glass_image=None;self.glass_size=None;self.pending=None
        self.bind('<Configure>',self.resize)
        self.bind('<Destroy>',self.cancel_pending,add='+')

    def cancel_pending(self,event):
        if event.widget is self and self.pending is not None:
            self.after_cancel(self.pending);self.pending=None

    def resize(self,event):
        self.itemconfigure(self.window,width=max(1,event.width-2*self.padding),height=max(1,event.height-2*self.padding))
        if self.pending is not None:self.after_cancel(self.pending)
        self.pending=self.after(45,self.paint_glass)

    def paint_glass(self):
        self.pending=None
        w,h=self.winfo_width(),self.winfo_height()
        if w<4 or h<4:return
        if self.glass_size!=(w,h):
            rgb=lambda c:tuple(int(c[i:i+2],16) for i in (1,3,5))
            base=rgb(self.colour);back=rgb(self.cget('background'));data=bytearray()
            r=min(self.radius,w/2,h/2)
            for y in range(h):
                for x in range(w):
                    # Signed distance gives the same soft edge along straight
                    # sides and curved corners; fractional coverage avoids steps.
                    qx=abs(x+.5-w/2)-(w/2-r)
                    qy=abs(y+.5-h/2)-(h/2-r)
                    distance=math.hypot(max(qx,0),max(qy,0))+min(max(qx,qy),0)-r
                    coverage=max(0,min(1,.5-distance))
                    if coverage==0:
                        data.extend(back);continue
                    edge=max(0,-distance)
                    haze=math.exp(-edge/8)*(4+3*(1-y/max(1,h)))
                    grain=(((x*23+y*37)%9)-4)*.10
                    for value,background in zip(base,back):
                        surface=min(255,value+haze+grain)
                        data.append(max(0,min(255,round(surface*coverage+background*(1-coverage)))))
            ppm=f'P6\n{w} {h}\n255\n'.encode()+bytes(data)
            self.glass_image=tk.PhotoImage(master=self,data=ppm,format='PPM')
            self.glass_size=(w,h)
        self.delete('surface')
        self.create_image(0,0,image=self.glass_image,anchor='nw',tags='surface')
        self.tag_lower('surface')


def label(parent, text='', size=12, colour=TEXT, bold=False, safe_glyphs=False, **kwargs):
    # Some macOS Tk/Helvetica combinations report too little room below the
    # baseline. Use Arial plus INTERNAL padding for descenders (g, p, q, y).
    # External pack padding does not expand a Label's own drawing area.
    return tk.Label(parent, text=text, background=parent.cget('background'),
                    foreground=colour, font=('Arial' if safe_glyphs else 'Helvetica',size,'bold' if bold else 'normal'),
                    anchor='w', justify='left', borderwidth=0, padx=0, pady=3 if safe_glyphs else 0, **kwargs)


class MealWiseApp:
    """UI state changes only after successful search or validated load."""
    def __init__(self, root):
        self.root = root
        self.recipes = catalogue()
        self.prefs = Preferences()
        self.plans = search(self.recipes, self.prefs)
        self.index = 0
        self.inputs = {}
        root.title('MealWise | A little planning. A better day.')
        root.geometry('1260x880')
        root.minsize(1140,820)
        root.configure(background=BG)
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('TEntry', fieldbackground='#eef4e6', foreground=INK, padding=9,
                        bordercolor='#6b8265', lightcolor='#6b8265', darkcolor='#6b8265')
        style.map('TEntry', bordercolor=[('focus',LIME)])
        style.configure('TButton', background='#526d4d', foreground=TEXT, borderwidth=0,
                        padding=(14,10), font=('Helvetica',11,'bold'))
        style.map('TButton', background=[('active','#68835e'),('pressed','#486343')])
        style.configure('Primary.TButton', background=LIME, foreground=INK, padding=(18,13))
        style.map('Primary.TButton',background=[('active','#e4ffc2'),('pressed','#c2e995')],foreground=[('active',INK)])
        style.configure('Accent.TButton', background=ORANGE, foreground='#1d3022')
        style.map('Accent.TButton',background=[('active','#ff9569')])
        style.configure('TCheckbutton', background=PANEL, foreground=TEXT, padding=6)
        style.map('TCheckbutton',background=[('active',PANEL)],foreground=[('active',TEXT)])
        style.configure('Vertical.TScrollbar', background='#75906a', troughcolor=PANEL, borderwidth=0, arrowsize=11)
        self.shell=tk.Frame(root,background=BG)
        self.shell.pack(fill='both',expand=True,padx=24,pady=20)
        top=tk.Frame(self.shell,background=BG); top.pack(fill='x',pady=(0,20))
        badge=label(top,' mw ',18,INK,True);badge.configure(background=LIME);badge.pack(side='left',padx=(0,12))
        label(top,'MealWise',23,TEXT,True).pack(side='left')
        label(top,'PERSONAL MEAL PLANNER',10,MUTED).pack(side='left',padx=20)
        ttk.Button(top,text='Home ↗',command=self.show_welcome).pack(side='right')
        label(top,'OFFLINE  /  ONE PERSON',10,LIME).pack(side='right',padx=18)
        body=tk.Frame(self.shell,background=BG);body.pack(fill='both',expand=True)
        side=RoundedPanel(body,width=266);side.pack(side='left',fill='y',padx=(0,20));f=side.inner
        label(f,'Your preferences',18,TEXT,True).pack(anchor='w')
        label(f,'A day that works for you.',11,MUTED).pack(anchor='w',pady=(5,20))
        for key,title,value in [('budget','Daily budget · AUD','18'),('minutes','Cooking time · minutes','60'),
                                ('target','Energy preference · kcal','1800'),('excluded','Leave out ingredients',''),
                                ('pantry','Already in your pantry','')]:
            label(f,title,11,MUTED).pack(anchor='w',pady=(0,6))
            var=tk.StringVar(root,value=value);self.inputs[key]=var
            ttk.Entry(f,textvariable=var).pack(fill='x',pady=(0,15))
        label(f,'Example: rice, tomato',10,MUTED).pack(anchor='w')
        ttk.Button(f,text='Ingredient labels ↗',command=self.show_ingredients).pack(fill='x',pady=(10,12))
        self.vegetarian=tk.BooleanVar(root,value=False)
        ttk.Checkbutton(f,text='Vegetarian only',variable=self.vegetarian).pack(anchor='w',pady=(0,14))
        ttk.Button(f,text='Generate my day  →',style='Primary.TButton',command=self.generate).pack(fill='x')
        label(f,'Edits apply on Generate.',10,MUTED).pack(anchor='w',pady=10)
        label(f,'Small choices.\nBetter everyday routines.',12,LIME).pack(side='bottom',anchor='w',pady=8)
        main=tk.Frame(body,background=BG);main.pack(side='left',fill='both',expand=True)
        heading=tk.Frame(main,background=BG);heading.pack(fill='x',pady=(0,14))
        label(heading,'Your day, at a glance',24,TEXT,True).pack(side='left')
        self.summary=tk.StringVar(root)
        label(heading,size=10,colour=LIME,textvariable=self.summary).pack(side='right')
        metrics=tk.Frame(main,background=BG);metrics.pack(fill='x',pady=(0,18));self.metric_values=[]
        for i,(caption,colour) in enumerate([('Daily cost',LIME),('Cooking time',PALE),('Energy',PALE),('Protein','#f9d3be')]):
            metrics.columnconfigure(i,weight=1,uniform='m')
            panel=RoundedPanel(metrics,colour,height=104,padding=16,radius=18)
            panel.grid(row=0,column=i,sticky='nsew',padx=(0,10 if i<3 else 0))
            label(panel.inner,caption,10,INK).pack(anchor='w')
            var=tk.StringVar(root);self.metric_values.append(var)
            label(panel.inner,size=23,colour=INK,bold=True,safe_glyphs=True,textvariable=var).pack(anchor='w',pady=(8,0))
        nav=tk.Frame(main,background=BG);nav.pack(fill='x',pady=(0,14))
        self.nav_buttons={}
        for key,title in [('menu','Daily menu'),('shopping','Shopping list'),('report','Full report')]:
            b=ttk.Button(nav,text=title,command=lambda k=key:self.select_tab(k));b.pack(side='left',padx=(0,8));self.nav_buttons[key]=b
        self.pages={}
        host=tk.Frame(main,background=BG);host.pack(fill='both',expand=True)
        host.rowconfigure(0,weight=1);host.columnconfigure(0,weight=1)
        for key in ('menu','shopping','report'):
            page=tk.Frame(host,background=BG);page.grid(row=0,column=0,sticky='nsew');self.pages[key]=page
        menu=self.pages['menu'];menu.rowconfigure(0,weight=1);menu.columnconfigure(0,weight=1)
        menu.columnconfigure(1,minsize=210)
        stack=tk.Frame(menu,background=BG);stack.grid(row=0,column=0,sticky='nsew',padx=(0,14))
        self.recipe_views=[]
        for i,slot in enumerate(('BREAKFAST','LUNCH','DINNER')):
            stack.rowconfigure(i,weight=1,uniform='meal');stack.columnconfigure(0,weight=1)
            card=RoundedPanel(stack,colour='#f4f7ec',padding=14,height=125)
            card.grid(row=i,column=0,sticky='nsew',pady=(0,10 if i<2 else 0))
            inside=card.inner
            row=tk.Frame(inside,background='#f4f7ec');row.pack(fill='x')
            label(row,f'0{i+1}  /  {slot}',10,'#5c7453',True).pack(side='left')
            label(row,'•',14,'#ea703d',True).pack(side='right')
            title=label(inside,size=17,colour=INK,bold=True,safe_glyphs=True);title.pack(anchor='w',pady=(3,2))
            meta=label(inside,size=10,colour='#547145',bold=True);meta.pack(anchor='w')
            ingredients=label(inside,size=10,colour='#52654d');ingredients.pack(anchor='w',pady=(5,0))
            method=label(inside,size=10,colour='#52654d');# Cooking instructions remain available in Full report.
            self.recipe_views.append((title,meta,ingredients,method))
            def wrap(event,views=(title,meta,ingredients,method)):
                for item in views:item.configure(wraplength=max(160,event.width-4))
            inside.bind('<Configure>',wrap)
        insight=RoundedPanel(menu,colour='#7e9972',padding=18,width=210)
        insight.grid(row=0,column=1,sticky='nsew');ins=insight.inner
        label(ins,'Budget balance',16,INK,True).pack(anchor='w')
        label(ins,'Your daily ingredient estimate',10,INK,wraplength=170).pack(anchor='w',pady=(6,14))
        self.balance_value=tk.StringVar(root)
        label(ins,size=27,colour=INK,bold=True,textvariable=self.balance_value).pack(anchor='w')
        label(ins,'LEFT IN YOUR BUDGET',9,INK).pack(anchor='w',pady=(4,22))
        self.budget_bar=tk.Canvas(ins,height=118,background='#7e9972',highlightthickness=0)
        self.budget_bar.pack(fill='x')
        self.budget_bar.bind('<Configure>',lambda e:self.draw_budget())
        label(ins,'A little room to spare.',12,INK,True).pack(anchor='w',pady=(18,6))
        label(ins,'Pantry labels reduce your shopping list. Full meal costs are still included.',11,INK,wraplength=170).pack(anchor='w')
        self.shopping_report=self.text_panel(self.pages['shopping'])
        self.report=self.text_panel(self.pages['report'])
        actions=tk.Frame(main,background=BG);actions.pack(fill='x',pady=(14,0))
        for title,call in [('Next option →',self.next_plan),('Save plan',self.save_plan),('Load plan',self.load_plan),('Export text',self.export)]:
            ttk.Button(actions,text=title,command=call).pack(side='left',padx=(0,8))
        self.status=tk.StringVar(root,value='Your first plan is ready. Make it yours on the left.')
        status=label(main,size=10,colour=MUTED,textvariable=self.status,wraplength=820)
        status.pack(anchor='w',pady=(12,4))
        main.bind('<Configure>',lambda e:status.configure(wraplength=max(200,e.width)))
        foot=label(main,'Illustrative estimates · Exact ingredient labels only · Not allergy screening',9,MUTED)
        foot.pack(anchor='w')
        actions.pack_configure(side='bottom')
        status.pack_configure(side='bottom')
        foot.pack_configure(side='bottom')
        host.pack_forget();host.pack(fill='both',expand=True)
        self.select_tab('menu');self.refresh();self.show_welcome()

    def select_tab(self,key):
        self.pages[key].tkraise()
        for name,button in self.nav_buttons.items():
            button.configure(style='Primary.TButton' if name==key else 'TButton')

    @staticmethod
    def text_panel(parent):
        panel=RoundedPanel(parent,colour='#f4f7ec',padding=16)
        panel.pack(fill='both',expand=True)
        text=tk.Text(panel.inner,wrap='word',font=('Helvetica',13),background='#f4f7ec',
                     foreground=INK,relief='flat',highlightthickness=0,padx=8,pady=8,
                     spacing1=3,spacing3=7,selectbackground=LIME,selectforeground=INK)
        bar=ttk.Scrollbar(panel.inner,command=text.yview);bar.pack(side='right',fill='y')
        text.configure(yscrollcommand=bar.set);text.pack(fill='both',expand=True)
        return text

    def show_ingredients(self):
        from tkinter import messagebox
        known=', '.join(sorted({i for r in self.recipes for i in r.ingredients}))
        messagebox.showinfo('Ingredient labels','Use these exact labels, separated by commas:\n\n'+known,parent=self.root)

    def draw_budget(self):
        total=totals(self.plans[self.index]);cap=self.prefs.budget_cents
        c=self.budget_bar;c.delete('all');w=max(c.winfo_width(),150)
        used=total['cents']/cap
        for i,(value,colour,title) in enumerate([(used,LIME,'Used'),(1-used,'#edf4df','Left')]):
            x=14+i*(w/2)
            c.create_rectangle(x,14,x+42,96,fill='#5e7a55',outline='')
            c.create_rectangle(x,96-82*value,x+42,96,fill=colour,outline='')
            c.create_text(x+21,110,text=title,fill=INK,font=('Helvetica',10))

    def render_dashboard(self):
        plan=self.plans[self.index];total=totals(plan)
        for variable,value in zip(self.metric_values,(f"${total['cents']/100:.2f}",f"{total['minutes']} min",f"{total['kcal']} kcal",f"{total['protein']} g")):
            variable.set(value)
        self.balance_value.set(f"${(self.prefs.budget_cents-total['cents'])/100:.2f}")
        for view,recipe in zip(self.recipe_views,plan):
            for widget,text in zip(view,(recipe.name,f"${recipe.cents/100:.2f}  ·  {recipe.minutes} min  ·  {recipe.kcal} kcal  ·  {recipe.protein} g protein",
                                         'Ingredients: '+', '.join(recipe.ingredients),recipe.method)):
                widget.configure(text=text)
        items=shopping(plan,self.prefs.pantry)
        text='YOUR SHOPPING LIST\n\nCounts show meal uses, not purchase quantities.\nPantry labels have already been left out.\n\n'
        text+='\n'.join(f'{name.title()}    ·    {count} meal(s)' for name,count in items.items()) if items else 'You already have every listed ingredient.'
        self.shopping_report.configure(state='normal');self.shopping_report.delete('1.0','end')
        self.shopping_report.insert('1.0',text);self.shopping_report.configure(state='disabled')
        self.draw_budget()

    def refresh(self):
        plan=self.plans[self.index]
        self.summary.set(f'OPTION {self.index+1:02} / {len(self.plans)}')
        self.report.configure(state='normal');self.report.delete('1.0','end')
        self.report.insert('1.0',display(plan,self.prefs));self.report.configure(state='disabled')
        self.render_dashboard()

    def show_welcome(self):
        if getattr(self,'welcome',None) is not None and self.welcome.winfo_exists():
            return
        self.shell.pack_forget()
        welcome=tk.Frame(self.root,background=BG);self.welcome=welcome
        welcome.pack(fill='both',expand=True,padx=36,pady=28)
        top=tk.Frame(welcome,background=BG);top.pack(fill='x')
        label(top,'MealWise',24,TEXT,True).pack(side='left')
        label(top,'A LITTLE PLANNING. A BETTER DAY.',10,MUTED).pack(side='right')
        center=tk.Frame(welcome,background=BG);center.pack(fill='both',expand=True,pady=30)
        center.columnconfigure(0,weight=1);center.columnconfigure(1,weight=1);center.rowconfigure(0,weight=1)
        left=RoundedPanel(center,colour=PANEL,padding=30)
        left.grid(row=0,column=0,sticky='nsew',padx=(0,22));f=left.inner
        label(f,'MADE FOR STUDENT LIFE',10,LIME,True).pack(anchor='w',pady=(0,18))
        self.promo_image=None
        artwork=BASE/'assets'/'promo.ppm'
        if artwork.is_file():
            try:
                self.promo_image=tk.PhotoImage(master=self.root,file=str(artwork),format='PPM')
            except tk.TclError:
                pass
        if self.promo_image is not None:
            tk.Label(f,image=self.promo_image,background=PANEL,borderwidth=0,
                     highlightthickness=0).pack(anchor='w',pady=(0,20))
        label(f,'Plan well. Eat well.',28,TEXT,True).pack(anchor='w',pady=(0,10))
        label(f,'Three meals. One plan. Built around you.',13,LIME,wraplength=430).pack(anchor='w',pady=(0,14))
        label(f,'Set your budget, cooking time and preferences. Compare complete days and keep a plan you like.',12,MUTED,wraplength=430).pack(anchor='w')
        def enter():
            welcome.destroy();self.welcome=None
            self.shell.pack(fill='both',expand=True,padx=24,pady=20)
        ttk.Button(f,text='Plan my day  →',style='Primary.TButton',command=enter).pack(fill='x',side='bottom',pady=(12,4))
        right=RoundedPanel(center,colour='#8fa899',padding=24)
        right.grid(row=0,column=1,sticky='nsew');f=right.inner
        label(f,'A day, thoughtfully planned.',24,INK,True,wraplength=420).pack(anchor='w',pady=(0,8))
        label(f,'A live preview from your current plan',11,INK).pack(anchor='w',pady=(0,20))
        total=totals(self.plans[self.index])
        grid=tk.Frame(f,background='#8fa899');grid.pack(fill='x',pady=(0,20))
        for i,(title,value,colour) in enumerate([('DAILY COST',f"${total['cents']/100:.2f}",LIME),('COOKING TIME',f"{total['minutes']} min",PALE),
                                                  ('ENERGY',f"{total['kcal']} kcal",PALE),('PROTEIN',f"{total['protein']} g",'#ffd0b9')]):
            grid.columnconfigure(i%2,weight=1,uniform='welcome')
            tile=RoundedPanel(grid,colour,height=106,padding=16,radius=18)
            tile.grid(row=i//2,column=i%2,sticky='nsew',padx=(0,10 if i%2==0 else 0),pady=(0,10))
            label(tile.inner,title,9,INK).pack(anchor='w')
            label(tile.inner,value,26,INK,True,safe_glyphs=True).pack(anchor='w',pady=(8,0))
        for number,recipe in enumerate(self.plans[self.index],1):
            tile=RoundedPanel(f,colour='#f1f5ed',height=72,padding=15,radius=18)
            tile.pack(fill='x',pady=(0,10))
            label(tile.inner,f'{number:02}  /  {recipe.slot.upper()}',9,'#657b6a').pack(anchor='w')
            label(tile.inner,recipe.name,14,INK,True,safe_glyphs=True).pack(anchor='w',pady=(3,0))
        label(welcome,'Illustrative estimates · One day / one person · Ingredient exclusions are not allergy screening',10,MUTED).pack(anchor='w')

    def generate(self):
        try:
            def labels(key):
                return tuple(x.strip().lower() for x in self.inputs[key].get().split(',') if x.strip())
            candidate = Preferences(float(self.inputs['budget'].get()), int(self.inputs['minutes'].get()),
                                    int(self.inputs['target'].get()), self.vegetarian.get(),
                                    labels('excluded'), labels('pantry'))
            known = {i for r in self.recipes for i in r.ingredients}
            unknown = (set(candidate.excluded) | set(candidate.pantry)) - known
            if unknown:
                raise ValueError('Unknown labels: ' + ', '.join(sorted(unknown)))
            plans = search(self.recipes, candidate)
            if not plans:
                raise ValueError('No feasible plan. Increase budget/time or reduce exclusions.')
            self.prefs, self.plans, self.index = candidate, plans, 0
            self.refresh()
            self.status.set('Ranked by energy gap, distinct missing ingredients, then cost. Form edits apply on Generate.')
        except (ValueError, OverflowError) as error:
            self.status.set(str(error) + ' Previous plan retained.')

    def next_plan(self):
        self.index = (self.index + 1) % len(self.plans)
        self.refresh()

    def save_plan(self):
        try:
            save(BASE / 'mealwise_saved.json', self.prefs, self.plans[self.index])
            self.status.set('Saved generated plan and its preferences to mealwise_saved.json.')
        except (OSError, ValueError) as error:
            self.status.set(f'Could not save: {error}')

    def load_plan(self):
        try:
            prefs, plan = load(BASE / 'mealwise_saved.json', self.recipes)
            plans = search(self.recipes, prefs)
            index = plans.index(plan)
            self.prefs, self.plans, self.index = prefs, plans, index
            for key in ('budget', 'minutes', 'target'):
                self.inputs[key].set(str(getattr(prefs, key)))
            for key in ('excluded', 'pantry'):
                self.inputs[key].set(', '.join(getattr(prefs, key)))
            self.vegetarian.set(prefs.vegetarian)
            self.refresh()
            self.status.set('Loaded saved plan and restored form inputs.')
        except (OSError, ValueError) as error:
            self.status.set(f'Could not load: {error}. Previous plan retained.')

    def export(self):
        try:
            (BASE / 'mealwise_plan.txt').write_text(display(self.plans[self.index], self.prefs) + '\n', encoding='utf-8')
            self.status.set('Exported generated plan to mealwise_plan.txt beside gui.py.')
        except OSError as error:
            self.status.set(f'Could not export: {error}')


if __name__ == '__main__':
    try:
        window = tk.Tk()
        MealWiseApp(window)
        window.mainloop()
    except tk.TclError as error:
        print(f'Tk cannot open a window: {error}. Run python3 main.py for terminal mode.')
