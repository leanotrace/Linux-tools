import os
import re # 정규표현식 모듈
import shutil  # 디렉터리 삭제를 위해 필요한 모듈
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
from tkinter import *
from tkinter import filedialog
from PIL import Image

root = Tk()
root.title("파일 삭제 프로그램")

root.geometry("1280x600")

# 삭제할 파일 목록
file_paths = []

# 파일 추가 함수 
def add_file():
    files = filedialog.askopenfilenames(title="파일을 선택하세요", \
    filetypes=(("모든 파일", "*"),),    
    initialdir=r"/root")

# *.*이라고 하면 확장자가 없는 리눅스 파일은 인식이 안되는 문제가 있음
    # 선택된 파일 확인
    if files:
        for file in files:
            list_file.insert(END, file)
            
            # 파일 경로 별도 저장(실행: 클릭 시 바로 삭제 위함)
            file_paths.append(file)
    else:
        print("파일이 선택되지 않음.")

def del_file():

    global file_paths
    
    if not file_paths:
        msgbox.showarning("경고", "삭제할 파일을 선택하세요")
        return
    
    # 파일 경로에 있는 모든 파일 삭제
    for file_path in file_paths:
        try:
            if os.path.isfile(file_path): #파일인 경우
                os.remove(file_path)
            elif os.path.isdir(file_path): #디렉터리인 경우
                shutil.rmtree(file_path) # 디렉터리와 그 안에 모든 내용 삭제
        except Exception as e:
            msgbox.showerror("에러", f"파일을 삭제할 수 없습니다: {file_path}\n{e}")
    
    # 리스트 박스에서 항목 제거 및 경로 리스트 초기화
    list_file.delete(0, END)
    file_paths = []
    msgbox.showinfo("알림", "선택된 파일이 삭제되었습니다.")

def filter_file():
    pattern = entry_filter.get()  # 입력창에서 패턴을 가져옴
    directory = entry_directory.get()
    file_type = cmb_file_type.get()
    
    if not pattern or not directory:
        msgbox.showwarning("경고", "필터와 디렉터리를 입력하세요")
        return 
    
    try:
        regex = re.compile(pattern)  # 정규표현식 패턴 컴파일
    except re.error as e:
        msgbox.showerror("에러", f"잘못된 정규표현식입니다: {e}")
        return
    
    # 필터 검색 시 기존 목록 제거
    list_file.delete(0, END)
    file_paths.clear()
    
    found_files = False # 매칭되는 파일이 있는지 확인하는 플래그
    
    # 사용자가 입력한 디렉터리에서 파일 검색
    for root_dir, dirs, files in os.walk(directory):
        if file_type.startswith("f"):  # 일반 파일만 검색
            files_to_search = files
        elif file_type.startswith("d"):  # 디렉터리만 검색
            files_to_search = dirs
        else:
            files_to_search = files + dirs  # 파일과 디렉터리 모두 검색
            
        for file_name in files_to_search:
            if regex.match(file_name):  # 패턴과 일치하는 파일 찾기
                full_path = os.path.join(root_dir, file_name)
                list_file.insert(END, full_path)  # 리스트 박스에 파일 추가
                file_paths.append(full_path)
                found_files = True
    # 매칭되는 파일이 없으면 경고 박스 표시
    if not found_files:
        msgbox.showwarning("경고", "매칭되는 파일이 없습니다.")

# 리스트에서 파일을 제거하는 함수
def remove_selected():
    selected_files = list_file.curselection()
    
    if not selected_files:
        msgbox.showwarning("경고", "제거할 파일을 선택하세요")
        return
    
    for index in reversed(selected_files):
        list_file.delete(index)
        del file_paths[index] # 파일 경로 목록에서도 제거
        
