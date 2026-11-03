"""QuizLab desktop GUI. Uses the existing quizlab.db SQLite schema; matplotlib is required for performance charts."""
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime, timedelta
import calendar
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = Path(__file__).with_name("quizlab.db")
if not DB_FILE.exists():
    DB_FILE = Path.home() / "AppData" / "Local" / "Temp" / "quizlab.db"

PURPLE = "#5146E5"
PURPLE_DARK = "#4035CF"
INK = "#22243A"
MUTED = "#777B91"
BG = "#F6F7FB"
WHITE = "#FFFFFF"
LINE = "#E7E8F0"
GREEN = "#18966A"
RED = "#D94B59"
FONT = "Segoe UI"


class QuizLab:
    def __init__(self, root):
        self.root = root
        self.root.title("QuizLab — Online Quiz Platform")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.root.configure(bg=BG)
        self.user = None
        self.page = None
        self.question_widgets = []
        self.quiz_questions = []
        self.answer_vars = {}
        self.current_attempt = None
        self.quiz_deadline = None
        self.timer_job = None
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", background=WHITE, fieldbackground=WHITE,
                             foreground=INK, rowheight=34, font=(FONT, 10), borderwidth=0)
        self.style.configure("Treeview.Heading", background="#F0F1F8", foreground=INK,
                             font=(FONT, 9, "bold"), relief="flat")
        self.style.map("Treeview", background=[("selected", "#EAE8FF")],
                       foreground=[("selected", INK)])
        self.db = sqlite3.connect(str(DB_FILE))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.show_auth("login")

    def q(self, sql, args=()):
        return self.db.execute(sql, args)

    def rows(self, sql, args=()):
        return self.q(sql, args).fetchall()

    def one(self, sql, args=()):
        return self.q(sql, args).fetchone()

    def commit(self):
        self.db.commit()

    def clear(self):
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        for widget in self.root.winfo_children():
            widget.destroy()

    def button(self, parent, text, command, primary=True, width=None):
        color = PURPLE if primary else WHITE
        fg = WHITE if primary else PURPLE
        b = tk.Button(parent, text=text, command=command, bg=color, fg=fg,
                      activebackground=PURPLE_DARK if primary else "#F2F1FF",
                      activeforeground=fg, relief="flat", bd=0, cursor="hand2",
                      font=(FONT, 10, "bold"), padx=16, pady=9,
                      highlightthickness=1 if not primary else 0,
                      highlightbackground=LINE, width=width)
        return b

    def label(self, parent, text, size=10, color=INK, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")),
                        fg=color, font=(FONT, size, "bold" if bold else "normal"),
                        anchor=kwargs.pop("anchor", "w"), **kwargs)

    def entry(self, parent, variable=None, show=None, width=36):
        e = tk.Entry(parent, textvariable=variable, show=show, width=width,
                     font=(FONT, 10), relief="solid", bd=1,
                     highlightthickness=1, highlightbackground=LINE,
                     highlightcolor=PURPLE, bg=WHITE, fg=INK, insertbackground=INK)
        e.configure(highlightthickness=1)
        return e

    def field(self, parent, title, variable=None, show=None, width=42):
        wrap = tk.Frame(parent, bg=parent.cget("bg"))
        self.label(wrap, title, 9, MUTED, True).pack(anchor="w", pady=(0, 6))
        widget = self.entry(wrap, variable, show, width)
        widget.pack(fill="x", ipady=8)
        return wrap, widget

    def card(self, parent, padx=22, pady=20):
        box = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        box.pack_propagate(True)
        return box

    def show_auth(self, mode="login"):
        self.clear()
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)
        panel = tk.Frame(outer, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        panel.place(relx=.5, rely=.5, anchor="center", width=440,
                    height=610 if mode == "register" else 560)
        self.label(panel, "QuizLab", 28, PURPLE, True).pack(pady=(36, 4))
        self.label(panel, "Online Quiz Platform", 10, MUTED).pack(pady=(0, 22))
        self.label(panel, "Create your account" if mode == "register" else "Welcome back", 19, INK, True).pack()
        self.label(panel, "Sign up to get started" if mode == "register" else "Sign in to continue to your dashboard", 9, MUTED).pack(pady=(7, 20))
        form = tk.Frame(panel, bg=WHITE)
        form.pack(fill="x", padx=48)
        self.auth_name = tk.StringVar()
        self.auth_email = tk.StringVar()
        self.auth_password = tk.StringVar()
        if mode == "register":
            w, _ = self.field(form, "Full name", self.auth_name)
            w.pack(fill="x", pady=7)
        w, email = self.field(form, "Email address", self.auth_email)
        w.pack(fill="x", pady=7)
        w, password = self.field(form, "Password", self.auth_password, "•")
        w.pack(fill="x", pady=7)
        action = self.button(panel, "Create account" if mode == "register" else "Sign in",
                             self.register if mode == "register" else self.login)
        action.pack(fill="x", padx=48, pady=(20, 12))
        link = tk.Button(panel, text=("Already have an account? Sign in" if mode == "register" else "New to QuizLab? Create an account"),
                         command=lambda: self.show_auth("login" if mode == "register" else "register"),
                         bg=WHITE, fg=PURPLE, font=(FONT, 9, "bold"), bd=0, cursor="hand2")
        link.pack()
        self.label(panel, "Demo: admin@gmail.com / admin@123\nstudent@gmail.com / student@123", 8, MUTED, justify="center").pack(side="bottom", pady=22)
        email.focus_set()
        self.root.bind("<Return>", lambda _e: self.register() if mode == "register" else self.login())

    def login(self):
        email, password = self.auth_email.get().strip().lower(), self.auth_password.get()
        user = self.one("SELECT * FROM users WHERE lower(email)=? AND password=? AND is_active=1", (email, password))
        if not user:
            messagebox.showerror("Sign in failed", "The email or password is incorrect, or this account is inactive.")
            return
        self.user = dict(user)
        self.root.unbind("<Return>")
        self.show_home()

    def register(self):
        name, email, password = self.auth_name.get().strip(), self.auth_email.get().strip().lower(), self.auth_password.get()
        if not name or not email or not password:
            messagebox.showwarning("Missing information", "Enter your name, email address, and password.")
            return
        try:
            self.q("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'Student')", (name, email, password))
            self.commit()
            self.user = dict(self.one("SELECT * FROM users WHERE email=?", (email,)))
            self.root.unbind("<Return>")
            self.show_home()
        except sqlite3.IntegrityError:
            messagebox.showerror("Account not created", "An account with this email already exists.")

    def show_home(self):
        if self.user["role"] == "Admin":
            self.show_admin_dashboard()
        else:
            self.show_student_dashboard()

    def shell(self, title, active, subtitle=None):
        self.clear()
        self.page = tk.Frame(self.root, bg=BG)
        self.page.pack(fill="both", expand=True)
        sidebar = tk.Frame(self.page, bg=WHITE, width=220, highlightthickness=1, highlightbackground=LINE)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.label(sidebar, "QuizLab", 23, PURPLE, True).pack(anchor="w", padx=24, pady=(26, 1))
        self.label(sidebar, "ONLINE QUIZ PLATFORM", 8, MUTED, True).pack(anchor="w", padx=26, pady=(0, 25))
        navs = ([('Dashboard', 'admin_dashboard'), ('Question Bank', 'question_bank'), ('Manage Quizzes', 'manage_quizzes'), ('Manage Subjects', 'manage_subjects')]
                if self.user["role"] == "Admin" else [('Dashboard', 'student_dashboard'), ('Available Quizzes', 'available'), ('My Performance', 'performance')])
        for text, key in navs:
            selected = key == active
            b = tk.Button(sidebar, text=("▣   " if selected else "   ")+text,
                          command=lambda k=key: self.navigate(k), anchor="w", padx=18,
                          bg="#F0EFFF" if selected else WHITE, fg=PURPLE if selected else "#62677C",
                          activebackground="#F0EFFF", activeforeground=PURPLE,
                          font=(FONT, 10, "bold" if selected else "normal"), bd=0, cursor="hand2", pady=12)
            b.pack(fill="x", padx=12, pady=3)
        tk.Frame(sidebar, bg=WHITE).pack(fill="both", expand=True)
        profile = tk.Frame(sidebar, bg=WHITE)
        profile.pack(fill="x", padx=18, pady=18)
        self.label(profile, self.user["name"], 9, INK, True).pack(anchor="w")
        self.label(profile, self.user["role"], 8, MUTED).pack(anchor="w", pady=(2, 9))
        tk.Button(profile, text="↪  Sign out", command=self.logout, bg=WHITE, fg=MUTED,
                  font=(FONT, 9), bd=0, anchor="w", cursor="hand2").pack(anchor="w")
        main = tk.Frame(self.page, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        area = tk.Frame(main, bg=BG)
        area.pack(fill="both", expand=True, padx=28, pady=24)
        self.content = area
        return area

    def navigate(self, key):
        actions = {"student_dashboard": self.show_student_dashboard, "available": self.show_available,
                   "performance": self.show_performance, "admin_dashboard": self.show_admin_dashboard,
                   "question_bank": self.show_question_bank, "manage_quizzes": self.show_manage_quizzes,
                   "manage_subjects": self.show_manage_subjects}
        actions[key]()

    def logout(self):
        self.user = None
        self.root.unbind("<Return>")
        self.show_auth("login")

    def heading(self, parent, title, detail=None, action=None, action_text=""):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 16))
        left = tk.Frame(row, bg=BG)
        left.pack(side="left", fill="x", expand=True)
        self.label(left, title, 20, INK, True).pack(anchor="w")
        if detail:
            self.label(left, detail, 9, MUTED).pack(anchor="w", pady=(4, 0))
        if action:
            self.button(row, action_text, action).pack(side="right")

    def stat(self, parent, title, value, note=""):
        box = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        box.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.label(box, title, 9, MUTED, True).pack(anchor="w", padx=18, pady=(15, 5))
        self.label(box, str(value), 24, INK, True).pack(anchor="w", padx=18)
        if note:
            self.label(box, note, 8, MUTED).pack(anchor="w", padx=18, pady=(3, 14))
        else:
            tk.Frame(box, bg=WHITE, height=14).pack()

    def show_student_dashboard(self):
        area = self.shell("Dashboard", "student_dashboard", "Welcome back, " + self.user["name"])
        self.heading(area, "Student Dashboard", "Pick up where you left off")
        attempts = self.rows("SELECT * FROM quiz_attempts WHERE user_id=?", (self.user["user_id"],))
        average = round(sum(float(a["percentage"]) for a in attempts)/len(attempts), 1) if attempts else 0
        stats = tk.Frame(area, bg=BG); stats.pack(fill="x", pady=(0, 22))
        self.stat(stats, "AVAILABLE QUIZZES", self.one("SELECT COUNT(*) n FROM quizzes WHERE status='Published'")["n"], "Ready to take")
        self.stat(stats, "QUIZZES COMPLETED", sum(a["status"] != "In Progress" for a in attempts), "Your submitted attempts")
        self.stat(stats, "AVERAGE SCORE", f"{average}%", "Across completed quizzes")
        self.heading(area, "Available Quizzes", "Continue learning with a quiz")
        self.quiz_cards(area, student=True)

    def show_available(self):
        area = self.shell("Available Quizzes", "available", "Browse published quizzes")
        self.heading(area, "Available Quizzes", "Choose a quiz to view its details")
        self.quiz_cards(area, student=True)

    def quiz_cards(self, parent, student=False):
        quizzes = self.rows("SELECT q.*,s.subject_name FROM quizzes q JOIN subjects s ON s.subject_id=q.subject_id WHERE q.status='Published' ORDER BY q.created_at DESC")
        if not quizzes:
            self.empty(parent, "No published quizzes yet", "Your admin will publish quizzes here when they are ready.")
            return
        for q in quizzes:
            box = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
            box.pack(fill="x", pady=6)
            body = tk.Frame(box, bg=WHITE); body.pack(fill="x", padx=20, pady=16)
            left = tk.Frame(body, bg=WHITE); left.pack(side="left", fill="x", expand=True)
            self.label(left, q["title"], 13, INK, True).pack(anchor="w")
            self.label(left, f"{q['subject_name']}   •   {q['duration_minutes']} min   •   {q['total_marks']:g} marks", 9, MUTED).pack(anchor="w", pady=5)
            self.label(left, q["description"] or "Test your knowledge and check your results instantly.", 9, MUTED).pack(anchor="w")
            self.button(body, "View details", lambda qid=q["quiz_id"]: self.show_quiz_details(qid)).pack(side="right", padx=(12, 0))

    def empty(self, parent, title, detail):
        box = tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        box.pack(fill="x", pady=8)
        self.label(box, title, 13, INK, True, anchor="center").pack(fill="x", pady=(25, 7))
        self.label(box, detail, 9, MUTED, anchor="center").pack(fill="x", pady=(0, 25))

    def show_quiz_details(self, quiz_id):
        q = self.one("SELECT q.*,s.subject_name FROM quizzes q JOIN subjects s ON s.subject_id=q.subject_id WHERE q.quiz_id=?", (quiz_id,))
        if not q: return self.show_available()
        area = self.shell("Quiz Details", "available", "Review the details before you begin")
        tk.Button(area, text="← Back to quizzes", command=self.show_available, bg=BG, fg=PURPLE,
                  bd=0, font=(FONT, 9, "bold"), cursor="hand2").pack(anchor="w", pady=(0, 12))
        box = tk.Frame(area, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        box.pack(fill="both", expand=True)
        self.label(box, q["title"], 21, INK, True).pack(anchor="w", padx=26, pady=(24, 4))
        self.label(box, q["description"] or "Test your knowledge and strengthen your skills.", 9, MUTED).pack(anchor="w", padx=26, pady=(0, 20))
        info = tk.Frame(box, bg=WHITE); info.pack(fill="x", padx=26)
        for name, val in (("Subject", q["subject_name"]), ("Duration", f"{q['duration_minutes']} minutes"),
                          ("Questions", str(self.one("SELECT COUNT(*) n FROM quiz_questions WHERE quiz_id=?", (quiz_id,))["n"])),
                          ("Total marks", f"{q['total_marks']:g}"), ("Passing marks", f"{q['passing_marks']:g}")):
            row = tk.Frame(info, bg=WHITE); row.pack(fill="x", pady=8)
            self.label(row, name, 9, MUTED).pack(side="left")
            self.label(row, val, 9, INK, True).pack(side="right")
            tk.Frame(info, bg=LINE, height=1).pack(fill="x")
        self.label(box, "Before you begin", 12, INK, True).pack(anchor="w", padx=26, pady=(22, 8))
        instructions = q["instructions"] or "Read each question carefully. You can review your answers before submitting. Your quiz will be submitted automatically when the timer ends."
        self.label(box, instructions, 9, MUTED, wraplength=760, justify="left").pack(anchor="w", padx=26)
        self.button(box, "Begin quiz", lambda: self.begin_quiz(quiz_id)).pack(anchor="e", padx=26, pady=24)

    def begin_quiz(self, quiz_id):
        q = self.one("SELECT * FROM quizzes WHERE quiz_id=? AND status='Published'", (quiz_id,))
        links = self.rows("SELECT qq.quiz_question_id,qq.marks,qq.question_order,qu.question_text,qu.question_type,qu.difficulty FROM quiz_questions qq JOIN questions qu ON qu.question_id=qq.question_id WHERE qq.quiz_id=? ORDER BY qq.question_order", (quiz_id,))
        if not q or not links:
            messagebox.showwarning("Quiz unavailable", "This quiz has no questions yet or is no longer published.")
            return
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.q("INSERT INTO quiz_attempts(user_id,quiz_id,started_at,total_marks,status) VALUES(?,?,?,?,'In Progress')",
                     (self.user["user_id"], quiz_id, start, float(q["total_marks"])))
        self.commit()
        self.current_attempt = cur.lastrowid
        self.quiz_questions = links
        self.answer_vars = {}
        area = self.shell("Take Quiz", "available", q["title"])
        top = tk.Frame(area, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        top.pack(fill="x", pady=(0, 14))
        self.label(top, q["title"], 13, INK, True).pack(side="left", padx=18, pady=14)
        self.timer_label = self.label(top, "", 11, RED, True)
        self.timer_label.pack(side="right", padx=18)
        canvas = tk.Canvas(area, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=area.winfo_width()-20)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure("all", width=e.width))
        for i, item in enumerate(links, 1):
            card = tk.Frame(inner, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
            card.pack(fill="x", pady=6)
            self.label(card, f"Question {i}  ·  {item['marks']:g} marks", 9, PURPLE, True).pack(anchor="w", padx=18, pady=(14, 5))
            self.label(card, item["question_text"], 11, INK, True, wraplength=800, justify="left").pack(anchor="w", padx=18, pady=(0, 8))
            opts = self.rows("SELECT * FROM options WHERE question_id=(SELECT question_id FROM quiz_questions WHERE quiz_question_id=?) ORDER BY option_order", (item["quiz_question_id"],))
            multi = item["question_type"] == "MSQ"
            vars_ = []
            for opt in opts:
                var = tk.BooleanVar(value=False) if multi else tk.IntVar(value=0)
                control = tk.Checkbutton(card, text=opt["option_text"], variable=var,
                                         onvalue=True if multi else opt["option_id"],
                                         offvalue=False if multi else 0,
                                         bg=WHITE, activebackground=WHITE, fg=INK,
                                         font=(FONT, 10), anchor="w", justify="left")
                control.pack(fill="x", padx=20, pady=2)
                vars_.append((opt["option_id"], var))
            self.answer_vars[item["quiz_question_id"]] = (multi, vars_)
            tk.Frame(card, bg=WHITE, height=9).pack()
        self.button(area, "Submit quiz", lambda: self.submit_quiz(False)).pack(anchor="e", pady=12)
        self.quiz_deadline = datetime.now() + timedelta(minutes=int(q["duration_minutes"]))
        self.update_timer()

    def update_timer(self):
        if not self.timer_label or not self.timer_label.winfo_exists(): return
        remaining = max(0, int((self.quiz_deadline - datetime.now()).total_seconds()))
        self.timer_label.config(text=f"Time remaining  {remaining//60:02d}:{remaining%60:02d}")
        if remaining <= 0:
            self.submit_quiz(True)
        else:
            self.timer_job = self.root.after(1000, self.update_timer)

    def submit_quiz(self, timed_out=False):
        if not timed_out and not messagebox.askyesno("Submit quiz", "Submit your answers and see your result?"):
            return
        score, total = 0.0, 0.0
        for item in self.quiz_questions:
            qid = item["quiz_question_id"]
            multi, vars_ = self.answer_vars[qid]
            selected = [oid for oid, var in vars_ if (var.get() is True if multi else var.get() == oid)]
            correct = [r["option_id"] for r in self.rows("SELECT option_id FROM options WHERE question_id=(SELECT question_id FROM quiz_questions WHERE quiz_question_id=?) AND is_correct=1", (qid,))]
            is_correct = bool(correct) and set(selected) == set(correct)
            marks = float(item["marks"])
            gained = marks if is_correct else 0.0
            score += gained; total += marks
            self.q("INSERT INTO attempt_answers(attempt_id,quiz_question_id,selected_option_ids,is_correct,marks_obtained) VALUES(?,?,?,?,?)",
                   (self.current_attempt, qid, json.dumps(selected), int(is_correct), gained))
        q = self.one("SELECT passing_marks FROM quizzes WHERE quiz_id=(SELECT quiz_id FROM quiz_attempts WHERE attempt_id=?)", (self.current_attempt,))
        pct = round(score / total * 100, 2) if total else 0.0
        status = "Timed Out" if timed_out else "Submitted"
        self.q("UPDATE quiz_attempts SET submitted_at=?,score=?,total_marks=?,percentage=?,status=?,result_status=? WHERE attempt_id=?",
               (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), score, total, pct, status,
                "Pass" if score >= float(q["passing_marks"]) else "Fail", self.current_attempt))
        self.commit()
        attempt = self.current_attempt
        self.current_attempt = None
        self.show_result(attempt)

    def show_result(self, attempt_id):
        a = self.one("SELECT a.*,q.title,q.passing_marks FROM quiz_attempts a JOIN quizzes q ON q.quiz_id=a.quiz_id WHERE a.attempt_id=?", (attempt_id,))
        area = self.shell("Quiz Results", "performance", "Your quiz has been submitted")
        box = tk.Frame(area, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        box.pack(fill="both", expand=True)
        self.label(box, "Quiz Results", 22, INK, True, anchor="center").pack(fill="x", pady=(28, 5))
        self.label(box, a["title"], 10, MUTED, anchor="center").pack(fill="x")
        self.label(box, f"{a['score']:g} / {a['total_marks']:g}", 32, PURPLE, True, anchor="center").pack(fill="x", pady=(23, 3))
        self.label(box, f"{a['percentage']:g}%", 13, INK, True, anchor="center").pack(fill="x")
        passed = a["result_status"] == "Pass"
        tk.Label(box, text="PASSED" if passed else "NEEDS IMPROVEMENT", bg="#E8F7F1" if passed else "#FFF0F1",
                 fg=GREEN if passed else RED, font=(FONT, 9, "bold"), padx=12, pady=6).pack(pady=17)
        stats = tk.Frame(box, bg=WHITE); stats.pack(pady=8)
        self.label(stats, f"Passing score  {a['passing_marks']:g}", 9, MUTED).pack(side="left", padx=18)
        self.label(stats, f"Status  {a['status']}", 9, MUTED).pack(side="left", padx=18)
        row = tk.Frame(box, bg=WHITE); row.pack(pady=24)
        self.button(row, "Back to dashboard", self.show_student_dashboard).pack(side="left", padx=5)
        self.button(row, "View performance", self.show_performance, primary=False).pack(side="left", padx=5)

    def show_performance(self):
        area = self.shell("My Performance", "performance", "Track your quiz history and results")
        attempts = self.rows(
            "SELECT a.*,q.title,s.subject_name FROM quiz_attempts a "
            "JOIN quizzes q ON q.quiz_id=a.quiz_id "
            "JOIN subjects s ON s.subject_id=q.subject_id "
            "WHERE a.user_id=? ORDER BY a.started_at DESC",
            (self.user["user_id"],),
        )
        completed = [a for a in attempts if a["status"] in ("Submitted", "Timed Out")]
        avg = round(sum(float(a["percentage"]) for a in completed) / len(completed), 1) if completed else 0
        self.heading(area, "Performance Overview", "Your quiz history at a glance")

        chart_canvas = tk.Canvas(area, bg=BG, highlightthickness=0)
        chart_scroll = ttk.Scrollbar(area, orient="vertical", command=chart_canvas.yview)
        body = tk.Frame(chart_canvas, bg=BG)
        body.bind("<Configure>", lambda _e: chart_canvas.configure(scrollregion=chart_canvas.bbox("all")))
        body_window = chart_canvas.create_window((0, 0), window=body, anchor="nw")
        chart_canvas.configure(yscrollcommand=chart_scroll.set)
        chart_canvas.bind("<Configure>", lambda e: chart_canvas.itemconfigure(body_window, width=e.width))
        chart_canvas.pack(side="left", fill="both", expand=True)
        chart_scroll.pack(side="right", fill="y")

        stats = tk.Frame(body, bg=BG)
        stats.pack(fill="x", pady=(0, 18))
        self.stat(stats, "TOTAL ATTEMPTS", len(attempts), "All quiz attempts")
        self.stat(stats, "AVERAGE SCORE", f"{avg}%", "Completed quizzes")
        self.stat(stats, "PASSED QUIZZES", sum(a["result_status"] == "Pass" for a in completed), "Keep it up")

        self.label(body, "Subject-wise Performance", 14, INK, True).pack(anchor="w", pady=(2, 9))
        subject_cols = ("subject", "quizzes", "attempts", "average_marks", "average_percent")
        subject_tree = ttk.Treeview(body, columns=subject_cols, show="headings", height=max(2, min(6, len(completed))))
        for col, title, width in zip(subject_cols,
                ("Subject", "Quizzes Taken", "Attempts", "Average Marks", "Average Score"),
                (270, 150, 120, 150, 150)):
            subject_tree.heading(col, text=title)
            subject_tree.column(col, width=width, anchor="w")
        subject_tree.pack(fill="x", pady=(0, 18))
        subject_rows = self.rows(
            "SELECT s.subject_name,COUNT(DISTINCT q.quiz_id) AS quizzes_taken,COUNT(a.attempt_id) AS attempts,"
            "AVG(a.score) AS avg_marks,AVG(a.percentage) AS avg_percent "
            "FROM quiz_attempts a JOIN quizzes q ON q.quiz_id=a.quiz_id "
            "JOIN subjects s ON s.subject_id=q.subject_id "
            "WHERE a.user_id=? AND a.status IN ('Submitted','Timed Out') "
            "GROUP BY s.subject_id,s.subject_name ORDER BY s.subject_name",
            (self.user["user_id"],),
        )
        for row in subject_rows:
            subject_tree.insert("", "end", values=(row["subject_name"], row["quizzes_taken"], row["attempts"],
                f"{(row['avg_marks'] or 0):g}", f"{(row['avg_percent'] or 0):.1f}%"))
        if not subject_rows:
            subject_tree.insert("", "end", values=("No completed quizzes yet", "—", "—", "—", "—"))

        self.label(body, "Monthly Quiz Trends", 14, INK, True).pack(anchor="w", pady=(1, 9))
        plots = tk.Frame(body, bg=BG)
        plots.pack(fill="x", pady=(0, 18))
        left = tk.Frame(plots, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        right = tk.Frame(plots, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right.pack(side="left", fill="both", expand=True, padx=(7, 0))

        dates = []
        for attempt in completed:
            try:
                dates.append(datetime.fromisoformat(attempt["started_at"]))
            except (TypeError, ValueError):
                continue
        if dates:
            first_month = min(dates).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_keys = []
            cursor = first_month
            while cursor <= last_month:
                month_keys.append(cursor.strftime("%Y-%m"))
                cursor = (cursor.replace(day=calendar.monthrange(cursor.year, cursor.month)[1]) + timedelta(days=1)).replace(day=1)
        else:
            now = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_keys = []
            cursor = now
            for _ in range(5):
                month_keys.insert(0, cursor.strftime("%Y-%m"))
                cursor = (cursor - timedelta(days=1)).replace(day=1)
        month_labels = [datetime.strptime(key, "%Y-%m").strftime("%b %Y") for key in month_keys]
        counts = {key: 0 for key in month_keys}
        marks = {key: [] for key in month_keys}
        for attempt in completed:
            try:
                key = datetime.fromisoformat(attempt["started_at"]).strftime("%Y-%m")
            except (TypeError, ValueError):
                continue
            if key in counts:
                counts[key] += 1
                marks[key].append(float(attempt["score"]))
        average_marks = [sum(marks[key]) / len(marks[key]) if marks[key] else 0 for key in month_keys]
        self.draw_month_chart(left, month_labels, [counts[key] for key in month_keys],
                              "Quizzes Taken by Month", "Number of quizzes", integer_axis=True)
        self.draw_month_chart(right, month_labels, average_marks,
                              "Average Marks by Month", "Average marks", integer_axis=False)

        self.label(body, "Recent Attempts", 14, INK, True).pack(anchor="w", pady=(1, 9))
        cols = ("title", "subject", "started_at", "score", "percentage", "status", "result_status")
        tree = ttk.Treeview(body, columns=cols, show="headings", height=7)
        for col, title, width in zip(cols,
                ("Quiz", "Subject", "Date", "Score", "Percentage", "Status", "Result"),
                (200, 145, 155, 100, 100, 110, 90)):
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="x", pady=(0, 15))
        for attempt in attempts:
            tree.insert("", "end", values=(attempt["title"], attempt["subject_name"], attempt["started_at"],
                f"{attempt['score']:g}/{attempt['total_marks']:g}", f"{attempt['percentage']:g}%",
                attempt["status"], attempt["result_status"] or "—"))
        if not attempts:
            self.empty(body, "No attempts yet", "Take a published quiz to see your progress here.")

    def draw_month_chart(self, parent, month_labels, values, title, y_label, integer_axis=False):
        figure = Figure(figsize=(5.2, 2.8), dpi=100, facecolor=WHITE)
        axis = figure.add_subplot(111)
        axis.set_facecolor(WHITE)
        positions = list(range(len(month_labels)))
        if integer_axis:
            axis.bar(positions, values, color=PURPLE, width=0.62)
        else:
            axis.plot(positions, values, color=PURPLE, marker="o", linewidth=2.2, markersize=5)
            axis.fill_between(positions, values, color=PURPLE, alpha=0.10)
        axis.set_title(title, loc="left", fontsize=11, color=INK, pad=12, fontweight="bold")
        axis.set_ylabel(y_label, fontsize=8, color=MUTED)
        axis.set_xticks(positions)
        axis.set_xticklabels(month_labels, rotation=35, ha="right", fontsize=7)
        axis.tick_params(axis="y", labelsize=8, colors=MUTED)
        axis.tick_params(axis="x", colors=MUTED)
        axis.grid(axis="y", color=LINE, linewidth=0.8)
        axis.set_axisbelow(True)
        for edge in ("top", "right"):
            axis.spines[edge].set_visible(False)
        axis.spines["left"].set_color(LINE)
        axis.spines["bottom"].set_color(LINE)
        if integer_axis:
            axis.set_ylim(bottom=0)
        figure.tight_layout(pad=1.6)
        chart = FigureCanvasTkAgg(figure, master=parent)
        chart.draw()
        chart.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def show_manage_subjects(self):
        area = self.shell("Manage Subjects", "manage_subjects", "Create and manage quiz subjects")
        self.heading(area, "Manage Subjects", "Add subjects and review their quiz activity",
                     self.add_subject, "+ Add subject")
        query = """
            SELECT s.subject_id, s.subject_name, COALESCE(s.description, '') AS description,
                   s.created_at, s.is_active,
                   (SELECT COUNT(*) FROM quizzes q
                    WHERE q.subject_id=s.subject_id AND q.status='Published') AS active_quizzes,
                   (SELECT COUNT(DISTINCT a.user_id) FROM quiz_attempts a
                    JOIN quizzes q ON q.quiz_id=a.quiz_id
                    WHERE q.subject_id=s.subject_id AND a.status IN ('Submitted','Timed Out')) AS students_taken,
                   (SELECT COUNT(*) FROM quizzes q WHERE q.subject_id=s.subject_id) AS total_quizzes
            FROM subjects s ORDER BY s.subject_id
        """
        subjects = self.rows(query)
        columns = ("serial", "subject_name", "description", "created_at", "status",
                   "active_quizzes", "students_taken", "total_quizzes")
        headings = ("Serial Number", "Subject Name", "Its Description", "Created At", "Status",
                    "Active Quizzes", "Students Taken", "Total Quizzes")
        widths = (95, 145, 240, 155, 90, 130, 145, 120)
        container = tk.Frame(area, bg=BG)
        container.pack(fill="both", expand=True)
        table = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        for col, heading, width in zip(columns, headings, widths):
            table.heading(col, text=heading)
            table.column(col, width=width, minwidth=75, anchor="w", stretch=False)
        ybar = ttk.Scrollbar(container, orient="vertical", command=table.yview)
        xbar = ttk.Scrollbar(container, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        table.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        for serial, subject in enumerate(subjects, 1):
            table.insert("", "end", iid=str(subject["subject_id"]), values=(serial,
                subject["subject_name"], subject["description"], subject["created_at"],
                "Active" if subject["is_active"] else "Inactive", subject["active_quizzes"],
                subject["students_taken"], subject["total_quizzes"]))
        buttons = tk.Frame(area, bg=BG)
        buttons.pack(fill="x", pady=(12, 0))
        self.button(buttons, "Edit selected", lambda: self.edit_subject(table), primary=False).pack(side="left")
        if not subjects:
            self.empty(area, "No subjects yet", "Add a subject to organize your questions and quizzes.")

    def add_subject(self):
        self.subject_dialog()

    def edit_subject(self, table):
        subject_id = self.selected_id(table)
        if subject_id is not None:
            self.subject_dialog(subject_id)

    def subject_dialog(self, subject_id=None):
        subject = self.one("SELECT * FROM subjects WHERE subject_id=?", (subject_id,)) if subject_id else None
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Subject" if subject else "Add Subject")
        dialog.configure(bg=WHITE)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.geometry("480x390")
        self.label(dialog, "Edit Subject" if subject else "Add Subject", 18, INK, True).pack(anchor="w", padx=24, pady=(22, 4))
        self.label(dialog, "Enter the subject details and status.", 9, MUTED).pack(anchor="w", padx=24, pady=(0, 17))
        name_var = tk.StringVar(value=subject["subject_name"] if subject else "")
        desc_var = tk.StringVar(value=subject["description"] or "" if subject else "")
        status_var = tk.StringVar(value="Active" if subject and subject["is_active"] else ("Inactive" if subject else "Active"))
        self.label(dialog, "Subject name", 9, MUTED, True).pack(anchor="w", padx=24, pady=(4, 5))
        name_entry = self.entry(dialog, name_var)
        name_entry.pack(fill="x", padx=24, ipady=8)
        self.label(dialog, "Description", 9, MUTED, True).pack(anchor="w", padx=24, pady=(15, 5))
        desc_entry = self.entry(dialog, desc_var)
        desc_entry.pack(fill="x", padx=24, ipady=8)
        self.label(dialog, "Status", 9, MUTED, True).pack(anchor="w", padx=24, pady=(15, 5))
        ttk.Combobox(dialog, textvariable=status_var, values=("Active", "Inactive"), state="readonly", width=18).pack(anchor="w", padx=24, ipady=4)
        actions = tk.Frame(dialog, bg=WHITE)
        actions.pack(fill="x", padx=24, pady=(22, 18))

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Subject name required", "Enter a name for this subject.", parent=dialog)
                return
            active = int(status_var.get() == "Active")
            try:
                if subject:
                    self.q("UPDATE subjects SET subject_name=?,description=?,is_active=? WHERE subject_id=?",
                           (name, desc_var.get().strip(), active, subject_id))
                else:
                    self.q("INSERT INTO subjects(subject_name,description,is_active) VALUES(?,?,?)",
                           (name, desc_var.get().strip(), active))
                self.commit()
                dialog.destroy()
                self.show_manage_subjects()
            except sqlite3.IntegrityError:
                self.db.rollback()
                messagebox.showerror("Subject not saved", "A subject with that name already exists.", parent=dialog)

        self.button(actions, "Save subject", save).pack(side="right")
        self.button(actions, "Cancel", dialog.destroy, primary=False).pack(side="right", padx=(0, 8))
        name_entry.focus_set()

    def show_admin_dashboard(self):
        area = self.shell("Admin Dashboard", "admin_dashboard", "Overview of your quiz platform")
        self.heading(area, "Admin Dashboard", "Manage quizzes, questions, subjects, and students")
        n_users = self.one("SELECT COUNT(*) n FROM users WHERE role='Student' AND is_active=1")["n"]
        n_quiz = self.one("SELECT COUNT(*) n FROM quizzes")["n"]
        n_questions = self.one("SELECT COUNT(*) n FROM questions WHERE is_active=1")["n"]
        n_attempts = self.one("SELECT COUNT(*) n FROM quiz_attempts WHERE status!='In Progress'")["n"]
        stats = tk.Frame(area, bg=BG); stats.pack(fill="x", pady=(0, 22))
        self.stat(stats, "TOTAL STUDENTS", n_users, "Active accounts")
        self.stat(stats, "TOTAL QUIZZES", n_quiz, "All quiz statuses")
        self.stat(stats, "QUESTION BANK", n_questions, "Active questions")
        self.stat(stats, "QUIZ ATTEMPTS", n_attempts, "Submitted attempts")
        self.heading(area, "Recent Quizzes", "Your latest quiz activity", self.show_manage_quizzes, "Manage quizzes")
        self.quiz_table(area, admin=True, limit=6)

    def quiz_table(self, parent, admin=False, limit=None):
        sql = "SELECT q.quiz_id,q.title,s.subject_name,q.duration_minutes,q.total_marks,q.status FROM quizzes q JOIN subjects s ON s.subject_id=q.subject_id ORDER BY q.created_at DESC"
        data = self.rows(sql + (" LIMIT ?" if limit else ""), (limit,) if limit else ())
        cols = ("id", "title", "subject_name", "duration_minutes", "total_marks", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        labels = ("ID", "Quiz title", "Subject", "Duration", "Total marks", "Status")
        widths = (55, 245, 190, 100, 100, 110)
        for c, label, width in zip(cols, labels, widths):
            tree.heading(c, text=label); tree.column(c, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for r in data: tree.insert("", "end", iid=str(r["quiz_id"]), values=(r["quiz_id"], r["title"], r["subject_name"], f"{r['duration_minutes']} min", f"{r['total_marks']:g}", r["status"]))
        return tree

    def show_manage_quizzes(self):
        area = self.shell("Manage Quizzes", "manage_quizzes", "Create and manage your quizzes")
        self.heading(area, "Manage Quizzes", "Create, publish, and update quizzes",
                     self.show_quiz_form, "+ Create quiz")
        self.quiz_table(area, admin=True)
        actions = tk.Frame(area, bg=BG); actions.pack(fill="x", pady=12)
        tree = area.winfo_children()[-2]
        self.button(actions, "Edit selected", lambda: self.edit_selected_quiz(tree), primary=False).pack(side="left", padx=(0, 8))
        self.button(actions, "Change status", lambda: self.change_quiz_status(tree)).pack(side="left")

    def selected_id(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select a row", "Select a quiz first."); return None
        return int(selected[0])

    def edit_selected_quiz(self, tree):
        qid = self.selected_id(tree)
        if qid: self.show_quiz_form(qid)

    def change_quiz_status(self, tree):
        qid = self.selected_id(tree)
        if not qid: return
        q = self.one("SELECT status FROM quizzes WHERE quiz_id=?", (qid,))
        nxt = "Published" if q["status"] == "Draft" else "Closed" if q["status"] == "Published" else "Draft"
        self.q("UPDATE quizzes SET status=? WHERE quiz_id=?", (nxt, qid)); self.commit(); self.show_manage_quizzes()

    def show_quiz_form(self, quiz_id=None):
        old = self.one("SELECT * FROM quizzes WHERE quiz_id=?", (quiz_id,)) if quiz_id else None
        area = self.shell("Edit Quiz" if old else "Create Quiz", "manage_quizzes", "Enter quiz details and add questions")
        self.heading(area, "Edit Quiz" if old else "Create a Quiz", "Quiz settings and questions")
        canvas = tk.Canvas(area, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=BG)
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw", width=area.winfo_width()-18)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure("all", width=e.width))
        details = tk.Frame(form, bg=WHITE, highlightthickness=1, highlightbackground=LINE); details.pack(fill="x", pady=(0, 14))
        self.label(details, "Quiz Details", 13, INK, True).pack(anchor="w", padx=18, pady=(16, 12))
        subjects = self.rows("SELECT subject_id,subject_name FROM subjects WHERE is_active=1 ORDER BY subject_name")
        if not subjects:
            messagebox.showerror("No subjects", "Add an active subject to the subjects table before creating a quiz.")
            return self.show_manage_quizzes()
        self.quiz_title = tk.StringVar(value=old["title"] if old else "")
        self.quiz_desc = tk.StringVar(value=old["description"] or "" if old else "")
        self.quiz_instructions = tk.StringVar(value=old["instructions"] or "" if old else "")
        self.quiz_duration = tk.StringVar(value=str(old["duration_minutes"] if old else 10))
        self.quiz_pass = tk.StringVar(value=str(old["passing_marks"] if old else 0))
        self.quiz_total = tk.StringVar(value=str(old["total_marks"] if old else 0))
        self.quiz_subject = tk.StringVar(value=str(old["subject_id"] if old else subjects[0]["subject_id"]))
        self.subject_map = {s["subject_name"]: s["subject_id"] for s in subjects}
        self.subject_names = list(self.subject_map)
        self.form_row(details, "Title", self.quiz_title)
        self.form_row(details, "Description", self.quiz_desc)
        self.form_row(details, "Instructions", self.quiz_instructions)
        row = tk.Frame(details, bg=WHITE); row.pack(fill="x", padx=18, pady=5)
        self.label(row, "Subject", 9, MUTED, True).pack(side="left", padx=(0, 16))
        self.subject_combo = ttk.Combobox(row, values=self.subject_names, state="readonly", width=25)
        current = next((name for name, sid in self.subject_map.items() if sid == int(self.quiz_subject.get())), self.subject_names[0])
        self.subject_combo.set(current); self.subject_combo.pack(side="left", ipady=4)
        row2 = tk.Frame(details, bg=WHITE); row2.pack(fill="x", padx=18, pady=8)
        for label, var, width in (("Duration (minutes)", self.quiz_duration, 16), ("Passing marks", self.quiz_pass, 14)):
            col = tk.Frame(row2, bg=WHITE); col.pack(side="left", padx=(0, 28))
            self.label(col, label, 9, MUTED, True).pack(anchor="w", pady=(0, 5))
            self.entry(col, var, width=width).pack(ipady=7)
        self.label(details, "Status", 9, MUTED, True).pack(anchor="w", padx=18, pady=(4, 5))
        self.quiz_status = tk.StringVar(value=old["status"] if old else "Draft")
        ttk.Combobox(details, textvariable=self.quiz_status, values=("Draft", "Published", "Closed"), state="readonly", width=16).pack(anchor="w", padx=18, pady=(0, 16), ipady=4)
        qbox = tk.Frame(form, bg=WHITE, highlightthickness=1, highlightbackground=LINE); qbox.pack(fill="x", pady=(0, 14))
        qhead = tk.Frame(qbox, bg=WHITE); qhead.pack(fill="x", padx=18, pady=15)
        self.label(qhead, "Questions", 13, INK, True).pack(side="left")
        self.button(qhead, "+ Add question", self.add_question_row, primary=False).pack(side="right")
        self.qrows_parent = tk.Frame(qbox, bg=WHITE); self.qrows_parent.pack(fill="x", padx=18, pady=(0, 14))
        self.question_widgets = []
        if old:
            linked = self.rows("SELECT qu.question_id,qu.question_text,qq.marks FROM quiz_questions qq JOIN questions qu ON qu.question_id=qq.question_id WHERE qq.quiz_id=? ORDER BY qq.question_order", (quiz_id,))
            for q in linked: self.add_question_row(q["question_id"], q["marks"])
        totalrow = tk.Frame(form, bg=BG); totalrow.pack(fill="x", pady=3)
        self.total_display = self.label(totalrow, "Total marks: 0", 10, INK, True); self.total_display.pack(side="left")
        self.quiz_total.set("0")
        actions = tk.Frame(form, bg=BG); actions.pack(fill="x", pady=12)
        self.button(actions, "Save quiz", lambda: self.save_quiz(quiz_id)).pack(side="right", padx=(8, 0))
        self.button(actions, "Cancel", self.show_manage_quizzes, primary=False).pack(side="right")
        self.update_total()

    def form_row(self, parent, name, variable):
        row = tk.Frame(parent, bg=WHITE); row.pack(fill="x", padx=18, pady=5)
        self.label(row, name, 9, MUTED, True).pack(anchor="w", pady=(0, 5))
        self.entry(row, variable).pack(fill="x", ipady=7)

    def add_question_row(self, question_id=None, marks=1):
        row = tk.Frame(self.qrows_parent, bg="#FAFAFD", highlightthickness=1, highlightbackground=LINE)
        row.pack(fill="x", pady=5)
        question_list = self.rows("SELECT question_id,question_text FROM questions WHERE subject_id=? AND is_active=1 ORDER BY question_id DESC", (int(self.quiz_subject.get()),))
        choices = {f"{item['question_id']} · {item['question_text']}": item["question_id"] for item in question_list}
        selected = next((name for name, qid in choices.items() if qid == question_id), "")
        textvar, markvar = tk.StringVar(value=selected), tk.StringVar(value=str(marks))
        tk.Label(row, text=f"Q{len(self.question_widgets)+1}", bg="#FAFAFD", fg=PURPLE,
                 font=(FONT, 9, "bold")).pack(side="left", padx=10)
        combo = ttk.Combobox(row, textvariable=textvar, values=list(choices), state="readonly")
        combo.pack(side="left", fill="x", expand=True, padx=4, pady=9, ipady=4)
        marks_entry = self.entry(row, markvar, width=7); marks_entry.pack(side="left", padx=8, ipady=6)
        tk.Label(row, text="marks", bg="#FAFAFD", fg=MUTED, font=(FONT, 8)).pack(side="left", padx=(0, 8))
        tk.Button(row, text="×", command=lambda r=row: self.remove_question_row(r), bg="#FAFAFD", fg=RED,
                  font=(FONT, 15), bd=0, cursor="hand2").pack(side="right", padx=8)
        self.question_widgets.append((row, textvar, markvar, choices))
        markvar.trace_add("write", lambda *_: self.update_total())
        self.update_total()

    def remove_question_row(self, row):
        row.destroy()
        self.question_widgets = [q for q in self.question_widgets if q[0] != row]
        self.update_total()

    def update_total(self):
        if not hasattr(self, "total_display") or not self.total_display.winfo_exists(): return
        total = sum(float(m.get() or 0) for _, _, m, _ in self.question_widgets if (m.get() or "0").replace(".", "", 1).isdigit())
        self.quiz_total.set(str(total)); self.total_display.config(text=f"Total marks: {total:g}")

    def save_quiz(self, quiz_id=None):
        title = self.quiz_title.get().strip()
        try:
            duration = int(self.quiz_duration.get()); passing = float(self.quiz_pass.get() or 0)
            question_data = [(choices.get(t.get()), float(m.get())) for _, t, m, choices in self.question_widgets]
        except ValueError:
            return messagebox.showerror("Check the values", "Duration, passing marks, and question marks must be valid numbers.")
        total = sum(m for _, m in question_data)
        if not title or duration <= 0 or passing < 0 or passing > total:
            return messagebox.showerror("Check the quiz details", "Enter a title and positive duration. Passing marks must be between zero and the total marks.")
        if any(not qid or m < 0 for qid, m in question_data):
            return messagebox.showerror("Check the questions", "Choose a question from the active question bank for every row and enter non-negative marks. Add questions in Question Bank first.")
        if len({qid for qid, _ in question_data}) != len(question_data):
            return messagebox.showerror("Duplicate question", "Choose each question only once in a quiz.")
        if len(question_data) == 0:
            return messagebox.showerror("No questions", "Add at least one question from the active question bank.")
        subject_id = self.subject_map.get(self.subject_combo.get())
        if any(not self.one("SELECT 1 FROM questions WHERE question_id=? AND subject_id=? AND is_active=1", (qid, subject_id)) for qid, _ in question_data):
            return messagebox.showerror("Question subject mismatch", "Every selected question must belong to the quiz subject and be active.")
        try:
            self.db.execute("BEGIN")
            if quiz_id:
                self.q("UPDATE quizzes SET subject_id=?,title=?,description=?,instructions=?,duration_minutes=?,total_marks=?,passing_marks=?,status=? WHERE quiz_id=?",
                       (subject_id,title,self.quiz_desc.get().strip(),self.quiz_instructions.get().strip(),duration,total,passing,self.quiz_status.get(),quiz_id))
                self.q("DELETE FROM quiz_questions WHERE quiz_id=?", (quiz_id,))
            else:
                cur = self.q("INSERT INTO quizzes(subject_id,title,description,instructions,duration_minutes,total_marks,passing_marks,status,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                             (subject_id,title,self.quiz_desc.get().strip(),self.quiz_instructions.get().strip(),duration,total,passing,self.quiz_status.get(),self.user["user_id"]))
                quiz_id = cur.lastrowid
            for index, (question_id, marks) in enumerate(question_data, 1):
                self.q("INSERT INTO quiz_questions(quiz_id,question_id,marks,question_order) VALUES(?,?,?,?)", (quiz_id,question_id,marks,index))
            self.commit()
            messagebox.showinfo("Saved", "Quiz details and selected questions were saved.")
            self.show_manage_quizzes()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            messagebox.showerror("Could not save quiz", f"The database rejected this quiz: {exc}")

    def show_question_bank(self):
        area = self.shell("Question Bank", "question_bank", "Create and review reusable quiz questions")
        self.heading(area, "Question Bank", "Questions are linked to subjects and can be reused in quizzes",
                     self.show_question_form, "+ Add question")
        rows = self.rows("SELECT qu.question_id,qu.question_text,qu.question_type,qu.difficulty,s.subject_name,COUNT(o.option_id) options FROM questions qu JOIN subjects s ON s.subject_id=qu.subject_id LEFT JOIN options o ON o.question_id=qu.question_id WHERE qu.is_active=1 GROUP BY qu.question_id ORDER BY qu.created_at DESC")
        cols = ("id", "question_text", "subject_name", "question_type", "difficulty", "options")
        tree = ttk.Treeview(area, columns=cols, show="headings")
        for c, label, width in zip(cols, ("ID", "Question", "Subject", "Type", "Difficulty", "Options"), (55, 430, 150, 90, 100, 75)):
            tree.heading(c, text=label); tree.column(c, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for r in rows: tree.insert("", "end", iid=str(r["question_id"]), values=(r["question_id"],r["question_text"],r["subject_name"],r["question_type"],r["difficulty"],r["options"]))
        actions = tk.Frame(area, bg=BG); actions.pack(fill="x", pady=12)
        self.button(actions, "Edit selected", lambda: self.edit_question(tree), primary=False).pack(side="left", padx=(0, 8))
        self.button(actions, "Delete selected Question", lambda: self.deactivate_question(tree)).pack(side="left")
        if not rows: self.empty(area, "Your question bank is empty", "Add a question to start building quizzes.")

    def edit_question(self, tree):
        qid = self.selected_id(tree)
        if qid: self.show_question_form(qid)

    def deactivate_question(self, tree):
        qid = self.selected_id(tree)
        if qid:
            try:
                self.q("UPDATE questions SET is_active=0 WHERE question_id=?", (qid,)); self.commit(); self.show_question_bank()
            except sqlite3.IntegrityError as exc:
                messagebox.showerror("Question is in use", f"This question is linked to a quiz and cannot be changed right now.\n{exc}")

    def show_question_form(self, question_id=None):
        q = self.one("SELECT * FROM questions WHERE question_id=?", (question_id,)) if question_id else None
        area = self.shell("Question Bank", "question_bank", "Add a question and its answer options")
        self.heading(area, "Edit Question" if q else "Add a Question", "Choose at least one correct option")
        box = tk.Frame(area, bg=WHITE, highlightthickness=1, highlightbackground=LINE); box.pack(fill="both", expand=True)
        subjects = self.rows("SELECT subject_id,subject_name FROM subjects WHERE is_active=1 ORDER BY subject_name")
        if not subjects: return self.empty(area, "No active subjects", "Add a subject in the database before adding questions.")
        self.q_text = tk.StringVar(value=q["question_text"] if q else "")
        self.q_subject = tk.StringVar(value=str(q["subject_id"] if q else subjects[0]["subject_id"]))
        self.q_type = tk.StringVar(value=q["question_type"] if q else "MCQ")
        self.q_difficulty = tk.StringVar(value=q["difficulty"] if q else "Medium")
        self.q_explanation = tk.StringVar(value=q["explanation"] or "" if q else "")
        self.subject_map = {s["subject_name"]: s["subject_id"] for s in subjects}
        self.label(box, "Question text", 9, MUTED, True).pack(anchor="w", padx=20, pady=(18, 6))
        self.entry(box, self.q_text).pack(fill="x", padx=20, ipady=8)
        row = tk.Frame(box, bg=WHITE); row.pack(fill="x", padx=20, pady=14)
        self.label(row, "Subject", 9, MUTED, True).pack(side="left", padx=(0, 8))
        self.q_subject_combo = ttk.Combobox(row, values=list(self.subject_map), state="readonly", width=23)
        selected = next((n for n,i in self.subject_map.items() if i==int(self.q_subject.get())), list(self.subject_map)[0]); self.q_subject_combo.set(selected); self.q_subject_combo.pack(side="left", padx=(0, 20))
        self.label(row, "Type", 9, MUTED, True).pack(side="left", padx=(0, 8))
        ttk.Combobox(row, textvariable=self.q_type, values=("MCQ","MSQ"), state="readonly", width=9).pack(side="left", padx=(0, 20))
        self.label(row, "Difficulty", 9, MUTED, True).pack(side="left", padx=(0, 8))
        ttk.Combobox(row, textvariable=self.q_difficulty, values=("Easy","Medium","Hard"), state="readonly", width=10).pack(side="left")
        self.label(box, "Answer options  (check every correct answer)", 10, INK, True).pack(anchor="w", padx=20, pady=(4, 8))
        existing = self.rows("SELECT * FROM options WHERE question_id=? ORDER BY option_order", (question_id,)) if q else []
        self.option_vars = []
        for i in range(max(4, len(existing))):
            line = tk.Frame(box, bg=WHITE); line.pack(fill="x", padx=20, pady=4)
            textv = tk.StringVar(value=existing[i]["option_text"] if i < len(existing) else "")
            correctv = tk.BooleanVar(value=bool(existing[i]["is_correct"]) if i < len(existing) else False)
            tk.Checkbutton(line, variable=correctv, bg=WHITE, activebackground=WHITE).pack(side="left")
            self.entry(line, textv).pack(side="left", fill="x", expand=True, ipady=7)
            self.option_vars.append((textv, correctv))
        self.label(box, "Explanation (optional)", 9, MUTED, True).pack(anchor="w", padx=20, pady=(14, 5))
        self.entry(box, self.q_explanation).pack(fill="x", padx=20, ipady=7)
        btns = tk.Frame(box, bg=WHITE); btns.pack(fill="x", padx=20, pady=18)
        self.button(btns, "Save question", lambda: self.save_question(question_id)).pack(side="right")
        self.button(btns, "Cancel", self.show_question_bank, primary=False).pack(side="right", padx=8)

    def save_question(self, question_id=None):
        text = self.q_text.get().strip()
        opts = [(t.get().strip(), bool(v.get())) for t,v in self.option_vars if t.get().strip()]
        if not text or len(opts) < 2 or not any(correct for _,correct in opts):
            return messagebox.showerror("Check the question", "Enter question text, at least two options, and at least one correct answer.")
        if self.q_type.get() == "MCQ" and sum(correct for _,correct in opts) != 1:
            return messagebox.showerror("Check the answers", "An MCQ must have exactly one correct option. Choose MSQ for multiple correct answers.")
        sid = self.subject_map[self.q_subject_combo.get()]
        try:
            if question_id:
                self.q("UPDATE questions SET subject_id=?,question_text=?,question_type=?,difficulty=?,explanation=?,is_active=1 WHERE question_id=?",
                       (sid,text,self.q_type.get(),self.q_difficulty.get(),self.q_explanation.get().strip(),question_id))
                self.q("DELETE FROM options WHERE question_id=?", (question_id,))
            else:
                cur = self.q("INSERT INTO questions(subject_id,question_text,question_type,difficulty,explanation,created_by) VALUES(?,?,?,?,?,?)",
                             (sid,text,self.q_type.get(),self.q_difficulty.get(),self.q_explanation.get().strip(),self.user["user_id"]))
                question_id = cur.lastrowid
            for order,(label,correct) in enumerate(opts,1):
                self.q("INSERT INTO options(question_id,option_text,is_correct,option_order) VALUES(?,?,?,?)", (question_id,label,int(correct),order))
            self.commit(); self.show_question_bank()
        except sqlite3.IntegrityError as exc:
            self.db.rollback(); messagebox.showerror("Could not save question", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizLab(root)
    def close_app():
        try: app.db.close()
        finally: root.destroy()
    root.protocol("WM_DELETE_WINDOW", close_app)
    root.mainloop()
