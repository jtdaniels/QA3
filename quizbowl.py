import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import random

class Question:
    def __init__(self, question_id, category, question_text, options, correct_answer):
        self.question_id = question_id
        self.category = category
        self.question_text = question_text
        self.options = options
        self.correct_answer = correct_answer

    def validate_answer(self, user_answer):
        return user_answer.upper() == self.correct_answer.upper()

class QuizBowlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Bowl Application")
        self.conn = sqlite3.connect("quiz_bowl.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.hashed_password = self.get_admin_password()

        self.current_user = None
        self.current_quiz_category = None
        self.questions = []
        self.score = 0
        self.question_index = 0

        self.show_login_screen()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                question_id INTEGER,
                question_text TEXT,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_answer TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        self.conn.commit()

        self.cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
        if self.cursor.fetchone() is None:
            hashed_password = hashlib.sha256("password".encode()).hexdigest()
            self.cursor.execute("INSERT INTO admin (username, password) VALUES ('admin', ?)", (hashed_password,))
            self.conn.commit()

    def get_admin_password(self):
        self.cursor.execute("SELECT password FROM admin WHERE username = 'admin'")
        result = self.cursor.fetchone()
        return result[0] if result else None

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        ttk.Label(self.root, text="Welcome to the Quiz Bowl!", font=("Arial", 20)).pack(pady=20)
        ttk.Button(self.root, text="Administrator Login", command=self.show_admin_login).pack(pady=10)
        ttk.Button(self.root, text="Quiz Taker", command=self.show_category_selection).pack(pady=10)

    def show_admin_login(self):
        self.clear_screen()
        ttk.Label(self.root, text="Administrator Login", font=("Arial", 16)).pack(pady=20)
        ttk.Label(self.root, text="Password:").pack()
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack()
        ttk.Button(self.root, text="Login", command=self.login).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.show_login_screen).pack(pady=10)

    def login(self):
        password = self.password_entry.get()
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if hashed_input == self.hashed_password:
            self.current_user = 'admin'
            self.show_admin_menu()
        else:
            messagebox.showerror("Login Failed", "Incorrect password.")
            self.password_entry.delete(0, tk.END)

    def show_admin_menu(self):
        self.clear_screen()
        ttk.Label(self.root, text="Administrator Menu", font=("Arial", 16)).pack(pady=20)
        ttk.Button(self.root, text="Add Question", command=self.show_add_question_form).pack(pady=10)
        ttk.Button(self.root, text="View Questions", command=self.show_view_questions_form).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.show_login_screen).pack(pady=10)

    def show_add_question_form(self):
        self.clear_screen()
        ttk.Label(self.root, text="Add New Question", font=("Arial", 16)).pack(pady=20)

        self.entries = {}
        self.cursor.execute("SELECT DISTINCT category FROM questions")
        categories = [r[0] for r in self.cursor.fetchall()]

        ttk.Label(self.root, text="Category:").pack()
        self.category_combobox = ttk.Combobox(self.root, values=categories, state="normal")
        self.category_combobox.pack()

        fields = ["Question Text", "Option A", "Option B", "Option C", "Option D", "Correct Answer (A, B, C, or D)"]
        for field in fields:
            ttk.Label(self.root, text=field + ":").pack()
            entry = ttk.Entry(self.root)
            entry.pack()
            self.entries[field] = entry

        ttk.Button(self.root, text="Add Question", command=self.add_question).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.show_admin_menu).pack(pady=10)

    def add_question(self):
        try:
            category = self.category_combobox.get()
            values = {k: e.get() for k, e in self.entries.items()}
            if not all(values.values()) or category == "" or values['Correct Answer (A, B, C, or D)'].upper() not in ('A', 'B', 'C', 'D'):
                raise ValueError("All fields required. Correct answer must be A-D.")
            self.cursor.execute("""
                INSERT INTO questions (category, question_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
            """, (category, values['Question Text'], values['Option A'], values['Option B'],
                  values['Option C'], values['Option D'], values['Correct Answer (A, B, C, or D)'].upper()))
            self.conn.commit()
            messagebox.showinfo("Success", "Question added!")
            for e in self.entries.values(): e.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_view_questions_form(self):
        self.clear_screen()
        ttk.Label(self.root, text="View Questions", font=("Arial", 16)).pack(pady=20)
        ttk.Label(self.root, text="Filter by Category:").pack()
        self.cursor.execute("SELECT DISTINCT category FROM questions")
        categories = [r[0] for r in self.cursor.fetchall()]
        categories.insert(0, "All")
        self.category_filter_combobox = ttk.Combobox(self.root, values=categories, state="readonly")
        self.category_filter_combobox.pack()
        self.category_filter_entry = ttk.Entry(self.root)
        self.category_filter_entry.pack()
        ttk.Button(self.root, text="View Questions", command=self.view_questions).pack(pady=10)

        self.tree = ttk.Treeview(self.root, columns=("ID", "Category", "Question"), show='headings')
        self.tree.heading("ID", text="ID")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Question", text="Question")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        ttk.Button(self.root, text="Modify Question", command=self.modify_question).pack(pady=5)
        ttk.Button(self.root, text="Delete Question", command=self.delete_question).pack(pady=5)
        ttk.Button(self.root, text="Back", command=self.show_admin_menu).pack(pady=10)

    def view_questions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        category_filter = self.category_filter_combobox.get()
        if category_filter == "All":
            category_filter = ""
        query = "SELECT * FROM questions WHERE category = ?" if category_filter else "SELECT * FROM questions"
        params = (category_filter,) if category_filter else ()
        self.cursor.execute(query, params)
        for q in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=(q[0], q[1], q[3]))

    def modify_question(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a question.")
            return
        qid = self.tree.item(selected[0])['values'][0]
        self.cursor.execute("SELECT * FROM questions WHERE id = ?", (qid,))
        q = self.cursor.fetchone()
        if not q:
            messagebox.showerror("Error", "Question not found.")
            return

        fields = ["Category", "Question Text", "Option A", "Option B", "Option C", "Option D", "Correct Answer"]
        new_values = []
        for i, label in enumerate(fields):
            val = simpledialog.askstring("Modify", f"{label}:", initialvalue=q[i+1])
            if not val:
                messagebox.showerror("Error", "All fields required.")
                return
            new_values.append(val)

        self.cursor.execute("""
            UPDATE questions SET category=?, question_text=?, option_a=?, option_b=?,
            option_c=?, option_d=?, correct_answer=? WHERE id=?
        """, (*new_values, qid))
        self.conn.commit()
        self.view_questions()

    def delete_question(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a question.")
            return
        qid = self.tree.item(selected[0])['values'][0]
        self.cursor.execute("DELETE FROM questions WHERE id = ?", (qid,))
        self.conn.commit()
        self.view_questions()

    def show_category_selection(self):
        self.clear_screen()
        ttk.Label(self.root, text="Select a Category", font=("Arial", 16)).pack(pady=20)
        self.cursor.execute("SELECT DISTINCT category FROM questions")
        categories = [r[0] for r in self.cursor.fetchall()]
        categories.append("Random Category")
        categories.append("Comprehensive")
        self.category_combobox = ttk.Combobox(self.root, values=categories, state="readonly")
        self.category_combobox.pack(pady=10)
        ttk.Button(self.root, text="Start Quiz", command=self.start_quiz).pack(pady=10)
        ttk.Button(self.root, text="Back", command=self.show_login_screen).pack(pady=10)

    def start_quiz(self):
        category = self.category_combobox.get()
        if category == "Random Category":
            self.cursor.execute("SELECT DISTINCT category FROM questions")
            categories = [r[0] for r in self.cursor.fetchall()]
            category = random.choice(categories) if categories else None

        if not category:
            messagebox.showerror("Error", "Select a category.")
            return

        if category == "Comprehensive":
            self.cursor.execute("SELECT * FROM questions")
        else:
            self.cursor.execute("SELECT * FROM questions WHERE category = ?", (category,))
        data = self.cursor.fetchall()
        random.shuffle(data)
        self.questions = [Question(q[2], q[1], q[3], [q[4], q[5], q[6], q[7]], q[8]) for q in data]
        if not self.questions:
            messagebox.showerror("Error", "No questions found.")
            return
        self.score = 0
        self.question_index = 0
        self.show_quiz_question()

    def show_quiz_question(self):
        self.clear_screen()
        if self.question_index >= len(self.questions):
            self.show_quiz_results()
            return
        q = self.questions[self.question_index]
        ttk.Label(self.root, text=q.question_text, font=("Arial", 14)).pack(pady=10)
        for i, opt in enumerate(q.options):
            ttk.Button(self.root, text=f"{chr(65+i)}. {opt}", command=lambda a=chr(65+i): self.check_answer(a)).pack(pady=5)
        self.feedback_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.feedback_label.pack(pady=10)

    def check_answer(self, answer):
        if self.questions[self.question_index].validate_answer(answer):
            self.score += 1
            self.feedback_label.config(text="Correct!", foreground="green")
        else:
            self.feedback_label.config(text="Incorrect!", foreground="red")
        self.question_index += 1
        self.root.after(1000, self.show_quiz_question)

    def show_quiz_results(self):
        self.clear_screen()
        ttk.Label(self.root, text="Quiz Results", font=("Arial", 20)).pack(pady=20)
        ttk.Label(self.root, text=f"Score: {self.score} / {len(self.questions)}", font=("Arial", 16)).pack(pady=10)
        percentage = (self.score / len(self.questions)) * 100
        ttk.Label(self.root, text=f"Percentage: {percentage:.2f}%", font=("Arial", 16)).pack(pady=10)
        ttk.Button(self.root, text="Back to Categories", command=self.show_category_selection).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizBowlApp(root)
    root.mainloop()
