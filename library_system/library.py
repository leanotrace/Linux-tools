import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from tkinter import PhotoImage
from tkinter import messagebox
import psycopg2
import re
import os
from collections import deque

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
    conn = connect_db()      # 연결 성공 시 연결 객체 반환
    if conn:
        cursor = conn.cursor() # 성공적으로 연결됬다면, SQL쿼리를 보낼 수 있는 커서 생성
        cursor.execute("SELECT username FROM users WHERE username=%s AND password=%s", (username, password))
        # 입력받은 user, password를 검색
        result = cursor.fetchone() # 쿼리 결과 첫번째 일치하는 결과를 튜플 형태로 반환 ('wsjang', '12345)
        conn.close()
        if result:
            return result[0] # 유저명 리턴
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
        self.reviews = deque(maxlen=3) # 리뷰를 최대 3개까지만 저장
    
    def add_review(self, rating, review):
        self.reviews.append((rating, review))

    def get_reviews(self):
        return list(self.reviews)

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
    """책 제목에서 괄호 정보를 제거하여, 기본적인 책 제목(ex 박찬호의 사랑꾼이 되는 비결)만 남기는 함수 """
    # \(.*?\)는 ()사이에 있는 모든 내용을 매칭.
    return re.sub(r"\(.*?\)", "", title).strip()

