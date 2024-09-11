import tkinter as tk
from tkinter import messagebox
import psycopg2
import re

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="library_system",
            user="wsjang",
            password="12345",
            host="localhost"            
        )
        return conn
    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return None

# 유저 인증 함수
def authenticate_user(username, password):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        else:
            return None

# 책(Book) 클래스
class Book:
    def __init__(self, title, author, isbn, is_rented=False, rented_by=None):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.is_rented = is_rented # 책의 대여 상태 (대여 가능 여부)
        self.rented_by = rented_by

    def rent(self, user_name):
        if not self.is_rented:
            self.is_rented = True
            self.rented_by = user_name
            return f"'{self.title}' 책이 {user_name}님께 대여되었습니다."
        else:
            return f"'{self.title}' 책은 이미 {self.rented_by}님이 대여 중입니다."

    def return_book(self, user_name):
        if self.is_rented and self.rented_by == user_name:
            self.is_rented = False
            self.rented_by = None
            return f"'{self.title}' 책이 반납되었습니다."
        elif self.is_rented:
            return f"'{self.title}' 책은 {self.rented_by}님이 대여 중입니다."
        else:
            return f"'{self.title}' 책은 이미 반납된 상태입니다."

def clean_title(title):
    """책 제목에서 괄호로 구분된 추가 정보를 제거하는 함수"""
    return re.sub(r"\(.*?\)", "", title).strip()

# 도서관(Library) 클래스
class Library:
    def __init__(self):
        self.conn = connect_db()
        self.books = self.load_books_from_db()  # 데이터베이스에서 책 목록 로드

    def load_books_from_db(self):
        """DB에서 책 목록 로드"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, author, isbn, is_rented, rented_by FROM books")
        rows = cursor.fetchall()
        books = [Book(title, author, isbn, is_rented, rented_by) for (title, author, isbn, is_rented, rented_by) in rows]
        return books

    def save_book_to_db(self, book):
        """책의 상태를 DB에 저장"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE books 
            SET is_rented = %s, rented_by = %s 
            WHERE isbn = %s
        """, (book.is_rented, book.rented_by, book.isbn))
        self.conn.commit()
        
    def add_book(self, book):
        self.books.append(book)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, isbn, is_rented, rented_by) 
            VALUES (%s, %s, %s, %s, %s)
        """, (book.title, book.author, book.isbn, book.is_rented, book.rented_by))
        self.conn.commit()
        
    def remove_book(self, title):
        """책을 도서관과 DB에서 제거"""
        for book in self.books:
            if clean_title(book.title) == clean_title(title):
                self.books.remove(book)
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM books WHERE isbn = %s", (book.isbn,))
                self.conn.commit()
                return f"'{title}' 책이 도서관에서 제거되었습니다."
        return f"'{title}' 책을 찾을 수 없습니다."

    def rent_book(self, title, user_name):
        """책 대여"""
        for book in self.books:
            if clean_title(book.title) == clean_title(title):
                result = book.rent(user_name)
                self.save_book_to_db(book)  # 책 상태를 DB에 저장
                return result
        return f"'{title}' 책은 도서관에 없습니다."
    
    def return_book(self, title, user_name):
        """책 반납"""
        for book in self.books:
            if clean_title(book.title) == clean_title(title):
                result = book.return_book(user_name)
                self.save_book_to_db(book)  # 책 상태를 DB에 저장
                return result
        return f"'{title}' 책은 도서관에 없습니다."
    
    def get_books(self):
        return [f"{book.title} (대여 중: {book.rented_by})" if book.is_rented else f"{book.title} (대여 가능)" for book in self.books]

    def update_books(self):
        # DB에서 책 목록을 다시 로드하여 최신 상태로 갱신
        self.books = self.load_books_from_db()

    def get_borrowed_books_by_user(self, user_name):
        """특정 유저가 대여한 책 목록을 반환"""
        return [book.title for book in self.books if book.is_rented and book.rented_by == user_name]


