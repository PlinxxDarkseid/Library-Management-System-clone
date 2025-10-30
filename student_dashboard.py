import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from datetime import datetime

class StudentDashboard:
    def __init__(self, student_id):
        self.db = Database()
        self.student_id = student_id
        self.root = tk.Tk()
        self.root.title("Student Dashboard")
        self.root.geometry("900x600")
        self.root.configure(bg="#f7f9fc")
        self.root.resizable(False, False)

        info = self.db.get_student(student_id)
        self.name = info["FullName"]
        self.score_val = info["Score"]
        self.streak_val = info["ReadingStreak"]

        tk.Label(self.root, text=f"Welcome, {self.name}", font=("Segoe UI", 18, "bold"),
                 bg="#f7f9fc", fg="#333").pack(pady=10)

        header = tk.Frame(self.root, bg="#f7f9fc")
        header.pack(pady=10)

        self.score_var = tk.StringVar(value=f"Score: {self.score_val}")
        self.streak_var = tk.StringVar(value=f"Streak: {self.streak_val} days")

        tk.Label(header, textvariable=self.score_var, font=("Segoe UI", 12), bg="#f7f9fc") \
            .grid(row=0, column=0, padx=20)
        tk.Label(header, textvariable=self.streak_var, font=("Segoe UI", 12), bg="#f7f9fc") \
            .grid(row=0, column=1, padx=20)

        self.score_bar = ttk.Progressbar(header, length=200, maximum=500)
        self.score_bar.grid(row=1, column=0, padx=20, pady=5)
        self.streak_bar = ttk.Progressbar(header, length=200, maximum=10)
        self.streak_bar.grid(row=1, column=1, padx=20, pady=5)

        self.update_progress()

        frame = ttk.Notebook(self.root)
        frame.pack(expand=True, fill="both", pady=10)

        self.books_tab(frame)
        self.reading_tab(frame)
        self.history_tab(frame)
        self.badges_tab(frame)

        status = tk.Label(self.root, text="📘 Keep reading to grow your streak!", bg="#eaf0f7", fg="#333", anchor="w")
        status.pack(fill="x", pady=5)

        self.root.mainloop()

    # Books tab shows ALL books and status
    def books_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Library Books")
        columns = ("ID", "Title", "Author", "Category", "Status")
        self.book_tree = ttk.Treeview(tab, columns=columns, show="headings")
        for col in columns:
            self.book_tree.heading(col, text=col)
            self.book_tree.column(col, width=150)
        self.book_tree.pack(expand=True, fill="both", padx=10, pady=10)
        ttk.Button(tab, text="Borrow Selected", command=self.borrow_selected).pack(pady=10)
        self.load_books()

    def load_books(self):
        self.book_tree.delete(*self.book_tree.get_children())
        books = self.db.fetchall("SELECT * FROM Book")
        for b in books:
            self.book_tree.insert("", "end", values=(
                b["BookID"], b["Title"], b["Author"], b["Category"], b["AvailabilityStatus"]
            ))

    def borrow_selected(self):
        selected = self.book_tree.focus()
        if not selected:
            messagebox.showwarning("Select Book", "Please select a book to borrow.")
            return
        book_data = self.book_tree.item(selected)["values"]
        book_id, title, status = book_data[0], book_data[1], book_data[4]
        if str(status).lower() == "borrowed":
            messagebox.showwarning("Unavailable", f"'{title}' is currently borrowed by another student.")
            return
        try:
            self.db.borrow_book(self.student_id, book_id, 1)
            # create reading record if not already active
            # ensure we don't create duplicates: check for existing unfinished session
            existing = self.db.fetchone(
                "SELECT ReadingID FROM ReadingHistory WHERE StudentID=? AND BookID=? AND Completed=0",
                (self.student_id, book_id)
            )
            if not existing:
                self.db.start_reading(self.student_id, book_id)
            messagebox.showinfo("Success", f"You've borrowed '{title}' successfully! It's added to your reading list.")
            self.load_books()
            self.load_reading_books()
            self.update_display()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Reading tab: show active reading sessions (not completed)
    def reading_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Reading")
        self.read_books = ttk.Treeview(tab, columns=("ID", "Title", "Status"), show="headings")
        self.read_books.heading("ID", text="Book ID")
        self.read_books.heading("Title", text="Book Title")
        self.read_books.heading("Status", text="Status")
        self.read_books.pack(expand=True, fill="both", padx=10, pady=10)
        btn_frame = tk.Frame(tab); btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Finish Reading", command=self.finish_reading).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_reading_books).grid(row=0, column=1, padx=5)
        self.load_reading_books()

    def load_reading_books(self):
        self.read_books.delete(*self.read_books.get_children())
        readings = self.db.fetchall(
            "SELECT r.BookID, b.Title FROM ReadingHistory r JOIN Book b ON r.BookID=b.BookID "
            "WHERE r.StudentID=? AND r.Completed=0",
            (self.student_id,)
        )
        for r in readings:
            self.read_books.insert("", "end", values=(r["BookID"], r["Title"], "Reading"))

    def finish_reading(self):
        selected = self.read_books.focus()
        if not selected:
            messagebox.showwarning("Select", "Choose a book from your reading list.")
            return
        book_id = self.read_books.item(selected)["values"][0]
        reading = self.db.fetchone(
            "SELECT ReadingID FROM ReadingHistory WHERE StudentID=? AND BookID=? AND Completed=0",
            (self.student_id, book_id)
        )
        if not reading:
            messagebox.showinfo("Info", "No active reading session found for this book.")
            return
        # mark reading completed (this updates score/streak in db.finish_reading)
        self.db.finish_reading(reading["ReadingID"])
        # update book availability to Available
        self.db.execute("UPDATE Book SET AvailabilityStatus='Available' WHERE BookID=?", (book_id,))
        messagebox.showinfo("Done", "Book marked as finished and is now available.")
        self.load_reading_books()
        self.load_books()
        self.load_history()
        self.update_display()
        self.show_motivation()

    # Reading history tab
    def history_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Reading History")
        cols = ("Book Title", "Start Date", "End Date", "Duration", "Completed")
        self.history_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c in cols:
            self.history_tree.heading(c, text=c)
            self.history_tree.column(c, width=150)
        self.history_tree.pack(expand=True, fill="both", padx=10, pady=10)
        ttk.Button(tab, text="Refresh", command=self.load_history).pack(pady=10)
        self.load_history()

    def load_history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        history = self.db.get_reading_history(self.student_id)
        for h in history:
            self.history_tree.insert("", "end", values=(
                h["Title"], h["StartDate"], h["EndDate"], h["DurationMinutes"], "Yes" if h["Completed"] else "No"
            ))

    # Badges tab
    def badges_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Achievements")
        self.badge_label = tk.Label(tab, text="", font=("Segoe UI", 13, "bold"))
        self.badge_label.pack(pady=20)
        ttk.Button(tab, text="Check Achievements", command=self.check_badges).pack()
        self.badge_output = tk.Label(tab, text="", wraplength=400, justify="center")
        self.badge_output.pack(pady=15)

    def check_badges(self):
        s = self.db.get_student(self.student_id)
        badges = []
        if s["ReadingStreak"] >= 3:
            badges.append("🔥 3-Day Streak Achiever")
        if s["ReadingStreak"] >= 7:
            badges.append("🏅 Weekly Warrior")
        if s["Score"] >= 200:
            badges.append("💡 Dedicated Reader")
        if s["Score"] >= 400:
            badges.append("🌟 Master Scholar")
        self.badge_output.config(text="\n".join(badges) if badges else "No badges yet. Keep reading!")
        self.badge_label.config(text=f"{len(badges)} Badge(s) Unlocked")

    def show_motivation(self):
        s = self.db.get_student(self.student_id)
        msgs = [
            "📖 Great job finishing another book!",
            "🔥 Consistency builds champions!",
            "💡 You're growing your knowledge every day.",
            "🏅 Keep it up, future leader!"
        ]
        if s["ReadingStreak"] in (3, 7, 10):
            messagebox.showinfo("Milestone Unlocked",
                                f"🏆 You've hit a {s['ReadingStreak']}-day streak!\nKeep the momentum going!")
        else:
            messagebox.showinfo("Motivation", msgs[datetime.now().second % len(msgs)])

    def update_display(self):
        s = self.db.get_student(self.student_id)
        self.score_val = s["Score"]
        self.streak_val = s["ReadingStreak"]
        self.score_var.set(f"Score: {self.score_val}")
        self.streak_var.set(f"Streak: {self.streak_val} days")
        self.update_progress()

    def update_progress(self):
        self.score_bar["value"] = min(self.score_val, 500)
        self.streak_bar["value"] = min(self.streak_val, 10)


if __name__ == "__main__":
    StudentDashboard(1)