# 도서관(Library) 클래스
class Library:
    def __init__(self):
        self.conn = connect_db()
        self.books = self.load_books_from_db()  # 데이터베이스에서 책 목록 로드

    def load_books_from_db(self):
        # load_books_from_db 메서드 수정 (별도의 리뷰 쿼리를 추가)

        cursor = self.conn.cursor()
        cursor.execute("SELECT title, author, isbn, is_rented, rented_by FROM books")
        rows = cursor.fetchall()
        
        books = {}
        for row in rows:
            title, author, isbn, is_rented, rented_by = row
            books[isbn] = Book(title, author, isbn, is_rented, rented_by)

        #각 책의 리뷰를 별도로 가져옴
        cursor.execute("SELECT isbn, rating, review FROM reviews ORDER BY id ASC")
        reviews = cursor.fetchall()
        
        for isbn, rating, review in reviews:
            if isbn in books:
                books[isbn].add_review(rating, review)
        
        return list(books.values())

        # books, reviews 테이블 LEFT JOIN. books = b. reviews = r.
        # 두 테이블은 ISBN(b.isbn = r.isbn) 을 기준으로 연결된다.
        # LEFT JOIN은 우선 왼쪽 테이블 books의 모든 행을 가져온다.
        # 그리고 reviews 테이블에 같은 값(isbn)이 있으면, 그 리뷰와 평점을 가져온다. (없으면 NULL로 채워짐)
                
        #ex 하나의 튜플은 ("Title", "Author", "12345", "t" 이런 식으로 구성) 이게 리스트에선 한 요소.
        # books 딕셔너리 구조
        #     {
        # "12345": Book(title="Book A", author="Author A", isbn="12345", is_rented=True, rented_by="User1", reviews=[(5, "Excellent!"), (4, "Good!")]),
        # "67890": Book(title="Book B", author="Author B", isbn="67890", is_rented=False, rented_by=None, reviews=[])
                     
        # books = [Book(title, author, isbn, is_rented, rented_by) for (title, author, isbn, is_rented, rented_by) in rows]
        # # books라는 리스트 생성. DB에서 가져온 정보를 기반으로 Book 객체를 생성하고, 리스트로 저장
        #return books # 생성한 Book 객체 리스트 반환
  
    def save_book_to_db(self, book):
        """책의 상태를 DB에 저장"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE books 
            SET is_rented = %s, rented_by = %s 
            WHERE isbn = %s
        """, (book.is_rented, book.rented_by, book.isbn))
        self.conn.commit() # update 구문 호출 후 commit 해야 실제 db에 반영
        
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
                # 제거하려는책(title)과 순수 책제목만 비교하여. 있는지 비교. 찾은 책은 books.remove로 리스트에서 제거
                self.books.remove(book)
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM books WHERE isbn = %s", (book.isbn,)) # isbn을 키로해서 제거
                self.conn.commit()
                return f"'{title}' 책이 도서관에서 제거되었습니다."
        return f"'{title}' 책을 찾을 수 없습니다."

    def rent_book(self, title, user_name):
        """책 대여"""
        for book in self.books:
            if clean_title(book.title) == clean_title(title):
                result = book.rent(user_name) # 대여하려는 책이 있다면, 대여 성공 메시지를 반환할 것.
                self.save_book_to_db(book)  # 책A 상태를 DB에 저장
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
    
    # 1. for book in ~ self.books 리스트에 있는 객체(book) 순회
    # 2. if book.is_rented가 true면, 대여 중: ~ 메시지 출력.
    # 3. else ~~~ 대여 가능한상태(false)면 {book.title} (대여 가능) 출력
    # 즉, get_books 함수는 ["파이썬 프로그래밍 (대여 중: 홍길동), "자바 프로그래밍 (대여 가능)"] 과 같은 리스트를 반환한다.

    def get_book_info(self, title):
        
        for book in self.books:
            if clean_title(book.title) == clean_title(title):
                return book
        return None

    def update_books(self):
        # DB에서 책 목록을 다시 로드하여 최신 상태로 갱신
        self.books = self.load_books_from_db()

    def get_borrowed_books_by_user(self, user_name):
        """특정 유저가 대여한 책 목록을 반환"""
        return [book.title for book in self.books if book.is_rented and book.rented_by == user_name]

    def add_review_to_book(self, isbn, review, rating):
        cursor = self.conn.cursor()
        
        # 해당 ISBN의 리뷰 개수를 확인
        cursor.execute("""
            SELECT id FROM reviews WHERE isbn = %s ORDER BY id ASC
        """, (isbn,))
        reviews = cursor.fetchall()

        if len(reviews) >= 3:
        # 리뷰가 3개 이상이면 가장 오래된 리뷰 삭제
            oldest_review_id = reviews[0][0]
            cursor.execute("DELETE FROM reviews WHERE id = %s", (oldest_review_id,))
        
        # 새로운 리뷰 추가
        cursor.execute("""
            INSERT INTO reviews (isbn, review, rating)
            VALUES (%s, %s, %s)
            """, (isbn,review,rating))
        self.conn.commit()
        
        # 메모리 상의 책 객체에도 리뷰를 추가
        book = self.get_book_info_by_isbn(isbn)
        if book:
            book.add_review(rating, review)

    # 책을 isbn으로 찾는 메서드 예시
    def get_book_info_by_isbn(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None            


# 리스트 컴프리핸션 (리스트 books의 각 책을 순서대로 꺼내와 리스트형태로 리턴 ["책1", "책2"] = iterable)
# 이처럼 반환된 리스트 형태는 iterable 객체이기 때문에, update_books_listbox 메서드 내에서 for문에 사용 가능

##################### 비즈니스 로직

# GUI 클래스
class LibraryGUI:
    def __init__(self, root, user_name):
        self.root = root          # 윈도우 창 객체 하나를 생성한다고 생각
        self.root.title(f"도서 대여 시스템 - {user_name}님 환영합니다!")
        self.library = Library()  # 라이브러리 객체 생성 (대여, 반납 등 비즈니스로직 구현)
        self.user_name = user_name
        
        self.borrowed_books = self.library.get_borrowed_books_by_user(user_name)  
        # 로그인 시, 해당 유저가 대여한 책을 별도로 저장.

        # GUI 위젯들 생성
        self.create_widgets()
        
        # 대여한 책을 리스트 박스에 표시하는 함수 
        self.update_borrowed_books_listbox()
        
        # 5초마다 책 목록 갱신
        self.update_books_periodically()

    def create_widgets(self):
        
        self.root.geometry("580x600")
        
        # 커스텀 폰트 정의
        listbox_font = tkFont.Font(family="Arial", size=11)  # 글씨 크기 설정
        
        # 기본 배경색 설정
        self.root.configure(bg="#F4F1DE")  # 크림색 도서관 느낌
    
        # 이미지 로드
        add_icon = PhotoImage(file="/root/book-icon.png")
    
        # 도서관의 책 목록 표시 (스크롤바 추가)
        self.books_listbox = tk.Listbox(self.root, height=8, width=50, selectmode=tk.SINGLE, font=listbox_font, \
            bg="#F0F0F0", fg="#000000") # bg=배경색, fg=글씨 색.
        self.books_scrollbar = tk.Scrollbar(self.root, orient="vertical")  # 스크롤바 추가
        self.books_listbox.config(yscrollcommand=self.books_scrollbar.set)
        self.books_scrollbar.config(command=self.books_listbox.yview)
        
        # 그리드에 배치
        self.books_listbox.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky="nsew")
        self.books_scrollbar.grid(row=0, column=2, sticky='nsw')  # 스크롤바 배치

        self.update_books_listbox()
        
        # 책 제목, 저자, ISBN 입력 필드
        tk.Label(self.root, text="책 제목:").grid(row=1, column=0, padx=3, pady=5, sticky="w")
        self.title_entry = tk.Entry(self.root, width=10)
        self.title_entry.grid(row=1, column=0, padx=3, pady=5, sticky="e")

        tk.Label(self.root, text="저자:").grid(row=1, column=1, padx=1, pady=5)
        self.author_entry = tk.Entry(self.root, width=7)
        self.author_entry.grid(row=1, column=1, padx=45, pady=5, sticky="e")

        tk.Label(self.root, text="ISBN:").grid(row=1, column=2, padx=3, pady=5, sticky="w")
        self.isbn_entry = tk.Entry(self.root, width=7)
        self.isbn_entry.grid(row=1, column=2, padx=3, pady=5, sticky="e")       
        
        # 책 추가 버튼
        self.add_button = tk.Button(self.root, text="책 추가", image=add_icon, compound="left", command=self.add_book, width=100)
        self.add_button.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.add_button.image = add_icon
        
        # 책 제거 버튼
        self.remove_button = tk.Button(self.root, text="책 제거", command=self.remove_book, width=6)
        self.remove_button.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # 대여 버튼
        self.rent_button = tk.Button(self.root, text="대여", command=self.rent_book, width=6)
        self.rent_button.grid(row=3, column=1, padx=5, pady=5)

        # 반납 버튼
        self.return_button = tk.Button(self.root, text="반납", command=self.return_book, width=6)
        self.return_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")
        
        # 책 정보 버튼
        self.bookinfo_button = tk.Button(self.root, text="책 정보", command=self.show_book_info, width=6)
        self.bookinfo_button.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        
        # 리뷰 입력 필드
        tk.Label(self.root, text="한줄 리뷰 작성:").grid(row=8, column=0, padx=3, pady=5, sticky="w")
        self.review_entry = tk.Text(self.root, width=30, height=5)
        self.review_entry.grid(row=8, column=1, padx=3, pady=5, sticky="e")
        
        # 평점 선택 필드 (1~5점)
        tk.Label(self.root, text="평점:").grid(row=9, column=0, padx=3, pady=5, sticky="w")
        self.rating_var = tk.StringVar(self.root)
        self.rating_var.set("5")
        self.rating_menu = tk.OptionMenu(self.root, self.rating_var, "1", "2", "3", "4", "5")
        self.rating_menu.grid(row=9, column=0, padx=3, pady=5)

        # 리뷰 제출 버튼
        self.submit_review_button = tk.Button(self.root, text="리뷰 제출", command=self.submit_review, width=10)
        self.submit_review_button.grid(row=8, column=2, padx=5, pady=5)

        # 대여한 책 목록 표시
        self.borrowed_books_label = tk.Label(self.root, text="대여한 책 목록:")
        self.borrowed_books_label.grid(row=5, column=0, padx=5, pady=10, sticky="w") # sticky=w는 서쪽(west)으로 위젯 정렬

        self.borrowed_books_listbox = tk.Listbox(self.root, height=8, width=50, selectmode=tk.SINGLE)
        self.borrowed_books_listbox.grid(row=6, column=0, padx=10, pady=5, columnspan=2)

    def update_books_listbox(self):
        """도서관의 책 목록을 업데이트"""
        self.books_listbox.delete(0, tk.END)           
        for book in self.library.get_books(): 
            self.books_listbox.insert(tk.END, book) 
            # 도서 목록을 가져와 listbox에 표시하는 부분
            # 도서 목록이 변경(대여 또는 반납)될 때마다 리스트박스 상태를 초기화하고 다시 채워 넣는 작업을 함

    def update_books_periodically(self):
        """주기적으로 책 목록을 업데이트"""
        self.library.update_books()  # DB에서 책 목록 갱신
        self.update_books_listbox()
        self.root.after(20000, self.update_books_periodically)  # 20초마다 특정 함수 호출 (재귀 호출하여 책 목록을 지속적 갱신)
        
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
    
    def show_book_info(self):
        """선택한 책의 상세 정보를 메시지 박스로 출력"""
        selected_idx = self.books_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("경고", "책을 선택하세요.")
            return

        title_with_info = self.books_listbox.get(selected_idx)
        title = clean_title(title_with_info)
        
        for book in self.library.books:
            if clean_title(book.title) == title:
                
                # 리뷰 표시 전 리뷰 리스트 초기화
                reviews_info = ""
                
                # 다시 가져옴               
                reviews_info = "\n\n".join([f"평점: {r[0]} \n리뷰: {r[1]}" for r in book.reviews])
                
                messagebox.showinfo("책 정보", f"제목: {book.title}\n저자: {book.author}\nISBN: {book.isbn}\n"
                                            f"대여 상태: {'대여 중' if book.is_rented else '대여 가능'}\n"
                                            f"\n[리뷰 및 평점]:\n{reviews_info if reviews_info else '없음'}")
                return
               
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
        title = title_with_info
 
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

    def submit_review(self):
        selected_idx = self.borrowed_books_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning("경고", "리뷰를 작성할 책을 선택하세요.")
            return

        title = clean_title(self.borrowed_books_listbox.get(selected_idx).split(" (")[0])
        review = self.review_entry.get("1.0", tk.END).strip()
        rating = self.rating_var.get()
        
        if not review:
            messagebox.showwarning("경고", "리뷰를 입력하세요.")
            return
        
        # 리뷰를 책 객체와 DB에 저장
        book = self.library.get_book_info(title)
        if book:
            # 책 객체에 리뷰 추가 (최대 3개)
            book.add_review(rating, review)
            
            # DB에 리뷰를 저장 (DB 저장 후, 책 객체에도 추가)
            self.library.add_review_to_book(book.isbn, review, rating)
            
            messagebox.showinfo("리뷰 추가", f"'{book.title}'에 대한 리뷰가 추가되었습니다.")
            self.review_entry.delete("1.0", tk.END)  # 입력 필드 초기화
        else:
            messagebox.showerror("오류", "책을 찾을 수 없습니다.")
        
        
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
        
        # 사용자명 및 비밀번호 필드
        tk.Label(self.root, text="유저명:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="비밀번호:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # 자동 로그인 체크박스
        self.auto_login_var = tk.BooleanVar()
        self.auto_login_checkbox = tk.Checkbutton(self.root, text="자동 로그인", variable=self.auto_login_var)  # 수정된 부분
        self.auto_login_checkbox.grid(row=2, column=0, padx=5, pady=5)
        
        # 로그인
        self.login_button = tk.Button(self.root, text="로그인", command=self.login)
        self.login_button.grid(row=2, column=1, padx=5, pady=5)
        
        # 자동 로그인 파일 읽기
        self.load_login_info()
        
    def load_login_info(self):
        """저장된 로그인 정보가 있으면 입력 필드에 자동 입력 및 체크박스 상태 유지"""
        if os.path.exists("/root/login_info.txt"):
            with open("/root/login_info.txt", "r") as file:
                lines = file.readlines()
                if len(lines) >= 3:
                    self.username_entry.insert(0, lines[0].strip())
                    self.password_entry.insert(0, lines[1].strip())
                    # 체크박스 상태 불러오기
                    self.auto_login_var.set(True if lines[2].strip() == "1" else False)
    
    def save_login_info(self):
        """자동 로그인 정보 저장 (체크박스 상태도 저장)"""
        print("test")

        with open("/root/login_info.txt", "w") as file:
            file.write(self.username_entry.get() + "\n")
            file.write(self.password_entry.get() + "\n")
            # 체크박스 상태를 저장 (1: 체크됨, 0: 체크 안 됨)
            file.write("1\n" if self.auto_login_var.get() else "0\n")
            
    def login(self):
        """로그인 시 자동 로그인 여부 확인 및 로그인 처리"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = authenticate_user(username, password)  # 유저명 리턴

        if user:
            if self.auto_login_var.get():
                self.save_login_info()  # 자동 로그인 정보 저장
            else:
                if os.path.exists("/root/login_info.txt"):
                    os.remove("/root/login_info.txt")  # 자동 로그인 해제 시 파일 삭제

            messagebox.showinfo("로그인 성공", f"{user}님 환영합니다!")
            self.root.destroy()  # 로그인창 파괴
            main_window = tk.Tk()  # 새로운 window 생성
            LibraryGUI(main_window, user)
            main_window.mainloop()
        else:
            messagebox.showerror("로그인 실패", "유저명 또는 비밀번호가 잘못되었습니다.")
            
# Tkinter 메인 루프
if __name__ == "__main__":
    root = tk.Tk()
    login_gui = LoginGUI(root)
    root.mainloop()
