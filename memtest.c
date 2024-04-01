#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIZE (100 * 1024 * 1024) // 100MB의 크기를 정의하는 매크로

int main() {
    // 메모리 변수 초기화
    char *memory = NULL;

    while(1) {
        char command[10];

        printf("Enter the command ('init', 'check', 'remove'): ");
        scanf("%9s", command); // 사용자 입력 받기

        // 명령 처리
        if (strcmp(command, "init") == 0) {
            // SIZE 매크로를 사용하여 100MB의 'aa'로 이루어진 문자열 초기화
            memory = (char *)malloc(SIZE);
            if (memory == NULL) {
                printf("Memory allocation failed.\n");
                exit(1);
            }
            memset(memory, 'a', SIZE - 1);
            memory[SIZE - 1] = '\0'; // NULL 문자 추가
            printf("Memory has been initialized.\n");
        } else if (strcmp(command, "check") == 0) {
            // 처음 100개 문자 출력
            if (memory != NULL) {
                char buffer[101];
                strncpy(buffer, memory, 100);
                buffer[100] = '\0';
                printf("%s\n", buffer);
            } else {
                printf("Memory has not been initialized.\n");
            }
        } else if (strcmp(command, "remove") == 0) {
            // 메모리 제거
            free(memory);
            memory = NULL;
            printf("Memory has been removed.\n");
            break; // 'remove' 명령을 받으면 루프 종료
        } else {
            printf("Unknown command.\n");
        }
    }

    return 0;
}
