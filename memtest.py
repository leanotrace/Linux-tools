# 필요한 라이브러리 임포트
import sys

# 메모리 변수 초기화
memory = None

# 무한 루프를 사용하여 여러 번의 입력 처리
while True:
    # 사용자 입력 받기
    command = input("명령을 입력하세요 ('init', 'check', 'remove'): ")

    # 명령 처리
    if command == 'init':
        # 100MB의 'aa'로 이루어진 문자열 초기화
        memory = 'a' * 100_000_000
        print("메모리가 초기화되었습니다.")
    elif command == 'check':
        # 처음 100개 문자 출력
        if memory is not None:
            print(memory[:100])
        else:
            print("메모리가 초기화되지 않았습니다.")
    elif command == 'remove':
        # 메모리 제거
        del memory
        print("메모리가 제거되었습니다.")
        break  # 'remove' 명령을 받으면 반복문 종료
    else:
        print("알 수 없는 명령입니다.")
