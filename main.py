import json
import os


from kivy.app import App
from kivy.lang import Builder
from kivy.properties import (
    ListProperty,
    DictProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
)
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label

# TTS (sesli okuma) için plyer kullanacağız; masaüstünde yoksa hata vermesin
try:
    from plyer import tts
except Exception:
    tts = None

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODULES_PATH = os.path.join(DATA_DIR, "modules.json")


# ---------- EKRANLAR ----------

class WelcomeScreen(Screen):
    pass


class ModuleListScreen(Screen):
    """Tüm modüllerin listesi, kilit ve skor gösterimi."""

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        box = self.ids.modules_box
        box.clear_widgets()

        for idx, module in enumerate(app.modules):
            unlocked = app.is_module_unlocked(idx)
            best_score = app.get_module_best_score(module["id"])
            status = f" | En iyi skor: {best_score}%" if best_score > 0 else ""

            text = f"{module['id']}. {module['title']} ({module['level']}){status}"
            btn = Button(
                text=text,
                size_hint_y=None,
                height="60dp",
                disabled=not unlocked,
                halign="left",
            )
            btn.module_index = idx
            btn.bind(on_release=self.open_module)
            box.add_widget(btn)

            if not unlocked:
                info = Label(
                    text="[i]Önceki modülden en az %70 almalısın.[/i]",
                    markup=True,
                    size_hint_y=None,
                    height="25dp",
                    font_size="12sp",
                )
                box.add_widget(info)

    def open_module(self, button):
        app = App.get_running_app()
        module_index = button.module_index
        detail = self.manager.get_screen("module_detail")
        detail.load_module(module_index)
        self.manager.current = "module_detail"


class ModuleDetailScreen(Screen):
    """Seçilen modülün açıklaması, kelime/hikaye/quiz giriş noktaları."""

    module_index = NumericProperty(0)

    def load_module(self, module_index):
        self.module_index = module_index
        app = App.get_running_app()
        module = app.modules[module_index]

        self.ids.module_title.text = module["title"]
        self.ids.module_desc.text = module.get("description", "")

        story = module.get("story")
        if story:
            intro_text = f"[b]{story.get('title', '')}[/b]\n{story.get('intro_tr', '')}"
            self.ids.story_intro.text = intro_text
            self.ids.story_intro.markup = True
        else:
            self.ids.story_intro.text = "Bu modüle henüz hikaye eklenmemiş."

        self.ids.info_label.text = (
            "1) Kelimeleri kart kart inceleyebilirsin.\n"
            "2) Hikaye özetini okuyup dinleyebilirsin.\n"
            "3) Modül sınavına gir; %70 ve üzeri alırsan bir sonraki modül açılır."
        )

    def open_words(self):
        screen = self.manager.get_screen("word_study")
        screen.load_module(self.module_index)
        self.manager.current = "word_study"

    def open_story(self):
        screen = self.manager.get_screen("story")
        screen.load_module(self.module_index)
        self.manager.current = "story"

    def start_quiz(self):
        screen = self.manager.get_screen("quiz")
        screen.start_quiz(self.module_index)
        self.manager.current = "quiz"


class WordStudyScreen(Screen):
    """Kelimeleri kart mantığıyla gösterir."""

    module_index = NumericProperty(0)
    word_index = NumericProperty(0)
    has_words = BooleanProperty(False)

    def load_module(self, module_index):
        self.module_index = module_index
        self.word_index = 0
        self.show_current_word()

    def get_words(self):
        app = App.get_running_app()
        module = app.modules[self.module_index]
        return module.get("words", [])

    def show_current_word(self):
        words = self.get_words()
        if not words:
            self.has_words = False
            self.ids.word_label.text = "Bu modüle henüz kelime eklenmemiş."
            self.ids.example_label.text = ""
            return

        self.has_words = True
        if self.word_index < 0:
            self.word_index = 0
        if self.word_index >= len(words):
            self.word_index = len(words) - 1

        w = words[self.word_index]
        self.ids.word_label.text = (
            f"{self.word_index+1}/{len(words)} - "
            f"[b]{w['word']}[/b] = {w['meaning_tr']}"
        )
        self.ids.word_label.markup = True
        self.ids.example_label.text = w.get("example", "")

    def next_word(self):
        if not self.has_words:
            return
        self.word_index += 1
        if self.word_index >= len(self.get_words()):
            self.word_index = 0
        self.show_current_word()

    def prev_word(self):
        if not self.has_words:
            return
        self.word_index -= 1
        if self.word_index < 0:
            self.word_index = len(self.get_words()) - 1
        self.show_current_word()

    def speak_word(self):
        if not self.has_words or tts is None:
            self.ids.example_label.text = "TTS (sesli okuma) bu cihazda aktif değil."
            return
        w = self.get_words()[self.word_index]
        tts.speak(w["word"])


