import os
import fnmatch

# def find_files(directory, pattern):
#     if not os.path.isdir(directory):
#         print(f"Error: {directory} is not a valid")
#         return
    
#     for root, dirs, files in os.walk(directory):
#         for filename in fnmatch.filter(files, pattern):
#             print(os.path.join(root, filename))


# # 사용자로부터 디렉터리 경로와 파일 패턴 입력받기
# directory_to_search = input("Enter the dir to search: ")
# file_pattern = input("Enter the file pattern: ")

# # 파일 검색 함수 호출
# find_files(directory_to_search, file_pattern)


import os
import fnmatch

def reverse_string(s: str) -> str:
    return s[::-1]

def find_files(directory, pattern):
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
    
    for root, dirs, files in os.walk(directory):
        for filename in fnmatch.filter(files, pattern):
            reversed_filename = reverse_string(filename)
            print(os.path.join(root, reversed_filename))

# 사용자로부터 디렉터리 경로와 파일 패턴 입력받기
directory_to_search = input("Enter the dir to search: ")
file_pattern = input("Enter the file pattern: ")

# 파일 검색 함수 호출
find_files(directory_to_search, file_pattern)