# 리스트 컴프리핸션 (리스트 books의 각 책을 순서대로 꺼내와 리스트형태로 리턴 ["책1", "책2"] = iterable)
# 이처럼 반환된 리스트 형태는 iterable 객체이기 때문에, update_books_listbox 메서드 내에서 for문에 사용 가능

##################### 비즈니스 로직

# GUI 클래스
class LibraryGUI:
    def __init__(self, root, user_name):
        self.root = root          # 윈도우 창 객체 하나를 생성한다고 생각
        self.root.title(f"도서 대여 시스템 - {user_name}님 환영합니다!")
        self.library = Library()
        self.user_name = user_name
        
        self.borrowed_books = self.library.get_borrowed_books_by_user(user_name)  # 로그인 시, 해당 유저가 대여한 책 불러오기

        # GUI 위젯들 생성
        self.create_widgets()
        
        # 대여한 책 목록을 업데이트
        self.update_borrowed_books_listbox()
        
        # 5초마다 책 목록 갱신
        self.update_books_periodically()

    def create_widgets(self):
        # 도서관의 책 목록 표시
        self.books_listbox = tk.Listbox(self.root, height=8, width=50, selectmode=tk.SINGLE)
        self.books_listbox.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
        self.update_books_listbox()
        
        # 책 제목, 저자, ISBN 입력 필드
        tk.Label(self.root, text="책 제목:").grid(row=1, column=0, padx=3, pady=5, sticky="w")
        self.title_entry = tk.Entry(self.root, width=10)
        self.title_entry.grid(row=1, column=0, padx=3, pady=5)

        tk.Label(self.root, text="저자:").grid(row=1, column=1, padx=3, pady=5, sticky="w")
        self.author_entry = tk.Entry(self.root, width=10)
        self.author_entry.grid(row=1, column=1, padx=3, pady=5)

        tk.Label(self.root, text="ISBN:").grid(row=1, column=1, padx=3, pady=5, sticky="e")
        self.isbn_entry = tk.Entry(self.root, width=10)
        self.isbn_entry.grid(row=1, column=2, padx=3, pady=5)       
        
        # 책 추가 버튼
        self.add_button = tk.Button(self.root, text="책 추가", command=self.add_book, width=9)
        self.add_button.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        # 책 제거 버튼
        self.remove_button = tk.Button(self.root, text="책 제거", command=self.remove_book, width=9)
        self.remove_button.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        
        # 대여 버튼
        self.rent_button = tk.Button(self.root, text="대여", command=self.rent_book, width=9)
        self.rent_button.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # 반납 버튼
        self.return_button = tk.Button(self.root, text="반납", command=self.return_book, width=9)
        self.return_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

        # 대여한 책 목록 표시
        self.borrowed_books_label = tk.Label(self.root, text="대여한 책 목록:")
        self.borrowed_books_label.grid(row=5, column=0, padx=5, pady=10, sticky="w") # sticky=w는 서쪽(west)으로 위젯 정렬

        self.borrowed_books_listbox = tk.Listbox(self.root, height=8, width=50, selectmode=tk.SINGLE)
        self.borrowed_books_listbox.grid(row=6, column=0, padx=10, pady=5, columnspan=2)

    def update_books_listbox(self):
        """도서관의 책 목록을 업데이트"""
        self.books_listbox.delete(0, tk.END)           
        for book in self.library.get_books(): # 도서 목록을 가져와 listbox에 표시하는 부분
            self.books_listbox.insert(tk.END, book) 
