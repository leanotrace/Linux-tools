import subprocess
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import pickle

# 로그 파일 설정
LOG_FILE = "/var/log/recent_patch.log"
CACHE_FILE = "/var/cache/patch_cache.pkl"

# 이메일 알림 설정
SMTP_SERVER = "smtp.naver.com"
SMTP_PORT = 587
SMTP_USER = "ghtjd785@naver.com"
SMTP_PASS = "nase@cuver1@"
TO_EMAIL = "leanotrace@gmail.com"

def write_log(message):
    """로그 파일에 메시지를 기록합니다."""
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def parse_updates(updates):
    """업데이트 목록에서 패키지 이름과 버전을 파싱합니다."""
    update_list = []
    for line in updates.splitlines():
        if len(line.split()) >= 2:
            package_name, version = line.split()[:2]
            update_list.append((package_name, version))
    return update_list

def load_cache():
    # 캐시 파일에서 업데이트 된 목록을 로드
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache_data = pickle.load(f)
            cache_time = cache_data.get('time') # 캐시에서 time 키에 해당하는 value를 가져온다.
            if cache_time and datetime.now() - cache_time < timedelta(minutes=10):  # cache_time이 None인지 and 10분이내 생성
                return cache_data.get('updates') # updates 키에 대한 값 반환
            
            #timedelta = 10분을 나타내는 timedelta 객체 생성
            # 현재 시간(datetime.now)에서 캐시 파일이 마지막으로 갱신된 시간을 뻄 = 경과 시간
    return None  # 캐시가 유효하지 않으면 None 반환

def save_cache(updates):
    # 업데이트 목록을 캐시 파일에 저장
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump({'time': datetime.now(), 'updates': updates}, f)

def check_updated_versions(selected_packages):
    
    updated_list = []
    try:
        # 패키지의 최신 버전 확인
        result = subprocess.run(['rpm', '-q'] + selected_packages, stdout=subprocess.PIPE, universal_newlines=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.split('-')
                pkg_name = '-'.join(parts[:-2]) # 처음부터 ~ 뒤에서 두번째 요소까지 (= 패키지 이름만)
                version = '-'.join(parts[-2:]) # 뒤에서 두번째 요소부터 끝까지 (= 버전만)
                updated_list.append((pkg_name, version))
        else:
            write_log("업데이트된 버전을 확인하는 중 오류가 발생했습니다.\n" + result.stderr)
    except Exception as e:
        write_log(f"버전 확인 중 오류 발생: {e}")
    
    return updated_list

def check_updates():
    """업데이트가 필요한 패키지를 확인하고 결과를 반환합니다."""
    try:
        print("업데이트 확인 중...")  # 디버그 출력 추가
        
        ## 파이썬 3.7보다 낮은 버전을 사용 중이라면, text=True 대신 universal_newlines=True를 사용
        ## subprocess.run 결과는 기본적으로 바이너리 이므로 문자열로 변환해야함
        result = subprocess.run(['dnf', 'check-update'], stdout=subprocess.PIPE, universal_newlines=True)
        # print(f"dnf 명령 실행 결과 코드: {result.returncode}")  # 디버그 출력 추가
        
        if result.returncode == 100:
            updates = result.stdout
            write_log("업데이트가 필요합니다:\n" + updates)
            parsed_updates = parse_updates(updates)
            save_cache(parsed_updates) # 캐시 저장
            return parsed_updates
        else:
            write_log("업데이트가 필요하지 않습니다.")
            return None
    except Exception as e:
        write_log(f"업데이트 확인 중 오류 발생: {e}")
        return None

def send_email_notification(subject, message):#
    """이메일로 알림을 전송합니다."""
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server: # 메일 서버와 연결을 나타내는 객체
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, TO_EMAIL, msg.as_string())
        write_log("이메일 알림이 성공적으로 전송되었습니다.")
    except Exception as e:
        write_log(f"이메일 전송 중 오류 발생: {e}")

def prompt_user_for_updates(update_list):
    """사용자에게 업데이트할 패키지를 선택하도록 요청합니다."""
    print("\n다음 패키지들이 업데이트 가능합니다:")
    for idx, (pkg, ver) in enumerate(update_list):
        print(f"{idx + 1}. {pkg} -> {ver}")

    selected_indices = input("업데이트할 패키지의 번호를 선택하세요 (콤마로 구분하여 다중 선택 가능): ")
    selected_indices = [int(i.strip()) - 1 for i in selected_indices.split(",")]

    selected_packages = [update_list[i][0] for i in selected_indices if i < len(update_list)]
    return selected_packages

def perform_updates(selected_packages):
    """선택한 패키지들을 업데이트합니다."""
    try:
        # 업데이트 실행
        result = subprocess.run(['dnf', '-y', 'update'] + selected_packages, stdout=subprocess.PIPE, universal_newlines=True)
        if result.returncode == 0:
            write_log(f"선택한 패키지 업데이트가 성공적으로 완료되었습니다: {', '.join(selected_packages)}")
            
            # 업데이트된 패키지의 버전 정보 가져오기
            updated_versions = check_updated_versions(selected_packages)
            if updated_versions:
                write_log("업데이트된 패키지 및 버전 정보:")
                for pkg, ver in updated_versions:
                    write_log(f"{pkg} -> {ver}")
        else:
            write_log("업데이트 중 오류가 발생했습니다:\n" + result.stderr)
    except Exception as e:
        write_log(f"업데이트 수행 중 오류 발생: {e}")

if __name__ == "__main__":
    try:
        update_list = load_cache() # 캐시에서 업데이트 목록 로드 먼저 시도
        if not update_list:
            update_list = check_updates() # 없으면, check_update 함수 호출
            
        if update_list:
            update_details = "\n".join([f"{pkg} -> {ver}" for pkg, ver in update_list])
            send_email_notification("서버 업데이트 알림", "업데이트가 필요합니다:\n" + update_details)
            selected_packages = prompt_user_for_updates(update_list)
            if selected_packages:
                perform_updates(selected_packages)
            else:
                write_log("업데이트할 패키지가 선택되지 않았습니다.")
        else:
            write_log("시스템이 최신 상태입니다.")
    except KeyboardInterrupt:
        write_log("\n사용자가 프로그램을 종료했습니다.")

