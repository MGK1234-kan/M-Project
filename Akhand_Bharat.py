import requests
from bs4 import BeautifulSoup
import webbrowser
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# --- Fetch Google News RSS ---
def fetch_google_news(limit=50):
    url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml-xml")
    items = soup.find_all("item")

    news_data = []
    for i, item in enumerate(items[:limit]):
        slno = str(i + 1)
        channel = item.source.text if item.source else "Google News"
        website = item.link.text if item.link else "No Link"
        headline = item.title.text if item.title else "No Title"

        if item.pubDate:
            parts = item.pubDate.text.split(" ")
            date = parts[0] if len(parts) > 0 else "Unknown"
            time = parts[4] if len(parts) > 4 else "Unknown"
        else:
            date, time = "Unknown", "Unknown"

        news_data.append((slno, channel, website, headline, date, time))
    return news_data

# --- Extract article content ---
def extract_article(url):
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.content, "html.parser")
        paras = [p.get_text() for p in soup.find_all("p")]
        text = "\n\n".join(paras[:20])  # limit to first 20 paragraphs
        return text if text else "No content extracted."
    except Exception as e:
        return f"Error extracting article: {e}"

# --- Table Cell ---
class TableCell(BoxLayout):
    def __init__(self, text="", width_ratio=1, fixed_height=80, scroll_type=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = fixed_height
        self.size_hint_x = width_ratio

        if scroll_type == "horizontal":
            sv = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False)
            lbl = Label(text=text, color=(1, 1, 0, 1), font_size='12sp',
                        halign="left", valign="middle",
                        size_hint_x=None, height=fixed_height)
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'width', inst.texture_size[0]))
            sv.add_widget(lbl)
            self.add_widget(sv)

        elif scroll_type == "vertical":
            sv = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
            lbl = Label(text=text, color=(1, 1, 0, 1), font_size='12sp',
                        halign="center", valign="top",
                        size_hint_y=None, width=self.width)
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1]))
            sv.add_widget(lbl)
            self.add_widget(sv)

        else:
            lbl = Label(text=text, color=(1, 1, 0, 1), font_size='12sp',
                        halign="center", valign="middle",
                        text_size=(self.width, fixed_height))
            self.add_widget(lbl)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

        self.bind(pos=self.update_border, size=self.update_border)

    def update_border(self, *args):
        self.border.rectangle = (self.x, self.y, self.width, self.height)
        
    
class TableRow(GridLayout):
    def __init__(self, values, width_ratios=None, fixed_height=80, link=None, app=None, **kwargs):
        super().__init__(**kwargs)
        self.cols = len(values)
        self.size_hint_y = None
        self.height = fixed_height
        self.link = link
        self.app = app
        self.selected = False

        if width_ratios is None:
            width_ratios = [1] * len(values)

        for idx, (v, ratio) in enumerate(zip(values, width_ratios)):
            if idx == 2:
                self.add_widget(TableCell(text=v, width_ratio=ratio, fixed_height=fixed_height, scroll_type="horizontal"))
            elif idx == 3:
                self.add_widget(TableCell(text=v, width_ratio=ratio, fixed_height=fixed_height, scroll_type="vertical"))
            else:
                self.add_widget(TableCell(text=v, width_ratio=ratio, fixed_height=fixed_height))

        with self.canvas.before:
            self.bg_color = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def select(self):
        self.selected = True
        self.bg_color.rgba = (0.2, 0.4, 0.8, 0.5)

    def deselect(self):
        self.selected = False
        self.bg_color.rgba = (0, 0, 0, 0)


class TableApp(App):
    def build(self):
        Window.size = (1400, 700)
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        Window.title = "Google News Headlines"

        # ✅ Create root_layout before returning
        self.root_layout = BoxLayout(orientation="vertical")

        # Progress bar
        self.progress = ProgressBar(max=50, value=0, size_hint=(1, None), height=20)

        # Search bar
        self.self_root.layout_add(widget.progress)
        s# Search bar
        search_layout = BoxLayout(size_hint=(1, None), height=40)

# Text input
        self.search_input = TextInput(hint_text="Enter keyword to search...", multiline=False)

# ✅ Bind Enter key inside the TextInput to search
        self.search_input.bind(on_text_validate=self.search_news)

# Search button
        search_btn = Button(text="Search", size_hint=(None, 1), width=100)
        search_btn.bind(on_press=self.search_news)

# Back button
       back_btn = Button(text="Back", size_hint=(None, 1), width=100)
       back_btn.bind(on_press=self.reset_table)

       search_layout.add_widget(self.search_input)
       search_layout.add_widget(search_btn)
       search_layout.add_widget(back_btn)
       self.root_layout.add_widget(search_layout)

        # Scrollable table
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        self.table_layout = GridLayout(cols=1, spacing=2, padding=5, size_hint_y=None)
        self.table_layout.bind(minimum_height=self.table_layout.setter('height'))
        self.scroll.add_widget(self.table_layout)
        self.root_layout.add_widget(self.scroll)

        # Initial load
        self.refresh_table()

        # Schedule refresh
        Clock.schedule_interval(self.update_progress, 1)

        # Keyboard navigation
        self.selected_index = None
        Window.bind(on_key_down=self.on_key_down)

        return self.root_layout

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        rows = [c for c in reversed(self.table_layout.children) if isinstance(c, TableRow)]
        if not rows:
            return

        if key == 40:  # Down arrow
            if self.selected_index is None:
                self.selected_index = 0
            else:
                self.selected_index = min(self.selected_index + 1, len(rows) - 1)
            self.update_selection(rows)

        elif key == 38:  # Up arrow
            if self.selected_index is None:
                self.selected_index = 0
            else:
                self.selected_index = max(self.selected_index - 1, 0)
            self.update_selection(rows)

        elif key == 13:  # Enter
            if self.selected_index is not None:
                row = rows[self.selected_index]
                if row.link and row.link != "No Link":
                    content = extract_article(row.link)
                    self.show_article(content, row.link)

        elif key == 27:  # Escape
            self.reset_table(None)

    def update_selection(self, rows):
        for i, r in enumerate(rows):
            if i == self.selected_index:
                r.select()
            else:
                r.deselect()


    def show_article(self, content, link):
        self.table_layout.clear_widgets()
        back_btn = Button(text="Back to Headlines", size_hint=(None, None), width=200, height=40)
        back_btn.bind(on_press=self.reset_table)
        self.table_layout.add_widget(back_btn)

        self.table_layout.add_widget(Label(text=f"Article from: {link}", color=(0,1,1,1),
                                           size_hint_y=None, height=40))

        sv = ScrollView(size_hint=(1, 1))
        lbl = Label(text=content, color=(1,1,0,1), font_size='14sp',
                    text_size=(Window.width-50, None), size_hint_y=None)
        lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1]))
        sv.add_widget(lbl)
        self.table_layout.add_widget(sv)


if __name__ == "__main__":
    TableApp().run()

