import threading
import traceback
import customtkinter as ctk

from blender_bridge import check_blender_listener, send_code_to_blender
from code_cleaner import validate_code
from ollama_engine import check_ollama, clean_code, generate_blender_code, get_models
from agent import run_agent


class BlenderAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chandu Prompt Studio")
        self.geometry("1180x760")
        self.minsize(980, 680)

        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#1f1f1f")

        self.font_ui = ctk.CTkFont(family="Bahnschrift", size=14)
        self.font_title = ctk.CTkFont(family="Bahnschrift", size=22, weight="bold")
        self.font_code = ctk.CTkFont(family="Consolas", size=13)

        self.accent = "#f58f00"
        self.panel = "#2a2a2a"
        self.panel_alt = "#242424"
        self.text = "#f2f2f2"
        self.active_section = "Dashboard"
        self.project_history = []
        self.section_profiles = {
            "Dashboard": {
                "subtitle": "Studio overview",
                "header_action": "Export Pack",
                "prompt_title": "Prompt Workspace",
                "default_prompt": "Create a stylized low-poly spaceship with orange emissive lights, add floor, camera, and key light.",
                "presets": [
                    ("Character", "Create a game-ready fantasy character in Blender with clean topology, armor, cloth folds, and a neutral standing pose."),
                    ("Gear System", "Create a realistic mechanical watch gear system in Blender with interlocking brass gears, a dark metal baseplate, and studio lighting."),
                    ("Environment", "Create a stylized sci-fi environment in Blender with modular structures, atmospheric lighting, and game-ready composition."),
                ],
                "gallery_title": "Project Gallery",
                "gallery": [
                    ("Latest Output", "Recently generated Blender scene or asset"),
                    ("Characters", "Armored heroes and rig-ready models"),
                    ("Gears", "Mechanical systems and watch parts"),
                ],
            },
            "Characters": {
                "subtitle": "Character workspace",
                "header_action": "Character Pack",
                "prompt_title": "Character Prompt Workspace",
                "default_prompt": "Create a game-ready fantasy character in Blender with clean topology, armor, cloth folds, and a neutral standing pose.",
                "presets": [
                    ("Warrior", "Create a fantasy warrior character with armor, cape, sword, and shield, ready for a third-person game."),
                    ("Sci-Fi Hero", "Create a futuristic armored hero with glowing accents, game-ready topology, and a strong pose."),
                    ("Creature", "Create a stylized fantasy creature with clean topology, expressive silhouette, and rig-ready structure."),
                ],
                "gallery_title": "Character Library",
                "gallery": [
                    ("Armored Hero", "Game-ready warrior with clean topology and neutral stance"),
                    ("NPC Soldier", "Efficient low-poly character for crowd scenes"),
                    ("Boss Enemy", "Striking silhouette with strong fantasy details"),
                ],
            },
            "Environments": {
                "subtitle": "Environment workspace",
                "header_action": "Scene Pack",
                "prompt_title": "Environment Prompt Workspace",
                "default_prompt": "Create a stylized sci-fi environment in Blender with modular structures, atmospheric lighting, and game-ready composition.",
                "presets": [
                    ("Sci-Fi Hall", "Create a modular sci-fi hallway environment with strong lighting, repeating panels, and game-ready layout."),
                    ("Forest", "Create a stylized fantasy forest scene with layered trees, atmospheric fog, and cinematic lighting."),
                    ("Street", "Create a game environment of a small street with storefronts, props, and natural composition."),
                ],
                "gallery_title": "Environment Gallery",
                "gallery": [
                    ("Sci-Fi Hall", "Modular corridor with atmospheric lighting and reusable pieces"),
                    ("Forest Edge", "Stylized outdoor scene with depth and haze"),
                    ("City Block", "Game-ready urban space with props and signage"),
                ],
            },
            "Gears": {
                "subtitle": "Mechanical workspace",
                "header_action": "Mechanics Pack",
                "prompt_title": "Mechanical Prompt Workspace",
                "default_prompt": "Create a realistic mechanical watch gear system in Blender with interlocking brass gears, a dark metal baseplate, and studio lighting.",
                "presets": [
                    ("Watch Gear", "Create a mechanical watch movement with interlocking brass gears and precise spacing."),
                    ("Engine", "Create a small mechanical engine assembly with pulleys, gears, and metal housing."),
                    ("Robot", "Create a mechanical robot joint system with visible gears and industrial parts."),
                ],
                "gallery_title": "Mechanical Gallery",
                "gallery": [
                    ("Watch Movement", "Precision gear assembly with brass and steel materials"),
                    ("Engine Core", "Compact mechanical blockout with rotating parts"),
                    ("Robot Joint", "Industrial articulation and gear housing"),
                ],
            },
            "Exports": {
                "subtitle": "Export workspace",
                "header_action": "Export Pack",
                "prompt_title": "Export Prompt Workspace",
                "default_prompt": "Prepare the current Blender asset for export with clean topology, separate parts, and game-engine friendly naming.",
                "presets": [
                    ("FBX Ready", "Prepare the scene for FBX export with clean transforms and organized objects."),
                    ("glTF Ready", "Prepare the scene for glTF export with efficient materials and optimized topology."),
                    ("Unreal Ready", "Prepare the asset for Unreal Engine with proper scale, separate parts, and clean hierarchy."),
                ],
                "gallery_title": "Export Targets",
                "gallery": [
                    ("FBX", "Best for broad engine compatibility and animation workflows"),
                    ("glTF", "Efficient format for modern real-time pipelines"),
                    ("Unreal", "Prepared for engine import and scene setup"),
                ],
            },
        }

        self.current_models = []
        self._build_ui()
        self._set_busy(False)

        self.refresh_models()
        self.poll_status()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(self, fg_color="#212121", corner_radius=0, width=260)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="CHANDU\nGAME\nPROMPT\nSTUDIO",
            justify="left",
            font=ctk.CTkFont(family="Bahnschrift", size=24, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=18, pady=(22, 12), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Prompt-to-Blender workspace\nfor game assets and scenes",
            justify="left",
            font=ctk.CTkFont(family="Bahnschrift", size=13),
            text_color="#d4d4d4",
        ).grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

        self.nav_buttons = []
        for index, label in enumerate(["Dashboard", "Characters", "Environments", "Gears", "Exports"]):
            button = ctk.CTkButton(
                sidebar,
                text=label,
                command=lambda value=label: self.set_section(value),
                fg_color=self.accent if index == 0 else "#303030",
                hover_color="#ffad32" if index == 0 else "#3b3b3b",
                text_color="#121212" if index == 0 else self.text,
                font=ctk.CTkFont(family="Bahnschrift", size=14, weight="bold" if index == 0 else "normal"),
                height=40,
            )
            button.grid(row=index + 2, column=0, padx=18, pady=(0, 10), sticky="ew")
            self.nav_buttons.append(button)

        studio_card = ctk.CTkFrame(sidebar, fg_color="#2b2b2b", corner_radius=12)
        studio_card.grid(row=7, column=0, padx=18, pady=(18, 12), sticky="ew")
        studio_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            studio_card,
            text="Studio Goals",
            font=ctk.CTkFont(family="Bahnschrift", size=15, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            studio_card,
            text="• Game-ready assets\n• Blender automation\n• Unreal pipeline later",
            justify="left",
            font=self.font_ui,
            text_color=self.text,
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, rowspan=2, padx=14, pady=14, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(content, fg_color=self.panel, corner_radius=14)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=0)
        header.grid_rowconfigure(2, weight=0)

        self.header_title = ctk.CTkLabel(
            header,
            text="Chandu Prompt Studio",
            font=self.font_title,
            text_color=self.accent,
        )
        self.header_title.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="w")

        self.header_subtitle = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(family="Bahnschrift", size=13),
            text_color="#d5d5d5",
        )
        self.header_subtitle.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="w")

        header_action = ctk.CTkButton(
            header,
            text="Export Pack",
            fg_color=self.accent,
            hover_color="#ffad32",
            text_color="#121212",
            font=ctk.CTkFont(family="Bahnschrift", size=13, weight="bold"),
            width=130,
        )
        self.header_action = header_action
        header_action.grid(row=0, column=2, rowspan=2, padx=(8, 16), pady=14, sticky="e")

        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.grid(row=0, column=1, rowspan=2, padx=8, pady=14, sticky="e")

        self.ollama_status = ctk.CTkLabel(
            status_frame,
            text="Ollama: checking",
            font=self.font_ui,
            text_color="#f1c40f",
        )
        self.ollama_status.grid(row=0, column=0, pady=(0, 4), sticky="e")

        self.blender_status = ctk.CTkLabel(
            status_frame,
            text="Blender: checking",
            font=self.font_ui,
            text_color="#f1c40f",
        )
        self.blender_status.grid(row=1, column=0, sticky="e")

        model_strip = ctk.CTkFrame(header, fg_color=self.panel_alt, corner_radius=12)
        model_strip.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="ew")
        model_strip.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            model_strip,
            text="Model",
            font=ctk.CTkFont(family="Bahnschrift", size=13, weight="bold"),
            text_color=self.text,
        ).grid(row=0, column=0, padx=(12, 8), pady=12, sticky="w")

        self.model_box = ctk.CTkComboBox(
            model_strip,
            values=["loading..."],
            width=360,
            font=self.font_ui,
            dropdown_font=self.font_ui,
            fg_color="#343434",
            button_color=self.accent,
            button_hover_color="#ffad32",
            border_color="#4a4a4a",
        )
        self.model_box.grid(row=0, column=1, padx=6, pady=12, sticky="ew")

        self.refresh_button = ctk.CTkButton(
            model_strip,
            text="Refresh Models",
            command=self.refresh_models,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            font=self.font_ui,
            width=140,
        )
        self.refresh_button.grid(row=0, column=2, padx=(8, 12), pady=12, sticky="e")

        body = ctk.CTkFrame(content, fg_color="transparent")
        body.grid(row=3, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=0)
        body.grid_rowconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        prompt_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=14)
        prompt_panel.grid(row=0, column=0, rowspan=3, padx=(0, 8), sticky="nsew")
        prompt_panel.grid_rowconfigure(2, weight=1)
        prompt_panel.grid_columnconfigure(0, weight=1)

        self.prompt_panel_title_label = ctk.CTkLabel(
            prompt_panel,
            text="Prompt Workspace",
            font=ctk.CTkFont(family="Bahnschrift", size=18, weight="bold"),
            text_color=self.accent,
        )
        self.prompt_panel_title_label.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        preset_row = ctk.CTkFrame(prompt_panel, fg_color="transparent")
        preset_row.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        preset_row.grid_columnconfigure((0, 1, 2), weight=1)
        self.preset_buttons = []

        for index in range(3):
            button = ctk.CTkButton(
                preset_row,
                text="Preset",
                command=lambda value="": self.load_prompt_preset(value),
                fg_color="#353535",
                hover_color="#434343",
                font=ctk.CTkFont(family="Bahnschrift", size=13),
                height=34,
            )
            button.grid(row=0, column=index, padx=(0 if index == 0 else 6, 0 if index == 2 else 6), sticky="ew")
            self.preset_buttons.append(button)

        self.prompt_text = ctk.CTkTextbox(
            prompt_panel,
            font=self.font_ui,
            fg_color=self.panel_alt,
            text_color=self.text,
            border_color="#3a3a3a",
            border_width=1,
        )
        self.prompt_text.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="nsew")
        self.prompt_text.insert(
            "1.0",
            "Create a stylized low-poly spaceship with orange emissive lights, add floor, camera, and key light.",
        )

        button_row = ctk.CTkFrame(prompt_panel, fg_color="transparent")
        button_row.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")
        button_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.generate_button = ctk.CTkButton(
            button_row,
            text="Generate Code",
            command=self.on_generate_only,
            fg_color="#4e4e4e",
            hover_color="#606060",
            font=self.font_ui,
        )
        self.generate_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.run_button = ctk.CTkButton(
            button_row,
            text="Run Current Code",
            command=self.on_run_current,
            fg_color="#5a5a5a",
            hover_color="#6e6e6e",
            font=self.font_ui,
        )
        self.run_button.grid(row=0, column=1, padx=3, sticky="ew")

        self.generate_run_button = ctk.CTkButton(
            button_row,
            text="Generate + Run in Blender",
            command=self.on_generate_and_run,
            fg_color=self.accent,
            hover_color="#ffac2f",
            text_color="#121212",
            font=ctk.CTkFont(family="Bahnschrift", size=14, weight="bold"),
        )
        self.generate_run_button.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        gallery_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=14)
        gallery_panel.grid(row=0, column=1, padx=(8, 0), pady=(0, 8), sticky="nsew")
        gallery_panel.grid_columnconfigure(0, weight=1)

        self.gallery_title_label = ctk.CTkLabel(
            gallery_panel,
            text="Project Gallery",
            font=ctk.CTkFont(family="Bahnschrift", size=16, weight="bold"),
            text_color=self.accent,
        )
        self.gallery_title_label.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")

        self.gallery_cards = []
        for index in range(3):
            item = ctk.CTkFrame(gallery_panel, fg_color="#313131", corner_radius=10)
            item.grid(row=index + 1, column=0, padx=12, pady=6, sticky="ew")
            item.grid_columnconfigure(0, weight=1)
            title_label = ctk.CTkLabel(
                item,
                text="Item",
                font=ctk.CTkFont(family="Bahnschrift", size=13, weight="bold"),
                text_color=self.text,
            )
            title_label.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
            desc_label = ctk.CTkLabel(
                item,
                text="Description",
                font=ctk.CTkFont(family="Bahnschrift", size=12),
                text_color="#c9c9c9",
            )
            desc_label.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")
            self.gallery_cards.append((item, title_label, desc_label))

        export_strip = ctk.CTkFrame(gallery_panel, fg_color="transparent")
        export_strip.grid(row=4, column=0, padx=12, pady=(6, 12), sticky="ew")
        export_strip.grid_columnconfigure((0, 1, 2), weight=1)

        for index, label in enumerate(["FBX", "glTF", "Unreal"]):
            ctk.CTkButton(
                export_strip,
                text=f"Export {label}",
                command=lambda value=label: self.quick_export(value),
                fg_color="#3b3b3b",
                hover_color="#4a4a4a",
                font=ctk.CTkFont(family="Bahnschrift", size=12),
            ).grid(row=0, column=index, padx=(0 if index == 0 else 6, 0 if index == 2 else 6), sticky="ew")

        code_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=14)
        code_panel.grid(row=1, column=1, padx=(8, 0), sticky="nsew")
        code_panel.grid_rowconfigure(1, weight=1)
        code_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            code_panel,
            text="Generated Blender Python",
            font=ctk.CTkFont(family="Bahnschrift", size=18, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.code_text = ctk.CTkTextbox(
            code_panel,
            font=self.font_code,
            fg_color="#1e1e1e",
            text_color="#f6f6f6",
            border_color="#3a3a3a",
            border_width=1,
        )
        self.code_text.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        log_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=14)
        log_panel.grid(row=2, column=1, padx=(8, 0), pady=(8, 0), sticky="nsew")
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_panel,
            text="Activity Log",
            font=ctk.CTkFont(family="Bahnschrift", size=16, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.log_text = ctk.CTkTextbox(
            log_panel,
            font=self.font_ui,
            fg_color=self.panel_alt,
            text_color=self.text,
            height=180,
            border_color="#3a3a3a",
            border_width=1,
        )
        self.log_text.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        
    def _create_summary_card(self, parent, column, title, text):
        card = ctk.CTkFrame(parent, fg_color=self.panel, corner_radius=12)
        card.grid(row=0, column=column, padx=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family="Bahnschrift", size=14, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            card,
            text=text,
            font=self.font_ui,
            text_color=self.text,
            justify="left",
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")

    def _get_section_profile(self, section):
        return self.section_profiles.get(section, self.section_profiles["Dashboard"])

    def _shorten_text(self, text, limit=72):
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

    def _gallery_items_for_section(self, section):
        profile = self._get_section_profile(section)
        items = list(profile["gallery"])
        section_history = [item for item in self.project_history if item["section"] == section]
        if section_history:
            latest = section_history[0]
            items = [(latest["title"], latest["description"])] + items

        unique_items = []
        seen_titles = set()
        for title, desc in items:
            if title in seen_titles:
                continue
            seen_titles.add(title)
            unique_items.append((title, desc))
        return unique_items[: len(self.gallery_cards)]

    def _apply_section_profile(self, section):
        profile = self._get_section_profile(section)

        if hasattr(self, "header_subtitle"):
            self.header_subtitle.configure(text=profile["subtitle"])

        if hasattr(self, "header_action"):
            self.header_action.configure(text=profile["header_action"])

        if hasattr(self, "prompt_panel_title_label"):
            self.prompt_panel_title_label.configure(text=profile["prompt_title"])

        if hasattr(self, "gallery_title_label"):
            self.gallery_title_label.configure(text=profile["gallery_title"])

        if hasattr(self, "preset_buttons"):
            for button, (preset_name, preset_prompt) in zip(self.preset_buttons, profile["presets"]):
                button.configure(
                    text=preset_name,
                    command=lambda value=preset_prompt: self.load_prompt_preset(value),
                )

        if hasattr(self, "prompt_text"):
            self._set_text(self.prompt_text, profile["default_prompt"])

        self._sync_gallery_cards(section)

    def _sync_gallery_cards(self, section):
        if not hasattr(self, "gallery_cards"):
            return

        for index, (title, desc) in enumerate(self._gallery_items_for_section(section)):
            _, title_label, desc_label = self.gallery_cards[index]
            title_label.configure(text=title)
            desc_label.configure(text=desc)

        for index in range(len(self._gallery_items_for_section(section)), len(self.gallery_cards)):
            _, title_label, desc_label = self.gallery_cards[index]
            title_label.configure(text="")
            desc_label.configure(text="")

    def _record_generation(self, section, prompt, model):
        title = f"{section} • {model}"
        description = self._shorten_text(prompt)
        self.project_history.insert(0, {
            "section": section,
            "title": title,
            "description": description,
        })
        self.project_history = self.project_history[:12]
        if section == self.active_section:
            self._sync_gallery_cards(section)

    def set_section(self, section):
        self.active_section = section
        self._apply_section_profile(section)

        for button in getattr(self, "nav_buttons", []):
            active = button.cget("text") == section
            button.configure(
                fg_color=self.accent if active else "#303030",
                hover_color="#ffad32" if active else "#3b3b3b",
                text_color="#121212" if active else self.text,
            )

        if section != "Dashboard":
            self.log(f"Switched to {section} workspace")

    def load_prompt_preset(self, prompt):
        self._set_text(self.prompt_text, prompt)
        self.log("Loaded prompt preset into the workspace.")

    def quick_export(self, format_name):
        self.log(f"Queued export for {format_name}.")

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for widget_name in ("generate_button", "run_button", "generate_run_button", "refresh_button"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.configure(state=state)

    def _set_text(self, widget, text):
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    def _append_text(self, widget, text):
        widget.insert("end", text)
        widget.see("end")

    def _get_prompt(self):
        return self.prompt_text.get("1.0", "end").strip()

    def _get_code(self):
        return self.code_text.get("1.0", "end").strip()

    def log(self, message):
        self._append_text(self.log_text, f"{message}\n")

    def poll_status(self):
        try:
            ollama_ok = check_ollama()
            blender_ok = check_blender_listener()

            ollama_status = getattr(self, "ollama_status", None)
            blender_status = getattr(self, "blender_status", None)

            if ollama_status is not None:
                if ollama_ok:
                    ollama_status.configure(text="Ollama: online", text_color="#44d17a")
                else:
                    ollama_status.configure(text="Ollama: offline", text_color="#ff6363")

            if blender_status is not None:
                if blender_ok:
                    blender_status.configure(text="Blender: connected", text_color="#44d17a")
                else:
                    blender_status.configure(text="Blender: waiting", text_color="#f1c40f")
        finally:
            self.after(2500, self.poll_status)

    def refresh_models(self):
        def worker():
            models = get_models()

            def update_ui():
                self.current_models = models
                if models:
                    self.model_box.configure(values=models)
                    self.model_box.set(models[0])
                    self.log(f"Loaded {len(models)} model(s) from Ollama.")
                else:
                    self.model_box.configure(values=["No models found"])
                    self.model_box.set("No models found")
                    self.log("No Ollama models found. Pull one with: ollama pull llama3.1")

            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def on_generate_only(self):
        self._run_generation(auto_send=False)

    def on_generate_and_run(self):
        self._run_generation(auto_send=True)

    def _run_generation(self, auto_send):
        prompt = self._get_prompt()
        model = self.model_box.get().strip()
        section = self.active_section

        if not prompt:
            self.log("Prompt is empty.")
            return

        if not model or model == "No models found":
            self.log("Pick a valid Ollama model first.")
            return

        self._set_busy(True)
        self._set_text(self.code_text, "")
        self.log(f"Generating code with model: {model}")

        def on_token(token):
            self.after(0, lambda: self._append_text(self.code_text, token))

        def on_status(message):
            self.after(0, lambda: self.log(message))

        def on_scene(_state):
            return None

        def on_code(code):
            self.after(0, lambda: self._set_text(self.code_text, code))

        def on_success(message):
            self.after(0, lambda: self.log(message))

        def on_error(message):
            self.after(0, lambda: self.log(f"Error: {message}"))

        def on_retry(attempt, error_message):
            self.after(0, lambda: self.log(f"Retry {attempt}: {error_message}"))

        def worker():
            try:
                if auto_send:
                    callbacks = {
                        "on_status": on_status,
                        "on_scene": on_scene,
                        "on_code": on_code,
                        "on_plan_token": on_token,
                        "on_code_token": on_token,
                        "on_fix_token": on_token,
                        "on_success": on_success,
                        "on_error": on_error,
                        "on_retry": on_retry,
                    }
                    success = run_agent(prompt, model, callbacks)
                    if not success:
                        raise RuntimeError("Autonomous agent failed to complete the Blender run.")
                    cleaned = self._get_code()
                else:
                    generated = generate_blender_code(prompt=prompt, model=model, on_token=on_token)
                    cleaned = clean_code(generated)

                ok, err = validate_code(cleaned)
                if not ok:
                    raise RuntimeError(f"Generated code is invalid: {err}")
                
                if err:
                    self.after(0, lambda: self.log(f"⚠ {err}"))

                self.after(0, lambda: self._set_text(self.code_text, cleaned))
                self.after(0, lambda: self.log("Code generated and validated."))
                self.after(0, lambda: self._record_generation(section, prompt, model))

            except Exception as exc:
                self.after(0, lambda: self.log(f"Error: {exc}"))
                self.after(0, lambda: self.log(traceback.format_exc()))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def on_run_current(self):
        code = self._get_code()

        if not code:
            self.log("No code available. Generate code first.")
            return

        ok, err = validate_code(code)
        if not ok:
            self.log(f"Current code has syntax error: {err}")
            return
        
        if err:
            self.log(f"⚠ {err}")

        self._set_busy(True)
        self.log("Sending current code to Blender...")

        def worker():
            try:
                result = send_code_to_blender(code)
                self.after(0, lambda: self.log(f"Blender response: {result}"))
            except Exception as exc:
                self.after(0, lambda: self.log(f"Error: {exc}"))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = BlenderAIApp()
    app.mainloop()