# 리스트에서 파일을 선택하는 함수
def file_selected():
    selected_files = list_file.curselection()

    if not selected_files:
        msgbox.showwarning("경고", "삭제할 파일을 선택하세요")
        return
    
    # 선택된 파일들을 실제로 삭제
    for index in reversed(selected_files):
        try:
            if os.path.isfile(file_paths[index]): #파일일 때
                os.remove(file_paths[index])
            elif os.path.isdir(file_paths[index]): # 디렉터리일 때
                shutil.rmtree(file_paths[index])
            
            list_file.delete(index) # 리스트에서 제거
            del file_paths[index]
        except Exception as e:
            msgbox.showerror("에러", f"파일을 삭제할 수 없습니다: {file_paths[index]}\n{e}")
            
    msgbox.showinfo("알림", "선택된 파일이 삭제되었습니다.")
    

# grid의 빈공간 조절
root.grid_rowconfigure(0, weight=1)  # 상단 공간 비율
root.grid_rowconfigure(1, weight=0)  # 버튼 프레임 비율 (고정)
root.grid_rowconfigure(2, weight=1)  # 리스트 박스 아래 공간 비율
root.grid_columnconfigure(0, weight=0)  # 좌측 공간 비율
root.grid_columnconfigure(1, weight=1)  # 중앙 공간 (버튼 및 리스트 박스)
root.grid_columnconfigure(2, weight=0)  # 우측 공간 비율

# "삭제할 목록" 버튼과 "실행" 버튼을 중앙에 배치
button_frame = Frame(root)
button_frame.grid(row=1, column=1, padx=5, pady=5, sticky="n")

# "삭제할 목록" 버튼
btn_fileremove = Button(button_frame, padx=5, pady=5, width=12, text="삭제할 파일 찾기", command=add_file)
btn_fileremove.pack(side="left", padx=10)

# "파일 목록 제거" 버튼
btn_remove_selected = Button(button_frame, padx=5, pady=5, width=12, text="목록에서 제거", command=remove_selected)
btn_remove_selected.pack(side="left", padx=10)

# "전체 삭제" 버튼
btn_delete_all = Button(button_frame, padx=5, pady=5, width=12, text="전체 제거", command=del_file)
btn_delete_all.pack(side="left", padx=10)

# "선택 제거" 버튼 (리스트에서 선택한 파일을 삭제)
btn_delete_selected  = Button(button_frame, padx=5, pady=5, width=12, text="선택 제거", command=file_selected)
btn_delete_selected.pack(side="left", padx=10)

# "자동 필터링" 버튼
btn_filter = Button(button_frame, padx=5, pady=5, width=12, text="필터링 검색", command=filter_file)
btn_filter.pack(side="left", padx=10)

# 필터 입력 창
entry_filter = Entry(button_frame, width=20)
entry_filter.pack(side="left", padx=10)

# 디렉터리 입력 창
entry_directory = Entry(button_frame, width=30)
entry_directory.pack(side="left", padx=10)
entry_directory.insert(0, "/")  # 기본값을 "/"로 설정

# 파일 타입 선택 콤보박스
opt_file_type = ["f (일반 파일)", "d (디렉터리)", "a (all)"]
cmb_file_type = ttk.Combobox(button_frame, state="readonly", values=opt_file_type, width=15)
cmb_file_type.current(0)  # 기본값을 f로 설정
cmb_file_type.pack(side="left", padx=10)

# 리스트 박스를 중앙 아래에 배치 (버튼 아래에 꽉 차도록)
list_frame = Frame(root)
list_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

list_file = Listbox(list_frame, selectmode="extended", height=15)
list_file.pack(fill="both", expand=True)

# 리스트 박스를 창 크기에 맞게 확장
root.grid_rowconfigure(2, weight=1)  # 리스트 박스 행의 비율 조정 (아래 공간 꽉 채움)
root.grid_columnconfigure(1, weight=1)  # 리스트 박스가 창의 전체 너비를 차지하도록 설정

root.resizable(True, True)
root.mainloop()