# 도서 목록이 변경(대여 또는 반납)될 때마다 리스트박스의 상태를 초기화하고 다시 채워 넣는 작업을 하는 것.ㄴㄴ

    def update_books_periodically(self):
        """주기적으로 책 목록을 업데이트"""
        self.library.update_books()  # DB에서 책 목록 갱신
        self.update_books_listbox()
        self.root.after(5000, self.update_books_periodically)  # 5초마다 갱신
        
    def update_borrowed_books_listbox(self):
        """대여한 책 목록을 업데이트"""
        self.borrowed_books_listbox.delete(0, tk.END)
        for book in self.borrowed_books:
            self.borrowed_books_listbox.insert(tk.END, book)
            
    def add_book(self):
        """새 책을 도서관에 추가하는 메서드"""
        title = self.title_entry.get()
        author = self.author_entry.get()
        isbn = self.isbn_entry.get()

        if title and author and isbn:
            # 중복 검사
            for book in self.library.books:
                if clean_title(book.title) == clean_title(title) or book.isbn == isbn:
                    messagebox.showwarning("경고", "이미 존재하는 책 제목 또는 ISBN입니다.")
                    return

            new_book = Book(title, author, isbn)
            self.library.add_book(new_book)
            self.update_books_listbox()
            messagebox.showinfo("책 추가", f"'{title}' 책이 도서관에 추가되었습니다.")

            # 입력 필드 초기화
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.isbn_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("경고", "모든 필드를 입력하세요.")
            
    def remove_book(self):
        """선택한 책을 도서관에서 제거"""
        selected_idx = self.books_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("경고", "제거할 책을 선택하세요.")
            return
        title = clean_title(self.books_listbox.get(selected_idx).split(" (")[0])
        result = self.library.remove_book(title)
        messagebox.showinfo("책 제거", result)
        self.update_books_listbox() 
        
    def rent_book(self):
        """책 대여 메서드"""
        selected_idx = self.books_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("경고", "대여할 책을 선택하세요.")
            return

        title = clean_title(self.books_listbox.get(selected_idx).split(" (")[0])
        result = self.library.rent_book(title, self.user_name)

        if "대여되었습니다" in result:
            self.borrowed_books.append(title)
            self.update_borrowed_books_listbox()

        messagebox.showinfo("대여 결과", result)
        self.update_books_listbox()


    def return_book(self):
        selected_idx = self.borrowed_books_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("경고", "반납할 책을 선택하세요.")
            return

        title_with_info = self.borrowed_books_listbox.get(selected_idx)
        title = clean_title(title_with_info)  # 제목에서 괄호 제거 후 비교

        # borrowed_books 리스트에서 책이 존재하는지 확인 후 제거
        if title in self.borrowed_books:
            result = self.library.return_book(title, self.user_name)
            if "반납되었습니다" in result:
                self.borrowed_books.remove(title)
                self.update_borrowed_books_listbox()
            messagebox.showinfo("반납 결과", result)
            self.update_books_listbox()
        else:
            messagebox.showerror("오류", f"'{title}' 책은 대여한 목록에 없습니다.")
        
# 로그인 창 클래스
class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("도서 대여 시스템 로그인")
        
        # 창 크기 설정 (너비 x 높이)
        window_width = 300
        window_height = 150
        
        # 화면 너비와 높이를 가져옴
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 창이 화면 중앙에 위치하도록 좌표 계산
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        
        # geometry() 메서드를 사용해 창의 크기 및 위치 설정
        self.root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        tk.Label(self.root, text="유저명:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="비밀번호:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        self.login_button = tk.Button(self.root, text="로그인", command=self.login)
        self.login_button.grid(row=2, column=1, padx=5, pady=5)
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = authenticate_user(username, password)

        if user:
            messagebox.showinfo("로그인 성공", f"{user}님 환영합니다!")
            self.root.destroy()
            main_window = tk.Tk()
            LibraryGUI(main_window, user)
            main_window.mainloop()
        else:
            messagebox.showerror("로그인 실패", "유저명 또는 비밀번호가 잘못되었습니다.")


# Tkinter 메인 루프
if __name__ == "__main__":
    root = tk.Tk()
    login_gui = LoginGUI(root)
    root.mainloop()