class StoryScreen(Screen):
    """Hikaye özetini gösterir, istenirse TTS ile okur."""

    module_index = NumericProperty(0)

    def load_module(self, module_index):
        self.module_index = module_index
        app = App.get_running_app()
        module = app.modules[module_index]
        story = module.get("story")

        if not story:
            self.ids.story_title.text = "Hikaye Yok"
            self.ids.story_text.text = "Bu modüle hikaye eklenmemiş."
            return

        self.ids.story_title.text = story.get("title", "")
        paragraphs = story.get("paragraphs", [])
        self.ids.story_text.text = "\n\n".join(paragraphs)

    def speak_story(self):
        if tts is None:
            self.ids.story_text.text += (
                "\n\n[NOT] Bu cihazda TTS (text-to-speech) desteği yok."
            )
            self.ids.story_text.markup = False
            return

        text = self.ids.story_text.text
        if text.strip():
            tts.speak(text)


class QuizScreen(Screen):
    """Modül sınavı: çoktan seçmeli, doğru/yanlış, yazılı."""

    module_index = NumericProperty(0)
    questions = ListProperty([])
    current_index = NumericProperty(0)
    score = NumericProperty(0)

    question_text = StringProperty("")
    question_type = StringProperty("choice")
    options = ListProperty([])
    correct_answer = StringProperty("")
    correct_bool = BooleanProperty(False)

    def start_quiz(self, module_index):
        app = App.get_running_app()
        self.module_index = module_index
        module = app.modules[module_index]
        self.questions = module.get("quiz", [])
        self.current_index = 0
        self.score = 0
        self.ids.answer_input.text = ""
        self.ids.feedback.text = ""
        self.ids.options_box.clear_widgets()

        if not self.questions:
            self.question_text = "Bu modül için sınav sorusu yok."
            self.options = []
            return

        self.show_current_question()

    def show_current_question(self):
        self.ids.answer_input.text = ""
        self.ids.feedback.text = ""
        self.ids.options_box.clear_widgets()

        if self.current_index >= len(self.questions):
            self.finish_quiz()
            return

        q = self.questions[self.current_index]
        self.question_type = q["type"]
        self.question_text = q["question"]

        if self.question_type == "choice":
            self.options = q["options"]
            self.correct_answer = q["options"][q["answer_index"]]
            for opt in self.options:
                btn = Button(
                    text=opt,
                    size_hint_y=None,
                    height="40dp",
                )
                btn.bind(on_release=lambda instance, txt=opt: self.submit_choice_answer(txt))
                self.ids.options_box.add_widget(btn)

        elif self.question_type == "tf":
            self.options = ["True", "False"]
            self.correct_bool = bool(q["answer_bool"])
            for opt in self.options:
                btn = Button(
                    text=opt,
                    size_hint_y=None,
                    height="40dp",
                )
                btn.bind(on_release=lambda instance, txt=opt: self.submit_tf_answer(txt))
                self.ids.options_box.add_widget(btn)

        elif self.question_type == "input":
            self.options = []
            self.correct_answer = q["answer"]

    def submit_choice_answer(self, selected):
        if selected.strip().lower() == self.correct_answer.strip().lower():
            self.score += 1
            self.ids.feedback.text = "✅ Doğru!"
        else:
            self.ids.feedback.text = f"❌ Yanlış! Doğru: {self.correct_answer}"
        self.next_question()

    def submit_tf_answer(self, selected):
        user_bool = True if selected.lower() == "true" else False
        if user_bool == self.correct_bool:
            self.score += 1
            self.ids.feedback.text = "✅ Doğru!"
        else:
            correct_text = "True" if self.correct_bool else "False"
            self.ids.feedback.text = f"❌ Yanlış! Doğru: {correct_text}"
        self.next_question()

    def submit_input_answer(self):
        if self.question_type != "input":
            return
        answer = self.ids.answer_input.text.strip()
        if not answer:
            self.ids.feedback.text = "Lütfen bir cevap yaz."
            return
        if answer.lower() == self.correct_answer.strip().lower():
            self.score += 1
            self.ids.feedback.text = "✅ Doğru!"
        else:
            self.ids.feedback.text = f"❌ Yanlış! Doğru: {self.correct_answer}"
        self.next_question()

    def next_question(self):
        self.current_index += 1
        if self.current_index < len(self.questions):
            self.show_current_question()
        else:
            self.finish_quiz()

    def finish_quiz(self):
        total = len(self.questions)
        percent = int((self.score / total) * 100) if total else 0

        app = App.get_running_app()
        module = app.modules[self.module_index]
        app.update_progress(module["id"], percent)

        result = self.manager.get_screen("result")
        result.show_result(module["title"], percent)
        self.manager.current = "result"


