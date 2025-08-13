# ui_utils.py

import tkinter as tk
from config import Config

class UIUtils:
    @staticmethod
    def create_button(parent: tk.Widget, text: str, command: callable, **kwargs) -> tk.Button:
        # ... (unchanged)

    @staticmethod
    def create_label(parent: tk.Widget, text: str, **kwargs) -> tk.Label:
        # ... (unchanged)
