"""
Chandu Prompt Studio — Main App
Blender-style dark UI | Autonomous AI Agent | Real-time streaming
"""

import customtkinter as ctk
import threading
import json
import time
from tkinter import scrolledtext
import tkinter as tk

import ollama_engine
import agent as blender_agent

# ── Theme — Blender-inspired ──────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG         = "#1a1a1a"
PANEL      = "#232323"
PANEL2     = "#2b2b2b"
BORDER     = "#3a3a3a"
ORANGE     = "#e87d0d"
ORANGE_DIM = "#a85d09"
TEXT       = "#d0d0d0"
MUTED      = "#6a6a6a"
GREEN      = "#5fb15a"
RED        = "#c43e3e"
BLUE       = "#4a9eff"
MONO       = ("Consolas", 11)
TITLE_FONT = ("Segoe UI", 10, "bold")

# ── Main App ──────────────────────────────────────────────────────

class ChanduApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chandu Prompt Studio")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        self._agent_running = False
        self._models = []
        self._current_code = ""
        self._scene_state = {}

        self._build_ui()
        self.after(500, self._startup_checks)

    # ── UI Builder ────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚙  CHANDU PROMPT STUDIO",
            font=("Segoe UI", 13, "bold"), text_color=ORANGE
        ).pack(side="left", padx=18, pady=14)

        ctk.CTkLabel(
            header, text="Autonomous Blender Agent  |  Level 3",
            font=("Segoe UI", 10), text_color=MUTED
        ).pack(side="left", padx=0)

        # Blender status
        self.blender_dot = ctk.CTkLabel(header, text="●", text_color=MUTED, font=("Segoe UI", 14))
        self.blender_dot.pack(side="right", padx=(0, 6))
        self.blender_label = ctk.CTkLabel(header, text="BLENDER", font=("Segoe UI", 9), text_color=MUTED)
        self.blender_label.pack(side="right", padx=(0, 2))

        # Ollama status
        self.ollama_dot = ctk.CTkLabel(header, text="●", text_color=MUTED, font=("Segoe UI", 14))
        self.ollama_dot.pack(side="right", padx=(0, 6))
        self.ollama_label = ctk.CTkLabel(header, text="OLLAMA", font=("Segoe UI", 9), text_color=MUTED)
        self.ollama_label.pack(side="right", padx=(16, 2))

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        # Left sidebar
        sidebar = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=0, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Right content
        content = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        content.pack(side="left", fill="both", expand=True, padx=0)
        self._build_content(content)

        # ── Footer ──
        footer = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.status_bar = ctk.CTkLabel(
            footer, text="Ready. Type a prompt and press Run Agent.",
            font=("Segoe UI", 9), text_color=MUTED
        )
        self.status_bar.pack(side="left", padx=14)

        self.retry_label = ctk.CTkLabel(footer, text="", font=("Segoe UI", 9), text_color=ORANGE)
        self.retry_label.pack(side="right", padx=14)

    def _build_sidebar(self, parent):
        pad = {"padx": 12, "pady": 4}

        ctk.CTkLabel(parent, text="AI MODEL", font=("Segoe UI", 9, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=12, pady=(16, 2))

        self.model_var = ctk.StringVar(value="Loading...")
        self.model_menu = ctk.CTkOptionMenu(
            parent, variable=self.model_var,
            values=["Loading..."],
            fg_color=PANEL2, button_color=ORANGE_DIM,
            button_hover_color=ORANGE, text_color=TEXT,
            font=("Segoe UI", 10), width=196
        )
        self.model_menu.pack(**pad)

        ctk.CTkButton(
            parent, text="↻  Refresh Models", fg_color="transparent",
            border_color=BORDER, border_width=1, text_color=MUTED,
            hover_color=PANEL2, font=("Segoe UI", 9), height=26, width=196,
            command=self._refresh_models
        ).pack(**pad)

        # Divider
        ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=12, pady=12
        )

        ctk.CTkLabel(parent, text="BLENDER", font=("Segoe UI", 9, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=12, pady=(0, 2))

        self.blender_host = ctk.CTkEntry(
            parent, placeholder_text="localhost", width=196,
            fg_color=PANEL2, border_color=BORDER, text_color=TEXT,
            font=("Segoe UI", 10)
        )
        self.blender_host.insert(0, "localhost")
        self.blender_host.pack(**pad)

        self.blender_port = ctk.CTkEntry(
            parent, placeholder_text="6789", width=196,
            fg_color=PANEL2, border_color=BORDER, text_color=TEXT,
            font=("Segoe UI", 10)
        )
        self.blender_port.insert(0, "6789")
        self.blender_port.pack(**pad)

        ctk.CTkButton(
            parent, text="⟳  Ping Blender", fg_color="transparent",
            border_color=BORDER, border_width=1, text_color=MUTED,
            hover_color=PANEL2, font=("Segoe UI", 9), height=26, width=196,
            command=self._ping_blender
        ).pack(**pad)

        # Divider
        ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=12, pady=12
        )

        ctk.CTkLabel(parent, text="AGENT SETTINGS", font=("Segoe UI", 9, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=12, pady=(0, 2))

        ctk.CTkLabel(parent, text="Max retries", font=("Segoe UI", 9),
                     text_color=MUTED).pack(anchor="w", padx=12)
        self.retry_var = ctk.IntVar(value=3)
        ctk.CTkSlider(
            parent, from_=1, to=5, number_of_steps=4,
            variable=self.retry_var,
            button_color=ORANGE, button_hover_color=ORANGE_DIM,
            progress_color=ORANGE_DIM, width=196
        ).pack(**pad)

        ctk.CTkFrame(parent, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", padx=12, pady=12
        )

        # Scene stats
        ctk.CTkLabel(parent, text="SCENE", font=("Segoe UI", 9, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=12, pady=(0, 4))

        self.scene_objects = ctk.CTkLabel(parent, text="Objects: —",
                                          font=("Segoe UI", 10), text_color=TEXT)
        self.scene_objects.pack(anchor="w", padx=12)
        self.scene_lights = ctk.CTkLabel(parent, text="Lights: —",
                                         font=("Segoe UI", 10), text_color=TEXT)
        self.scene_lights.pack(anchor="w", padx=12)
        self.scene_cameras = ctk.CTkLabel(parent, text="Cameras: —",
                                          font=("Segoe UI", 10), text_color=TEXT)
        self.scene_cameras.pack(anchor="w", padx=12)

        ctk.CTkButton(
            parent, text="↻  Read Scene", fg_color="transparent",
            border_color=BORDER, border_width=1, text_color=MUTED,
            hover_color=PANEL2, font=("Segoe UI", 9), height=26, width=196,
            command=self._read_scene
        ).pack(padx=12, pady=(8, 4))

    def _build_content(self, parent):
        # ── Prompt area ──
        prompt_frame = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=0)
        prompt_frame.pack(fill="x", padx=0, pady=(0, 1))

        ctk.CTkLabel(
            prompt_frame, text="PROMPT", font=("Segoe UI", 9, "bold"), text_color=MUTED
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self.prompt_input = ctk.CTkTextbox(
            prompt_frame, height=72, fg_color=PANEL2,
            border_color=BORDER, border_width=1,
            text_color=TEXT, font=("Segoe UI", 11),
            wrap="word"
        )
        self.prompt_input.pack(fill="x", padx=12, pady=(0, 4))
        self.prompt_input.insert("1.0", "Create a futuristic AI reactor with spinning gears, glowing rings, and metallic materials")

        btn_row = ctk.CTkFrame(prompt_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        self.run_btn = ctk.CTkButton(
            btn_row, text="▶  RUN AGENT",
            fg_color=ORANGE, hover_color=ORANGE_DIM,
            text_color="#ffffff", font=("Segoe UI", 11, "bold"),
            height=34, width=140, corner_radius=4,
            command=self._run_agent
        )
        self.run_btn.pack(side="left")

        self.stop_btn = ctk.CTkButton(
            btn_row, text="■  STOP",
            fg_color="transparent", border_color=RED, border_width=1,
            text_color=RED, hover_color="#3a1a1a",
            font=("Segoe UI", 10), height=34, width=80, corner_radius=4,
            command=self._stop_agent
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="⎘  Copy Code",
            fg_color="transparent", border_color=BORDER, border_width=1,
            text_color=MUTED, hover_color=PANEL2,
            font=("Segoe UI", 9), height=34, width=100, corner_radius=4,
            command=self._copy_code
        ).pack(side="right")

        ctk.CTkButton(
            btn_row, text="Clear Log",
            fg_color="transparent", border_color=BORDER, border_width=1,
            text_color=MUTED, hover_color=PANEL2,
            font=("Segoe UI", 9), height=34, width=80, corner_radius=4,
            command=self._clear_log
        ).pack(side="right", padx=(0, 6))

        # ── Tabs ──
        tabs = ctk.CTkTabview(
            parent, fg_color=PANEL,
            segmented_button_fg_color=PANEL2,
            segmented_button_selected_color=ORANGE_DIM,
            segmented_button_selected_hover_color=ORANGE,
            segmented_button_unselected_color=PANEL2,
            segmented_button_unselected_hover_color=PANEL,
            text_color=TEXT, border_color=BORDER
        )
        tabs.pack(fill="both", expand=True, padx=0, pady=0)

        tabs.add("Agent Log")
        tabs.add("Generated Code")
        tabs.add("Plan")
        tabs.add("Scene Graph")

        # Agent log
        self.log_box = scrolledtext.ScrolledText(
            tabs.tab("Agent Log"),
            bg="#0f0f0f", fg=TEXT, insertbackground=ORANGE,
            font=MONO, relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.log_box.pack(fill="both", expand=True, padx=2, pady=2)
        self._setup_log_tags()

        # Code preview
        self.code_box = scrolledtext.ScrolledText(
            tabs.tab("Generated Code"),
            bg="#0f0f0f", fg="#ce9178", insertbackground=ORANGE,
            font=("Consolas", 11), relief="flat", bd=0,
            wrap="none", state="disabled"
        )
        self.code_box.pack(fill="both", expand=True, padx=2, pady=2)

        # Plan view
        self.plan_box = scrolledtext.ScrolledText(
            tabs.tab("Plan"),
            bg="#0f0f0f", fg=TEXT, insertbackground=ORANGE,
            font=("Segoe UI", 11), relief="flat", bd=0,
            wrap="word", state="disabled"
        )
        self.plan_box.pack(fill="both", expand=True, padx=2, pady=2)

        # Scene graph
        self.scene_box = scrolledtext.ScrolledText(
            tabs.tab("Scene Graph"),
            bg="#0f0f0f", fg="#9cdcfe", insertbackground=ORANGE,
            font=MONO, relief="flat", bd=0,
            wrap="none", state="disabled"
        )
        self.scene_box.pack(fill="both", expand=True, padx=2, pady=2)

    def _setup_log_tags(self):
        self.log_box.tag_config("ok",     foreground=GREEN)
        self.log_box.tag_config("err",    foreground=RED)
        self.log_box.tag_config("warn",   foreground=ORANGE)
        self.log_box.tag_config("info",   foreground=BLUE)
        self.log_box.tag_config("dim",    foreground=MUTED)
        self.log_box.tag_config("header", foreground=ORANGE, font=("Consolas", 11, "bold"))

    # ── Logging ───────────────────────────────────────────────────

    def _log(self, msg, tag=""):
        self.log_box.configure(state="normal")
        prefix = {"ok": "✓ ", "err": "✗ ", "warn": "⚠ ", "info": "ℹ "}.get(tag, "  ")
        self.log_box.insert("end", f"{prefix}{msg}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _log_token(self, token, box):
        box.configure(state="normal")
        box.insert("end", token)
        box.see("end")
        box.configure(state="disabled")

    def _set_code(self, code):
        self._current_code = code
        self.code_box.configure(state="normal")
        self.code_box.delete("1.0", "end")
        self.code_box.insert("1.0", code)
        self.code_box.configure(state="disabled")

    def _set_scene(self, state):
        self._scene_state = state
        # Update sidebar stats
        self.scene_objects.configure(text=f"Objects: {len(state.get('objects', []))}")
        self.scene_lights.configure(text=f"Lights:  {len(state.get('lights', []))}")
        self.scene_cameras.configure(text=f"Cameras: {len(state.get('cameras', []))}")
        # Update scene graph tab
        self.scene_box.configure(state="normal")
        self.scene_box.delete("1.0", "end")
        self.scene_box.insert("1.0", json.dumps(state, indent=2))
        self.scene_box.configure(state="disabled")

    def _set_status(self, msg):
        self.status_bar.configure(text=msg)
        self._log(msg, "info")

    # ── Status Indicators ─────────────────────────────────────────

    def _set_blender_status(self, ok):
        color = GREEN if ok else MUTED
        self.blender_dot.configure(text_color=color)
        self.blender_label.configure(text_color=color)

    def _set_ollama_status(self, ok):
        color = GREEN if ok else MUTED
        self.ollama_dot.configure(text_color=color)
        self.ollama_label.configure(text_color=color)

    # ── Actions ───────────────────────────────────────────────────

    def _startup_checks(self):
        threading.Thread(target=self._do_startup, daemon=True).start()

    def _do_startup(self):
        # Check Ollama
        ok = ollama_engine.check_ollama()
        self._set_ollama_status(ok)
        if ok:
            self._log("Ollama is running", "ok")
            self._refresh_models()
        else:
            self._log("Ollama not running — start with: ollama serve", "err")

        # Check Blender
        b_ok = blender_agent.ping_blender()
        self._set_blender_status(b_ok)
        if b_ok:
            self._log("Blender listener active", "ok")
            self._read_scene()
        else:
            self._log("Blender not connected — run blender_listener.py inside Blender", "warn")

    def _refresh_models(self):
        def do():
            models = ollama_engine.get_models()
            if models:
                self._models = models
                self.model_menu.configure(values=models)
                self.model_var.set(models[0])
                self._log(f"Found {len(models)} model(s)", "ok")
            else:
                self._log("No models found — pull a model: ollama pull deepseek-coder:6.7b", "warn")
        threading.Thread(target=do, daemon=True).start()

    def _ping_blender(self):
        def do():
            ok = blender_agent.ping_blender()
            self._set_blender_status(ok)
            if ok:
                self._log("Blender ping successful", "ok")
                self._read_scene()
            else:
                self._log("Blender not responding", "err")
        threading.Thread(target=do, daemon=True).start()

    def _read_scene(self):
        def do():
            state = blender_agent.get_scene_state()
            if state:
                self._set_scene(state)
                self._log(f"Scene read: {len(state.get('objects',[]))} objects", "ok")
            else:
                self._log("Could not read scene from Blender", "warn")
        threading.Thread(target=do, daemon=True).start()

    def _stop_agent(self):
        self._agent_running = False
        self._log("Stop requested", "warn")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.plan_box.configure(state="normal")
        self.plan_box.delete("1.0", "end")
        self.plan_box.configure(state="disabled")

    def _copy_code(self):
        if self._current_code:
            self.clipboard_clear()
            self.clipboard_append(self._current_code)
            self._log("Code copied to clipboard", "ok")

    def _run_agent(self):
        if self._agent_running:
            return
        prompt = self.prompt_input.get("1.0", "end").strip()
        if not prompt:
            self._log("Enter a prompt first", "warn")
            return

        model = self.model_var.get()
        if not model or model == "Loading...":
            self._log("Select a model first", "warn")
            return

        self._agent_running = True
        self.run_btn.configure(state="disabled", text="⟳  Running...")

        # Clear plan box
        self.plan_box.configure(state="normal")
        self.plan_box.delete("1.0", "end")
        self.plan_box.configure(state="disabled")

        self._log("", "")
        self._log(f"━━━━ AGENT START ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "header")
        self._log(f"Prompt: {prompt[:80]}", "dim")
        self._log(f"Model:  {model}", "dim")

        def do():
            callbacks = {
                "on_status":     lambda m: self.after(0, self._set_status, m),
                "on_scene":      lambda s: self.after(0, self._set_scene, s),
                "on_code":       lambda c: self.after(0, self._set_code, c),
                "on_plan_token": lambda t: self.after(0, self._log_token, t, self.plan_box),
                "on_success":    lambda m: self.after(0, self._on_success, m),
                "on_error":      lambda m: self.after(0, self._on_error, m),
                "on_retry":      lambda n, e: self.after(0, self._on_retry, n, e),
            }
            try:
                blender_agent.MAX_RETRIES = self.retry_var.get()
                blender_agent.run_agent(prompt, model, callbacks)
            except Exception as e:
                self.after(0, self._on_error, str(e))

        threading.Thread(target=do, daemon=True).start()

    def _on_success(self, msg):
        self._agent_running = False
        self.run_btn.configure(state="normal", text="▶  RUN AGENT")
        self._log(f"━━━━ SUCCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "header")
        self._log(msg, "ok")
        self.status_bar.configure(text=f"✓  {msg}")
        self.retry_label.configure(text="")

    def _on_error(self, msg):
        self._agent_running = False
        self.run_btn.configure(state="normal", text="▶  RUN AGENT")
        self._log(f"━━━━ FAILED ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "header")
        self._log(msg, "err")
        self.status_bar.configure(text="✗  Agent failed — see log")

    def _on_retry(self, attempt, error_msg):
        self._log(f"↺ Retry {attempt} — fixing error automatically", "warn")
        self.retry_label.configure(text=f"Retry {attempt}/{self.retry_var.get()}")
        short_err = error_msg[:120].strip()
        self._log(f"  Error was: {short_err}", "dim")


# ── Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        import customtkinter
    except ImportError:
        print("Installing customtkinter...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter

    app = ChanduApp()
    app.mainloop()
