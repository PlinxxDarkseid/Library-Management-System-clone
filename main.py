import tkinter as tk
from tkinter import messagebox
from database import Database
from student_dashboard import StudentDashboard
from librarian_dashboard import LibrarianDashboard

db = Database()

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        tk.Label(root, text="Library Management System", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Label(root, text="Username:").pack()
        self.username = tk.Entry(root, width=30)
        self.username.pack()

        tk.Label(root, text="Password:").pack()
        self.password = tk.Entry(root, show="*", width=30)
        self.password.pack()

        tk.Button(root, text="Login", width=15, command=self.login_user).pack(pady=15)

    def login_user(self):
        user = self.username.get().strip()
        pw = self.password.get().strip()
        if not user or not pw:
            messagebox.showwarning("Error", "Enter username and password")
            return

        record = db.verify_user(user, pw)
        if record:
            messagebox.showinfo("Success", f"Welcome {record['Role']}")
            self.root.destroy()
            if record["Role"].lower() == "student":
                open_student_dashboard(record["ReferenceID"])
            else:
                open_librarian_dashboard(record["ReferenceID"])
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")


def open_student_dashboard(student_id):
    StudentDashboard(student_id)


def open_librarian_dashboard(librarian_id):
    LibrarianDashboard(librarian_id)
    # win = tk.Tk()
    # win.title("Librarian Dashboard")
    # win.geometry("500x400")
    # tk.Label(win, text=f"Welcome Librarian #{librarian_id}", font=("Arial", 14, "bold")).pack(pady=40)
    # tk.Label(win, text="Librarian features will appear here.").pack()
    # tk.Button(win, text="Exit", command=win.destroy).pack(pady=20)
    # win.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
    db.close()
