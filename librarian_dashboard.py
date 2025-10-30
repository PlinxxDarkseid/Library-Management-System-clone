import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database
import csv
from datetime import datetime


class LibrarianDashboard:
    def __init__(self, librarian_id):
        self.db = Database()
        self.librarian_id = librarian_id

        self.root = tk.Tk()
        self.root.title("Librarian Dashboard")
        self.root.geometry("1050x650")
        self.root.configure(bg="#f7f9fc")
        self.root.resizable(False, False)

        tk.Label(self.root, text="Librarian Dashboard",
                 font=("Segoe UI", 18, "bold"), bg="#f7f9fc", fg="#222").pack(pady=10)

        tabs = ttk.Notebook(self.root)
        tabs.pack(expand=True, fill="both", padx=10, pady=10)

        self.books_tab(tabs)
        self.students_tab(tabs)
        self.manage_tab(tabs)
        self.reports_tab(tabs)
        self.leaderboard_tab(tabs)

        tk.Label(self.root, text="Crystal Heights Library System  |  © 2025",
                 bg="#e9eef5", fg="#333", anchor="center", font=("Segoe UI", 9)).pack(fill="x", pady=3)

        self.root.mainloop()

    # ------------------- MANAGE BOOKS -------------------
    def books_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Manage Books")

        form = tk.Frame(tab)
        form.pack(pady=10)

        tk.Label(form, text="Title").grid(row=0, column=0)
        tk.Label(form, text="Author").grid(row=0, column=2)
        tk.Label(form, text="Category").grid(row=1, column=0)

        self.title_entry = tk.Entry(form, width=25)
        self.author_entry = tk.Entry(form, width=25)
        self.cat_entry = tk.Entry(form, width=25)
        self.title_entry.grid(row=0, column=1)
        self.author_entry.grid(row=0, column=3)
        self.cat_entry.grid(row=1, column=1)

        ttk.Button(form, text="Add Book", command=self.add_book).grid(row=1, column=3, padx=5)
        ttk.Button(form, text="Delete Selected", command=self.delete_book).grid(row=1, column=4, padx=5)

        cols = ("BookID", "Title", "Author", "Category", "Status")
        self.book_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c in cols:
            self.book_tree.heading(c, text=c)
            self.book_tree.column(c, width=150)
        self.book_tree.pack(expand=True, fill="both", padx=10, pady=10)
        self.load_books()

    def load_books(self):
        self.book_tree.delete(*self.book_tree.get_children())
        for b in self.db.fetchall("SELECT * FROM Book"):
            self.book_tree.insert("", "end", values=(
                b["BookID"], b["Title"], b["Author"], b["Category"], b["AvailabilityStatus"]))

    def add_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        cat = self.cat_entry.get().strip()
        if not title or not author:
            messagebox.showwarning("Error", "Title and Author required.")
            return
        self.db.add_book(title, author, cat)
        self.load_books()
        messagebox.showinfo("Added", f"Book '{title}' added successfully.")
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.cat_entry.delete(0, tk.END)

    def delete_book(self):
        selected = self.book_tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Select a book to delete.")
            return
        book_id = self.book_tree.item(selected)["values"][0]
        self.db.delete_book(book_id)
        self.load_books()
        messagebox.showinfo("Deleted", "Book removed.")

    # ------------------- REGISTER STUDENTS -------------------
    def students_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Register Student")

        form = tk.Frame(tab)
        form.pack(pady=10)

        labels = ["Full Name", "Address", "Course", "Level", "DOB", "Username", "Password"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(form, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = tk.Entry(form, width=30)
            entry.grid(row=i, column=1, padx=5)
            self.entries[label] = entry

        ttk.Button(form, text="Register Student", command=self.register_student).grid(
            row=len(labels), column=0, columnspan=2, pady=10)

    def register_student(self):
        name = self.entries["Full Name"].get()
        address = self.entries["Address"].get()
        course = self.entries["Course"].get()
        level = self.entries["Level"].get()
        dob = self.entries["DOB"].get()
        username = self.entries["Username"].get()
        password = self.entries["Password"].get()

        if not all([name, username, password]):
            messagebox.showwarning("Error", "Name, username and password required.")
            return

        sid = self.db.add_student(name, address, course, level, dob)
        if self.db.create_user(username, password, "Student", sid):
            messagebox.showinfo("Success", f"Student '{name}' registered successfully!")
            for e in self.entries.values():
                e.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Username already exists.")

    # ------------------- MANAGE STUDENTS -------------------
    def manage_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Manage Students")

        cols = ("UserID", "Username", "Role", "ReferenceID", "IsActive")
        self.user_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c in cols:
            self.user_tree.heading(c, text=c)
            self.user_tree.column(c, width=150)
        self.user_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Reset Password", command=self.reset_password).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Suspend / Activate", command=self.toggle_active).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Delete Account", command=self.delete_user).grid(row=0, column=2, padx=5)

        ttk.Button(tab, text="Refresh List", command=self.load_users).pack()
        self.load_users()

    def load_users(self):
        self.user_tree.delete(*self.user_tree.get_children())
        for u in self.db.fetchall("SELECT * FROM Users WHERE Role='Student'"):
            self.user_tree.insert("", "end", values=(
                u["UserID"], u["Username"], u["Role"], u["ReferenceID"], "Active" if u["IsActive"] else "Suspended"))

    def reset_password(self):
        sel = self.user_tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a student to reset password.")
            return
        user_id = self.user_tree.item(sel)["values"][0]
        new_pass = "student123"
        self.db.execute("UPDATE Users SET PasswordHash=? WHERE UserID=?",
                        (self.db.hash_password(new_pass), user_id))
        messagebox.showinfo("Done", f"Password reset to: {new_pass}")

    def toggle_active(self):
        sel = self.user_tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a student to suspend/activate.")
            return
        user_id = self.user_tree.item(sel)["values"][0]
        current = self.db.fetchone("SELECT IsActive FROM Users WHERE UserID=?", (user_id,))
        new_status = 0 if current["IsActive"] == 1 else 1
        self.db.execute("UPDATE Users SET IsActive=? WHERE UserID=?",
                        (new_status, user_id))
        messagebox.showinfo("Updated", f"Account {'activated' if new_status else 'suspended'}.")
        self.load_users()

    def delete_user(self):
        sel = self.user_tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a student to delete.")
            return
        data = self.user_tree.item(sel)["values"]
        user_id, ref_id = data[0], data[3]
        if messagebox.askyesno("Confirm", "Delete this account permanently?"):
            self.db.execute("DELETE FROM Users WHERE UserID=?", (user_id,))
            self.db.execute("DELETE FROM Student WHERE StudentID=?", (ref_id,))
            self.load_users()
            messagebox.showinfo("Deleted", "Student account removed.")

    # ------------------- REPORTS -------------------
    def reports_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Reports")

        cols = ("BorrowID", "StudentID", "BookID", "BorrowDate", "DueDate", "ReturnDate", "Status")
        self.borrow_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c in cols:
            self.borrow_tree.heading(c, text=c)
            self.borrow_tree.column(c, width=120)
        self.borrow_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Refresh", command=self.load_borrowed_books).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=1, padx=5)

        self.load_borrowed_books()

    def load_borrowed_books(self):
        self.borrow_tree.delete(*self.borrow_tree.get_children())
        for r in self.db.fetchall("SELECT * FROM BorrowedBooks ORDER BY BorrowDate DESC"):
            self.borrow_tree.insert("", "end", values=(
                r["BorrowID"], r["StudentID"], r["BookID"], r["BorrowDate"], r["DueDate"], r["ReturnDate"], r["Status"]))

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file:
            return
        try:
            with open(file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([c for c in self.borrow_tree["columns"]])
                for row in self.borrow_tree.get_children():
                    writer.writerow(self.borrow_tree.item(row)["values"])
            messagebox.showinfo("Exported", f"Report successfully saved as {file}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export CSV:\n{e}")

    # ------------------- LEADERBOARD -------------------
    def leaderboard_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Leaderboard")

        tk.Label(tab, text="Top Performing Students",
                 font=("Segoe UI", 13, "bold")).pack(pady=10)

        cols = ("Rank", "Student Name", "Score", "Reading Streak")
        self.leader_tree = ttk.Treeview(tab, columns=cols, show="headings")
        for c in cols:
            self.leader_tree.heading(c, text=c)
            self.leader_tree.column(c, width=180)
        self.leader_tree.pack(expand=True, fill="both", padx=10, pady=10)

        ttk.Button(tab, text="Refresh Leaderboard", command=self.load_leaderboard).pack(pady=10)
        self.load_leaderboard()

    def load_leaderboard(self):
        self.leader_tree.delete(*self.leader_tree.get_children())
        students = self.db.fetchall("SELECT FullName, Score, ReadingStreak FROM Student ORDER BY Score DESC LIMIT 10")
        rank = 1
        for s in students:
            tag = ""
            if rank == 1: tag = "gold"
            elif rank == 2: tag = "silver"
            elif rank == 3: tag = "bronze"
            self.leader_tree.insert("", "end",
                values=(rank, s["FullName"], s["Score"], s["ReadingStreak"]), tags=(tag,))
            rank += 1
        self.leader_tree.tag_configure("gold", background="#fff7c2")
        self.leader_tree.tag_configure("silver", background="#e6e6e6")
        self.leader_tree.tag_configure("bronze", background="#f4d1a4")


if __name__ == "__main__":
    LibrarianDashboard(1)
