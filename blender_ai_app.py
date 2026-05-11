import threading
import traceback
import customtkinter as ctk

from blender_bridge import check_blender_listener, send_code_to_blender
from code_cleaner import validate_code
from ollama_engine import check_ollama, clean_code, generate_blender_code, get_models


class BlenderAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chandu AI Lab - Blender Copilot")
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

        self.current_models = []
        self._build_ui()
        self._set_busy(False)

        self.refresh_models()
        self.poll_status()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color=self.panel, corner_radius=10)
        header.grid(row=0, column=0, padx=14, pady=(12, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            header,
            text="Chandu AI Lab  |  Blender Prompt Studio",
            font=self.font_title,
            text_color=self.accent,
        ).grid(row=0, column=0, padx=14, pady=10, sticky="w")

        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        self.ollama_status = ctk.CTkLabel(
            status_frame, text="Ollama: checking", font=self.font_ui, text_color="#f1c40f"
        )
        self.ollama_status.grid(row=0, column=0, padx=(0, 12))

        self.blender_status = ctk.CTkLabel(
            status_frame, text="Blender: checking", font=self.font_ui, text_color="#f1c40f"
        )
        self.blender_status.grid(row=0, column=1)

        controls = ctk.CTkFrame(self, fg_color=self.panel, corner_radius=10)
        controls.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
        controls.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(controls, text="Model", font=self.font_ui).grid(
            row=0, column=0, padx=(14, 8), pady=12
        )

        self.model_box = ctk.CTkComboBox(
            controls,
            values=["loading..."],
            width=360,
            font=self.font_ui,
            dropdown_font=self.font_ui,
            fg_color=self.panel_alt,
            button_color=self.accent,
            button_hover_color="#ffad32",
            border_color="#3a3a3a",
        )
        self.model_box.grid(row=0, column=1, padx=6, pady=12, sticky="w")

        self.refresh_button = ctk.CTkButton(
            controls,
            text="Refresh Models",
            command=self.refresh_models,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            font=self.font_ui,
            width=140,
        )
        self.refresh_button.grid(row=0, column=2, padx=8, pady=12, sticky="w")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        prompt_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=10)
        prompt_panel.grid(row=0, column=0, rowspan=2, padx=(0, 8), sticky="nsew")
        prompt_panel.grid_rowconfigure(1, weight=1)
        prompt_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            prompt_panel,
            text="Prompt",
            font=ctk.CTkFont(family="Bahnschrift", size=18, weight="bold"),
            text_color=self.accent,
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.prompt_text = ctk.CTkTextbox(
            prompt_panel,
            font=self.font_ui,
            fg_color=self.panel_alt,
            text_color=self.text,
            border_color="#3a3a3a",
            border_width=1,
        )
        self.prompt_text.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="nsew")
        self.prompt_text.insert(
            "1.0",
            "Create a stylized low-poly spaceship with orange emissive lights, add floor, camera, and key light.",
        )

        button_row = ctk.CTkFrame(prompt_panel, fg_color="transparent")
        button_row.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
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

        code_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=10)
        code_panel.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
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

        log_panel = ctk.CTkFrame(body, fg_color=self.panel, corner_radius=10)
        log_panel.grid(row=1, column=1, padx=(8, 0), pady=(8, 0), sticky="nsew")
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

    def _set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.generate_button.configure(state=state)
        self.run_button.configure(state=state)
        self.generate_run_button.configure(state=state)
        self.refresh_button.configure(state=state)

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

            if ollama_ok:
                self.ollama_status.configure(text="Ollama: online", text_color="#44d17a")
            else:
                self.ollama_status.configure(text="Ollama: offline", text_color="#ff6363")

            if blender_ok:
                self.blender_status.configure(text="Blender: connected", text_color="#44d17a")
            else:
                self.blender_status.configure(text="Blender: waiting", text_color="#f1c40f")
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

        def worker():
            try:
                generated = generate_blender_code(prompt=prompt, model=model, on_token=on_token)
                cleaned = clean_code(generated)

                ok, err = validate_code(cleaned)
                if not ok:
                    raise RuntimeError(f"Generated code is invalid: {err}")
                
                if err:
                    self.after(0, lambda: self.log(f"⚠ {err}"))

                self.after(0, lambda: self._set_text(self.code_text, cleaned))
                self.after(0, lambda: self.log("Code generated and validated."))

                if auto_send:
                    if not check_blender_listener():
                        raise ConnectionError(
                            "Blender listener is not reachable. Run blender_listener.py inside Blender Scripting tab."
                        )
                    result = send_code_to_blender(cleaned)
                    self.after(0, lambda: self.log(f"Blender response: {result}"))

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
