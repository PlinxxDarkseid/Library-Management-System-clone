-- ================================
-- LIBRARY MANAGEMENT & GAMIFICATION SCHEMA
-- ================================

-- Location table: shelf/section mapping
CREATE TABLE IF NOT EXISTS Location (
    LocationID INTEGER PRIMARY KEY AUTOINCREMENT,
    ShelfNumber TEXT,
    SectionName TEXT
);

-- Book table: basic book metadata and availability
CREATE TABLE IF NOT EXISTS Book (
    BookID INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT NOT NULL,
    Author TEXT NOT NULL,
    Category TEXT,
    LocationID INTEGER,
    AvailabilityStatus TEXT DEFAULT 'Available',
    FOREIGN KEY (LocationID) REFERENCES Location(LocationID)
);

-- Student table: core profile + gamification fields
CREATE TABLE IF NOT EXISTS Student (
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT NOT NULL,
    Address TEXT,
    Course TEXT,
    Level TEXT,
    DateOfBirth TEXT,
    Score INTEGER DEFAULT 100,
    ReadingStreak INTEGER DEFAULT 0
);

-- Librarian table: admin personnel
CREATE TABLE IF NOT EXISTS Librarian (
    LibrarianID INTEGER PRIMARY KEY AUTOINCREMENT,
    FullName TEXT NOT NULL,
    DateEmployed TEXT,
    Email TEXT
);

-- BorrowedBooks: tracks borrow/return and status
CREATE TABLE IF NOT EXISTS BorrowedBooks (
    BorrowID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    BookID INTEGER,
    LibrarianID INTEGER,
    BorrowDate TEXT,
    DueDate TEXT,
    ReturnDate TEXT,
    Status TEXT DEFAULT 'Borrowed',
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY (BookID) REFERENCES Book(BookID),
    FOREIGN KEY (LibrarianID) REFERENCES Librarian(LibrarianID)
);

-- ReadingHistory: logs reading sessions (not necessarily tied to borrowing)
CREATE TABLE IF NOT EXISTS ReadingHistory (
    ReadingID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER,
    BookID INTEGER,
    StartDate TEXT,
    EndDate TEXT,
    DurationMinutes INTEGER,
    Completed INTEGER DEFAULT 0,   -- 1 if the student finished the book/session
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY (BookID) REFERENCES Book(BookID)
);

-- Users: authentication table (links to Student or Librarian via ReferenceID)
CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    PasswordHash TEXT NOT NULL,
    Role TEXT NOT NULL,           -- 'Student' or 'Librarian'
    ReferenceID INTEGER           -- references StudentID or LibrarianID depending on Role
);
-- ALTER TABLE Users ADD COLUMN IsActive INTEGER DEFAULT 1;
