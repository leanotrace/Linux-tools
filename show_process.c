#include <stdio.h>
#include <dirent.h>
#include <string.h>
#include <stdlib.h>

void printProcessList() {
    DIR *dir;
    struct dirent *entry;
    char path[256];
    FILE *fp;
    char processName[256];

    // /proc 디렉토리 열기
    dir = opendir("/proc");
    if (dir == NULL) {
        perror("opendir failed");
        return;
    }

    // /proc 디렉토리 내의 각 항목에 대해 반복
    while ((entry = readdir(dir)) != NULL) {
        // 디렉토리 이름이 숫자로만 구성되어 있는 경우(프로세스 디렉토리)
        if (entry->d_type == DT_DIR && strspn(entry->d_name, "0123456789") == strlen(entry->d_name)) {
            sprintf(path, "/proc/%s/comm", entry->d_name); // comm 파일 경로 생성

            // comm 파일 열기 및 프로세스 이름 읽기
            fp = fopen(path, "r");
            if (fp) {
                if (fgets(processName, sizeof(processName), fp) != NULL) {
                    // 프로세스 ID와 이름 출력
                    printf("PID: %s, Name: %s", entry->d_name, processName);
                }
                fclose(fp);
            }
        }
    }

    closedir(dir); // 디렉토리 닫기
}

int main() {
    printProcessList(); // 현재 실행 중인 프로세스 목록 출력
    return 0;
}
