# config.py

import os

class Config:
    BG_COLOR = "#f3f5fa"
    ACCENT_COLOR = "#1a4971"
    TEXT_COLOR = "#2c3e50"
    FONT = ("Arial", 12)
    FONT_BOLD = ("Arial", 14, "bold")
    FONT_SMALL = ("Arial", 10)
    WINDOW_SIZE_MAIN = "990x800"
    WINDOW_SIZE_WIZARD = "990x620"
    ANSWER_KEY_PATH = os.path.join("database", "answers.json")
    WIZARD_TREE_PATH = os.path.join("database", "wizard.json")
    USER_RESPONSE_PATH = os.path.join("database", "responses.json")
    FUZZY_THRESHOLD = 85
    CONTEXT_WINDOW = 2