class ResultScreen(Screen):
    """Sınav sonucu ve açıklama."""

    def show_result(self, module_title, percent):
        app = App.get_running_app()
        self.ids.result_title.text = f"Modül: {module_title}"
        self.ids.result_score.text = f"Skor: {percent}%"

        if percent >= app.pass_score:
            msg = (
                f"Tebrikler, modülü başarıyla geçtin!\n"
                f"Geçme notu: {app.pass_score}%, senin notun: {percent}%.\n"
                "Bir sonraki modül (varsa) açıldı."
            )
        else:
            msg = (
                f"Bu modülden geçmek için en az {app.pass_score}% alman gerekiyor.\n"
                f"Şu an aldığın not: {percent}%.\n"
                "İstersen modülü tekrar çalışıp sınavı yeniden çözebilirsin."
            )
        self.ids.result_message.text = msg


# ---------- ANA UYGULAMA ----------

class EnglishLearningApp(App):
    modules = ListProperty([])
    pass_score = NumericProperty(70)
    progress = DictProperty({})  # {"module_id_str": best_score_int}

    def build(self):
        self.title = "İngilizce Öğren (Kelime + Hikaye + Sınav)"
        self.load_modules()
        self.load_progress()
        kv_path = os.path.join(BASE_DIR, "english_app.kv")
        return Builder.load_file(kv_path)

    # ---- data ----
    def load_modules(self):
        with open(MODULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.pass_score = data.get("pass_score", 70)
        self.modules = data.get("modules", [])

    def get_progress_path(self):
        user_dir = self.user_data_dir
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, "progress.json")

    def load_progress(self):
        path = self.get_progress_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.progress = json.load(f)
        else:
            self.progress = {}

    def save_progress(self):
        path = self.get_progress_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def update_progress(self, module_id, score):
        key = str(module_id)
        old = self.progress.get(key, 0)
        if score > old:
            self.progress[key] = score
            self.save_progress()

    def get_module_best_score(self, module_id):
        return int(self.progress.get(str(module_id), 0))

    # ---- kilit sistemi (A modeli, %70) ----
    def is_module_unlocked(self, module_index: int) -> bool:
        if module_index == 0:
            return True
        prev_module = self.modules[module_index - 1]
        prev_id = str(prev_module["id"])
        best_prev_score = self.progress.get(prev_id, 0)
        return best_prev_score >= self.pass_score


if __name__ == "__main__":
    EnglishLearningApp().run()
