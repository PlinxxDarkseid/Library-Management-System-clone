"""
database.py
Phase 2: CRUD Operations and Gamification Logic
-----------------------------------------------
Handles:
- Book, Student, Librarian CRUD
- Borrowing & Returning books
- Reading activity logging
- Automatic scoring & streak updates
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

DEFAULT_DB = "library.db"
SCHEMA_FILE = "schema.sql"


# ---------- Helper ----------
def hash_password(password: str) -> str:
    """Return SHA-256 hash of the provided password (hex)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------- Database Class ----------
class Database:
    def __init__(self, db_name: str = DEFAULT_DB, schema_file: str = SCHEMA_FILE):
        self.db_name = db_name
        self.schema_file = schema_file
        self.conn: sqlite3.Connection = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.initialize_db()

    # =====================================================
    # =============== INITIALIZATION =======================
    # =====================================================
    def initialize_db(self):
        if not os.path.exists(self.schema_file):
            raise FileNotFoundError(f"Schema file '{self.schema_file}' not found.")

        with open(self.schema_file, "r", encoding="utf-8") as f:
            sql_script = f.read()
        self.cursor.executescript(sql_script)
        self.conn.commit()

        # Create default librarian if Users is empty
        if self._users_count() == 0:
            self._create_default_admin()

        self.ensure_isactive_column()

    def _users_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) as cnt FROM Users")
        return self.cursor.fetchone()["cnt"]

    def _create_default_admin(self):
        print("No users found. Creating default admin...")
        self.cursor.execute(
            "INSERT INTO Librarian (FullName, DateEmployed, Email) VALUES (?, date('now'), ?)",
            ("Default Admin", "admin@example.com"),
        )
        librarian_id = self.cursor.lastrowid
        self.cursor.execute(
            "INSERT INTO Users (Username, PasswordHash, Role, ReferenceID) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "Librarian", librarian_id),
        )
        self.conn.commit()
        print("✅ Default admin created → username: admin | password: admin123")

    # =====================================================
    # =============== GENERIC HELPERS =====================
    # =====================================================
    def execute(self, query: str, params: Tuple = ()) -> None:
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

    def ensure_isactive_column(self):
        try:
            self.cursor.execute("ALTER TABLE Users ADD COLUMN IsActive INTEGER DEFAULT 1")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists


    # =====================================================
    # =============== AUTHENTICATION ======================
    # =====================================================
    def create_user(self, username: str, password: str, role: str, ref_id: Optional[int]) -> bool:
        try:
            self.cursor.execute(
                "INSERT INTO Users (Username, PasswordHash, Role, ReferenceID) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, ref_id),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username: str, password: str):
        row = self.fetchone("SELECT * FROM Users WHERE Username=?", (username,))
        if not row:
            return None
        if row["PasswordHash"] != hashlib.sha256(password.encode()).hexdigest():
            return None
        if row["IsActive"] == 0:
            raise Exception("Your account is suspended. Contact the librarian.")
        return row


    # =====================================================
    # =============== STUDENT MANAGEMENT ==================
    # =====================================================
    def add_student(self, full_name, address, course, level, dob) -> int:
        self.execute(
            "INSERT INTO Student (FullName, Address, Course, Level, DateOfBirth) VALUES (?, ?, ?, ?, ?)",
            (full_name, address, course, level, dob),
        )
        return self.cursor.lastrowid

    def get_student(self, student_id: int):
        return self.fetchone("SELECT * FROM Student WHERE StudentID=?", (student_id,))

    def update_student_score(self, student_id: int, delta: int):
        self.execute("UPDATE Student SET Score = Score + ? WHERE StudentID=?", (delta, student_id))

    def reset_streak(self, student_id: int):
        self.execute("UPDATE Student SET ReadingStreak = 0 WHERE StudentID=?", (student_id,))

    def increment_streak(self, student_id: int):
        self.execute("UPDATE Student SET ReadingStreak = ReadingStreak + 1 WHERE StudentID=?", (student_id,))

    # =====================================================
    # =============== BOOK MANAGEMENT =====================
    # =====================================================
    def add_book(self, title, author, category, location_id=None):
        self.execute(
            "INSERT INTO Book (Title, Author, Category, LocationID) VALUES (?, ?, ?, ?)",
            (title, author, category, location_id),
        )
        return self.cursor.lastrowid

    def update_book(self, book_id, title, author, category, status):
        self.execute(
            "UPDATE Book SET Title=?, Author=?, Category=?, AvailabilityStatus=? WHERE BookID=?",
            (title, author, category, status, book_id),
        )

    def delete_book(self, book_id):
        self.execute("DELETE FROM Book WHERE BookID=?", (book_id,))

    def search_books(self, keyword):
        key = f"%{keyword}%"
        return self.fetchall(
            "SELECT * FROM Book WHERE Title LIKE ? OR Author LIKE ? OR Category LIKE ?",
            (key, key, key),
        )

    # =====================================================
    # =============== BORROWING SYSTEM ====================
    # =====================================================
    def borrow_book(self, student_id: int, book_id: int, librarian_id: int, days_due: int = 7):
        """Student borrows a book; auto-updates availability and score."""
        borrow_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=days_due)).strftime("%Y-%m-%d")

        # Check availability
        book = self.fetchone("SELECT AvailabilityStatus FROM Book WHERE BookID=?", (book_id,))
        if not book or book["AvailabilityStatus"] != "Available":
            raise Exception("Book not available for borrowing.")

        # Insert record
        self.execute(
            "INSERT INTO BorrowedBooks (StudentID, BookID, LibrarianID, BorrowDate, DueDate, Status) VALUES (?, ?, ?, ?, ?, 'Borrowed')",
            (student_id, book_id, librarian_id, borrow_date, due_date),
        )
        # Update book status
        self.execute("UPDATE Book SET AvailabilityStatus='Borrowed' WHERE BookID=?", (book_id,))
        # Reward points
        self.update_student_score(student_id, +5)

    def return_book(self, borrow_id: int):
        """Mark book as returned and adjust score based on timeliness."""
        record = self.fetchone("SELECT * FROM BorrowedBooks WHERE BorrowID=?", (borrow_id,))
        if not record:
            raise Exception("Invalid borrow record.")

        return_date = datetime.now().strftime("%Y-%m-%d")
        due_date = datetime.strptime(record["DueDate"], "%Y-%m-%d").date()
        is_late = datetime.now().date() > due_date

        # Update BorrowedBooks record
        self.execute("UPDATE BorrowedBooks SET ReturnDate=?, Status='Returned' WHERE BorrowID=?", (return_date, borrow_id))
        # Make book available again
        self.execute("UPDATE Book SET AvailabilityStatus='Available' WHERE BookID=?", (record["BookID"],))
        # Adjust score
        if is_late:
            self.update_student_score(record["StudentID"], -10)
        else:
            self.update_student_score(record["StudentID"], +10)

    # =====================================================
    # =============== READING HISTORY =====================
    # =====================================================
    def start_reading(self, student_id: int, book_id: int):
        """Log the start of a reading session."""
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            "INSERT INTO ReadingHistory (StudentID, BookID, StartDate) VALUES (?, ?, ?)",
            (student_id, book_id, start_date),
        )
        self.update_student_score(student_id, +2)  # reward for starting

    def finish_reading(self, reading_id: int):
        """Mark a reading session complete and award points."""
        end_time = datetime.now()
        session = self.fetchone("SELECT * FROM ReadingHistory WHERE ReadingID=?", (reading_id,))
        if not session or session["EndDate"]:
            return

        start_time = datetime.strptime(session["StartDate"], "%Y-%m-%d %H:%M:%S")
        duration = int((end_time - start_time).total_seconds() // 60)

        self.execute(
            "UPDATE ReadingHistory SET EndDate=?, DurationMinutes=?, Completed=1 WHERE ReadingID=?",
            (end_time.strftime("%Y-%m-%d %H:%M:%S"), duration, reading_id),
        )

        self.update_student_score(session["StudentID"], +10)
        self._update_reading_streak(session["StudentID"])

    def _update_reading_streak(self, student_id: int):
        """Check last reading date and update streak."""
        last_read = self.fetchone(
            "SELECT EndDate FROM ReadingHistory WHERE StudentID=? AND Completed=1 ORDER BY EndDate DESC LIMIT 1",
            (student_id,),
        )
        if not last_read or not last_read["EndDate"]:
            self.reset_streak(student_id)
            return

        last_date = datetime.strptime(last_read["EndDate"].split(" ")[0], "%Y-%m-%d").date()
        today = datetime.now().date()

        if (today - last_date).days == 1:
            self.increment_streak(student_id)
            self.update_student_score(student_id, +5)
        elif (today - last_date).days > 1:
            self.reset_streak(student_id)
            self.update_student_score(student_id, -5)

    def get_reading_history(self, student_id: int):
        return self.fetchall(
            "SELECT rh.*, b.Title FROM ReadingHistory rh JOIN Book b ON rh.BookID=b.BookID WHERE rh.StudentID=? ORDER BY rh.StartDate DESC",
            (student_id,),
        )

    # =====================================================
    # =============== REPORTS & LEADERBOARDS ==============
    # =====================================================
    def list_top_readers(self, limit: int = 10):
        return self.fetchall(
            "SELECT StudentID, FullName, Score, ReadingStreak FROM Student ORDER BY Score DESC LIMIT ?",
            (limit,),
        )


# --------------- TEST RUN ---------------
if __name__ == "__main__":
    db = Database()
    print("✅ Database ready and CRUD operations loaded.")
    print("Top readers:", [dict(r) for r in db.list_top_readers()])
    db.close()
