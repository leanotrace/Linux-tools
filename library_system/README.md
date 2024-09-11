# LibrarySystem

## Description 
"LibrarySystem" is a Python-based application designed for book rental and management. This program integrates with a PostgreSQL database to provide functions such as borrowing, returning, adding, and removing books, while also managing each user's rental history through user authentication.

The system offers an intuitive GUI, allowing users to easily track the rental status of books and manage their rental records in real-time. Additionally, it ensures efficient library management by using the database to handle book inventories and prevent duplicate entries.


## Key Features
1. Book Borrowing and Returning: After user authentication, users can borrow and return books. Books that are currently borrowed cannot be rented by others until they are returned.

2. Adding and Removing Books: Administrators can add new books or remove existing ones. The system checks for duplicate entries by verifying the book's title and ISBN before adding it to the library.

3. Real-Time Book Status Updates: The system syncs with the database every 5 seconds to ensure that the book list is up-to-date. This feature allows other users to see the latest status of borrowed/returned books.

4. User-Specific Rental History: Each user can view their own rental history, which is updated in real-time based on the user's borrowing and returning actions.

5. Search Functionality: Users can search for books by title or ISBN, and filter to display only available books.

# Requirements
- Python 3.x later
- PostgreSQL DB

## Installation

1. Clone or download the source code:
```bash
git clone https://github.com/yourusername/LibrarySystem.git

2. Install the required Python packages:
```bash
pip install -r requirements.txt

3. Set up the PostgreSQL database and create the necessary tables:

```bash
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    is_rented BOOLEAN DEFAULT FALSE,
    rented_by VARCHAR(255)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

4. Run the program:
```bash
python3 library.py
