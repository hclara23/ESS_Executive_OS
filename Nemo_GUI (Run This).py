import json
import os
import dotenv
from tkinter import StringVar
from customtkinter import *
from PIL import Image
from Features.Onboarding import is_onboarded, save_user_profile, get_profile
from Features.BiddingHub import get_bidding_dashboard_data


class BiddingDashboard(CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Bidding Hub - Elio Agent")
        self.geometry("800x600")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_lbl = CTkLabel(self, text="Intelligent Bidding Hub", font=CTkFont(size=24, weight="bold"))
        self.title_lbl.grid(row=0, column=0, pady=20)

        self.tabview = CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.tab_available = self.tabview.add("Available Bids")
        self.tab_proposals = self.tabview.add("Active Proposals")

        self.text_available = CTkTextbox(self.tab_available)
        self.text_available.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_proposals = CTkTextbox(self.tab_proposals)
        self.text_proposals.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh_btn = CTkButton(self, text="Refresh Dashboard", command=self.load_data)
        self.refresh_btn.grid(row=2, column=0, pady=20)

        self.load_data()

    def load_data(self):
        data = get_bidding_dashboard_data()
        
        self.text_available.delete("1.0", "end")
        for b in data['available']:
            self.text_available.insert("end", f"[{b['id']}] {b['client']} - {b['project']} ({b['value']})\nDeadline: {b['deadline']}\nSummary: {b['rfp_summary']}\n---\n")

        self.text_proposals.delete("1.0", "end")
        if not data['proposals']:
            self.text_proposals.insert("end", "No active proposals drafted yet.")
        else:
            for bid_id, prop in data['proposals'].items():
                self.text_proposals.insert("end", f"[{bid_id}] Status: {prop['status']}\nDraft:\n{prop['draft']}\n---\n")


class OnboardingWizard(CTkToplevel):
    def __init__(self, user_key, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_key = user_key
        self.callback = callback
        self.title(f"Onboarding Elio for {user_key.capitalize()}")
        self.geometry("500x600")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        
        self.label = CTkLabel(self, text=f"Welcome to Elio, {user_key.capitalize()}!", font=CTkFont(size=20, weight="bold"))
        self.label.pack(pady=20)

        self.desc = CTkLabel(self, text="Please set up your profile to continue.", font=CTkFont(size=14))
        self.desc.pack(pady=10)

        # Name
        self.name_label = CTkLabel(self, text="Full Name:")
        self.name_label.pack(pady=(10, 0))
        self.name_entry = CTkEntry(self, width=300)
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, user_key.capitalize())

        # Email
        self.email_label = CTkLabel(self, text="Professional Email:")
        self.email_label.pack(pady=(10, 0))
        self.email_entry = CTkEntry(self, width=300)
        self.email_entry.pack(pady=5)

        # Role
        self.role_label = CTkLabel(self, text="Role in Company:")
        self.role_label.pack(pady=(10, 0))
        self.role_entry = CTkOptionMenu(self, values=["Owner/CEO", "Project Manager", "Lead Engineer", "Admin"], width=300)
        self.role_entry.pack(pady=5)
        if user_key == "sandra": self.role_entry.set("Owner/CEO")
        else: self.role_entry.set("Lead Engineer")

        # Tone Preference
        self.tone_label = CTkLabel(self, text="Assistant Tone Preference:")
        self.tone_label.pack(pady=(10, 0))
        self.tone_entry = CTkOptionMenu(self, values=["Professional", "Concise", "Friendly", "Direct"], width=300)
        self.tone_entry.pack(pady=5)

        # Second Brain Questions
        self.brain_label = CTkLabel(self, text="Second Brain Survey", font=CTkFont(size=16, weight="bold"))
        self.brain_label.pack(pady=(20, 10))

        self.goal_label = CTkLabel(self, text="What is your top professional goal for this year?")
        self.goal_label.pack()
        self.goal_entry = CTkEntry(self, width=400)
        self.goal_entry.pack(pady=5)

        self.stake_label = CTkLabel(self, text="Who are your top 3 most important stakeholders?")
        self.stake_label.pack()
        self.stake_entry = CTkEntry(self, width=400)
        self.stake_entry.pack(pady=5)

        self.pain_label = CTkLabel(self, text="What is your biggest daily recurring pain point?")
        self.pain_label.pack()
        self.pain_entry = CTkEntry(self, width=400)
        self.pain_entry.pack(pady=5)

        self.finish_btn = CTkButton(self, text="Complete Onboarding & Sync Brain", command=self.finish)
        self.finish_btn.pack(pady=40)

    def finish(self):
        profile = {
            "onboarded": True,
            "full_name": self.name_entry.get(),
            "email": self.email_entry.get(),
            "role": self.role_entry.get(),
            "tone": self.tone_entry.get(),
            "setup_date": str(os.times()[4])
        }
        save_user_profile(self.user_key, profile)
        
        # Save Second Brain Facts
        from Features.MemoryStore import save_second_brain_fact
        save_second_brain_fact(self.user_key, "top_goal", self.goal_entry.get())
        save_second_brain_fact(self.user_key, "stakeholders", self.stake_entry.get())
        save_second_brain_fact(self.user_key, "pain_point", self.pain_entry.get())
        
        self.destroy()
        self.callback()


class SettingsWindow(CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Elio Settings & Data Banks")
        self.geometry("800x800")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_creds = self.tabview.add("Credentials")
        self.tab_persona = self.tabview.add("Personality")
        self.tab_memory = self.tabview.add("Memory Bank")
        self.tab_lessons = self.tabview.add("Lessons Bank")
        self.tab_audit = self.tabview.add("Audit Logs")

        # --- Credentials Tab ---
        self.scroll_creds = CTkScrollableFrame(self.tab_creds)
        self.scroll_creds.pack(fill="both", expand=True)
        self.scroll_creds.grid_columnconfigure(1, weight=1)
        
        if not hasattr(self, "fields"): self.fields = {}
        self._add_row("OpenAI API Key", "Data/Api.txt", self.scroll_creds)
        self._add_row("Postgres URI", ".env", self.scroll_creds)
        self._add_row("Gmail Client ID", "gmail_id", self.scroll_creds)
        self._add_row("Gmail Client Secret", "gmail_secret", self.scroll_creds)
        self._add_row("Calendar Client ID", "calendar_id", self.scroll_creds)
        self._add_row("Calendar Client Secret", "calendar_secret", self.scroll_creds)
        self._add_row("QuickBooks Client ID", "quickbooks_id", self.scroll_creds)
        self._add_row("QuickBooks Client Secret", "quickbooks_secret", self.scroll_creds)
        self._add_row("Procore Client ID", "procore_id", self.scroll_creds)
        self._add_row("Procore Client Secret", "procore_secret", self.scroll_creds)
        self._add_row("Jira API Token", "jira_token", self.scroll_creds)

        # --- Personality Tab ---
        self.scroll_persona = CTkScrollableFrame(self.tab_persona)
        self.scroll_persona.pack(fill="both", expand=True)
        self.scroll_persona.grid_columnconfigure(1, weight=1)
        
        self._add_persona_row("Assistant Name", "name", self.scroll_persona)
        self._add_persona_row("Tone", "tone", self.scroll_persona)
        self._add_persona_row("Persona Description", "persona", self.scroll_persona, is_large=True)
        self._add_persona_row("System Instructions", "instructions", self.scroll_persona, is_large=True)

        # --- Memory Bank Tab ---
        self.btn_refresh_mem = CTkButton(self.tab_memory, text="Refresh Memory", command=self.load_memory)
        self.btn_refresh_mem.pack(pady=10)
        self.text_memory = CTkTextbox(self.tab_memory)
        self.text_memory.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Lessons Bank Tab ---
        self.btn_refresh_lessons = CTkButton(self.tab_lessons, text="Refresh Lessons", command=self.load_lessons)
        self.btn_refresh_lessons.pack(pady=10)
        self.text_lessons = CTkTextbox(self.tab_lessons)
        self.text_lessons.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Audit Logs Tab ---
        self.btn_refresh_audit = CTkButton(self.tab_audit, text="Refresh Audit Logs", command=self.load_audit)
        self.btn_refresh_audit.pack(pady=10)
        self.text_audit = CTkTextbox(self.tab_audit)
        self.text_audit.pack(fill="both", expand=True, padx=20, pady=10)

        self.save_btn = CTkButton(self, text="Save All Settings", command=self.save_all)
        self.save_btn.grid(row=1, column=0, pady=20)

        self.load_all()

    def _add_row(self, label, key, parent):
        row = len(parent.winfo_children()) // 2
        lbl = CTkLabel(parent, text=label)
        lbl.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry = CTkEntry(parent, width=400)
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        self.fields[key] = {"entry": entry}

    def _add_persona_row(self, label, key, parent, is_large=False):
        row = len(parent.winfo_children()) // 2
        lbl = CTkLabel(parent, text=label)
        lbl.grid(row=row, column=0, padx=10, pady=10, sticky="nw")
        
        if is_large:
            entry = CTkTextbox(parent, height=100, width=400)
        else:
            entry = CTkEntry(parent, width=400)
            
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        if not hasattr(self, "persona_fields"): self.persona_fields = {}
        self.persona_fields[key] = {"entry": entry, "is_large": is_large}

    def load_all(self):
        dotenv.load_dotenv()

        mapping = {
            "gmail_id": os.getenv("ELIO_GMAIL_CLIENT_ID", ""),
            "gmail_secret": os.getenv("ELIO_GMAIL_CLIENT_SECRET", ""),
            "calendar_id": os.getenv("ELIO_CAL_CLIENT_ID", ""),
            "calendar_secret": os.getenv("ELIO_CAL_CLIENT_SECRET", ""),
            "quickbooks_id": os.getenv("ELIO_QBO_CLIENT_ID", ""),
            "quickbooks_secret": os.getenv("ELIO_QBO_CLIENT_SECRET", ""),
            "procore_id": os.getenv("ELIO_PROCORE_CLIENT_ID", ""),
            "procore_secret": os.getenv("ELIO_PROCORE_CLIENT_SECRET", ""),
            "jira_token": os.getenv("ELIO_JIRA_TOKEN", ""),
        }
        for k, v in mapping.items():
            if k in self.fields: self.fields[k]["entry"].insert(0, v)

        # OpenAI Key
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if "Data/Api.txt" in self.fields:
            self.fields["Data/Api.txt"]["entry"].insert(0, openai_key)

        # .env
        pg_uri = os.getenv("ELIO_PG_URI", "")
        if ".env" in self.fields:
            self.fields[".env"]["entry"].insert(0, pg_uri)

        # Load Persona
        if os.path.exists("Data/personality.json"):
            with open("Data/personality.json", "r") as f:
                persona = json.load(f)
                for k, v in persona.items():
                    if k in self.persona_fields:
                        fld = self.persona_fields[k]
                        if fld["is_large"]:
                            fld["entry"].insert("1.0", v)
                        else:
                            fld["entry"].insert(0, v)
        
        self.load_memory()
        self.load_lessons()
        self.load_audit()

    def load_memory(self):
        try:
            from Features.MemoryStore import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute("SELECT user_name, text_body, created_at FROM elio_memory_private ORDER BY created_at DESC LIMIT 50")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            self.text_memory.delete("1.0", "end")
            for r in rows:
                self.text_memory.insert("end", f"[{r[2]}] {r[0]}: {r[1]}\n---\n")
        except:
            self.text_memory.insert("end", "Could not load memory. Is Postgres running?")

    def load_lessons(self):
        try:
            from Features.MemoryStore import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute("SELECT owner, text_body, created_at FROM elio_lessons_learned ORDER BY created_at DESC LIMIT 50")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            self.text_lessons.delete("1.0", "end")
            for r in rows:
                self.text_lessons.insert("end", f"[{r[2]}] {r[0]}: {r[1]}\n---\n")
        except:
            self.text_lessons.insert("end", "Could not load lessons. Is Postgres running?")

    def load_audit(self):
        try:
            from Features.MemoryStore import _pg_conn
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute("SELECT user_name, action_type, details, created_at FROM elio_audit_logs ORDER BY created_at DESC LIMIT 100")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            self.text_audit.delete("1.0", "end")
            for r in rows:
                self.text_audit.insert("end", f"[{r[3]}] {r[0]} -> {r[1]}: {r[2]}\n---\n")
        except:
            self.text_audit.insert("end", "Could not load audit logs.")

    def save_all(self):
        env_file = ".env"
        if not os.path.exists(env_file):
            open(env_file, 'a').close()
            
        dotenv.set_key(env_file, "ELIO_GMAIL_CLIENT_ID", self.fields["gmail_id"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_GMAIL_CLIENT_SECRET", self.fields["gmail_secret"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_CAL_CLIENT_ID", self.fields["calendar_id"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_CAL_CLIENT_SECRET", self.fields["calendar_secret"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_QBO_CLIENT_ID", self.fields["quickbooks_id"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_QBO_CLIENT_SECRET", self.fields["quickbooks_secret"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_PROCORE_CLIENT_ID", self.fields["procore_id"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_PROCORE_CLIENT_SECRET", self.fields["procore_secret"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_JIRA_TOKEN", self.fields["jira_token"]["entry"].get())

        # Persona
        persona = {}
        for k, v in self.persona_fields.items():
            if v["is_large"]:
                persona[k] = v["entry"].get("1.0", "end-1c")
            else:
                persona[k] = v["entry"].get()
        with open("Data/personality.json", "w") as f: json.dump(persona, f, indent=2)

        # Files
        dotenv.set_key(env_file, "OPENAI_API_KEY", self.fields["Data/Api.txt"]["entry"].get())
        dotenv.set_key(env_file, "ELIO_PG_URI", self.fields[".env"]["entry"].get())
        
        print("Settings saved.")
        self.destroy()


class Widget:
    def __init__(self):
        self.root = CTk()
        set_appearance_mode("dark")
        set_default_color_theme("blue")

        self.root.title("Elio")
        self.root.geometry("520x720")
        self.root.resizable(False, False)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.card = CTkFrame(self.root, corner_radius=28)
        self.card.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")
        self.card.grid_rowconfigure(8, weight=1)
        self.card.grid_columnconfigure(0, weight=1)

        self.title = CTkLabel(
            self.card,
            text="Elio",
            font=CTkFont(family="Poppins", size=34, weight="bold"),
        )
        self.title.grid(row=0, column=0, pady=(24, 4))

        self.subtitle = CTkLabel(
            self.card,
            text="Your daily helper for Alex and Sandra",
            font=CTkFont(family="Poppins", size=14),
            text_color=("gray30", "gray70"),
        )
        self.subtitle.grid(row=1, column=0, pady=(0, 18))

        logo_img = CTkImage(Image.open("Data/Elio_Logo.png"), size=(220, 220))
        self.logo = CTkLabel(self.card, text="", image=logo_img)
        self.logo.grid(row=2, column=0, pady=(0, 16))

        self.status_var = StringVar(value="Ready.")
        self.status = CTkLabel(
            self.card,
            textvariable=self.status_var,
            font=CTkFont(family="Poppins", size=13),
            text_color=("gray35", "gray70"),
        )
        self.status.grid(row=3, column=0, pady=(0, 18))

        self.start_btn = CTkButton(
            self.card,
            text="Start",
            height=46,
            corner_radius=22,
            font=CTkFont(family="Poppins", size=16, weight="bold"),
            command=self.clicked,
        )
        self.start_btn.grid(row=4, column=0, padx=28, pady=(0, 18), sticky="ew")

        self.settings_btn = CTkButton(
            self.card,
            text="Settings / Admin",
            height=34,
            corner_radius=18,
            fg_color=("gray20", "gray30"),
            font=CTkFont(family="Poppins", size=13),
            command=self.open_settings,
        )
        self.settings_btn.grid(row=5, column=0, padx=28, pady=(0, 12), sticky="ew")

        self.bidding_btn = CTkButton(
            self.card,
            text="Bidding Hub",
            height=34,
            corner_radius=18,
            fg_color=("darkgreen", "darkgreen"),
            font=CTkFont(family="Poppins", size=13),
            command=self.open_bidding,
        )
        self.bidding_btn.grid(row=6, column=0, padx=28, pady=(0, 16), sticky="ew")

        self.upload_btn = CTkButton(
            self.card,
            text="Upload Manual / PDF",
            height=34,
            corner_radius=18,
            fg_color=("darkblue", "darkblue"),
            font=CTkFont(family="Poppins", size=13),
            command=self.upload_pdf,
        )
        self.upload_btn.grid(row=7, column=0, padx=28, pady=(0, 16), sticky="ew")

        self.mode_btn = CTkButton(
            self.card,
            text="Light / Dark",
            height=30,
            corner_radius=15,
            fg_color=("gray85", "gray20"),
            text_color=("gray10", "gray90"),
            font=CTkFont(family="Poppins", size=11),
            command=self.toggle_mode,
        )
        self.mode_btn.grid(row=8, column=0, pady=(0, 12))

        self.footer = CTkLabel(
            self.card,
            text="Say “wake up” after you start.",
            font=CTkFont(family="Poppins", size=12),
            text_color=("gray40", "gray70"),
        )
        self.footer.grid(row=9, column=0, pady=(0, 16))

        self.root.mainloop()

    def toggle_mode(self):
        current = get_appearance_mode().lower()
        if current == "dark":
            set_appearance_mode("light")
        else:
            set_appearance_mode("dark")

    def open_settings(self):
        SettingsWindow(self.root)

    def open_bidding(self):
        BiddingDashboard(self.root)

    def upload_pdf(self):
        from tkinter import filedialog
        from Features.KnowledgeBase import ingest_pdf
        from Features.Storage import upload_to_elio_storage
        import os

        file_path = filedialog.askopenfilename(
            title="Select Manual or PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            file_name = os.path.basename(file_path)
            self.status_var.set(f"Uploading {file_name}...")
            
            # 1. Cloud Storage
            success_gcs, msg_gcs = upload_to_elio_storage(file_path, file_name)
            
            # 2. Local Knowledge Ingestion
            success_kb, msg_kb = ingest_pdf(file_path, file_name)
            
            if success_kb:
                self.status_var.set(f"Ingested {file_name} successfully.")
                from Features.Face.Mouth import speak
                speak(f"I have successfully learned from {file_name}. You can now ask me questions about it.")
            else:
                self.status_var.set(f"Upload Error: {msg_kb}")

    def clicked(self):
        # 1. Identify User (Ask if not known)
        from Features.Mode import resolve_user
        user = resolve_user()
        
        if user == "unknown":
            self.status_var.set("Please identify yourself...")
            # Simple dialog to pick user
            dialog = CTkInputDialog(text="Are you Alex or Sandra?", title="Identify User")
            user_input = dialog.get_input()
            if user_input and user_input.lower() in ["alex", "sandra"]:
                user = user_input.lower()
            else:
                self.status_var.set("Start Cancelled.")
                return

        # 2. Check Onboarding
        if not is_onboarded(user):
            self.status_var.set(f"Onboarding {user.capitalize()}...")
            OnboardingWizard(user, self.start_main)
        else:
            self.start_main()

    def start_main(self):
        self.status_var.set("Starting Elio...")
        from Main_Nemo import ThisMain
        import threading
        # Run in thread to not block GUI
        threading.Thread(target=ThisMain, daemon=True).start()


if __name__ == "__main__":
    widget = Widget()
