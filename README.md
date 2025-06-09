# AutoUpdateManager

## Description 
"AutoUpdateManager" is a py script that helps you quickly check latest packages and update manually.

This script uses DNF command to check the list of updateable packages on your system,
and provides an interface to update only the packages you select.
It is also designed to cache the latest update status to avoid duplicates dnf checks within 10 minutes.

## Key Features
- Efficieny: Utilize the cache to quickly check the status of updates and avoid redundant tasks.

- User-friendly: The command-line interface allows you to select and manage packages for updates on your own.

- Flexible: You can receive update notifications by email and view detailed version information for updated packages.

- Log history: All updates and error logs are logged for future reference.

# Requirements
- Python 3.x later

## How to install

Clone or download the source code from the GitHub repository.

```bash
git clone https://github.com/yourusername/AutoUpdateManager.git

## Example
python3 AutoUpdateManager.py


업데이트 확인 중...

857. grub2-tools.x86_64 -> 1:2.02-142.el8
858. grub2-tools-extra.x86_64 -> 1:2.02-150.el8
859. grub2-tools.x86_64 -> 1:2.02-142.el8
860. grub2-tools-extra.x86_64 -> 1:2.02-156.el8
861. grub2-tools.x86_64 -> 1:2.02-142.el8
862. grub2-tools-minimal.x86_64 -> 1:2.02-142.el8_7.1
863. grub2-tools.x86_64 -> 1:2.02-142.el8
..

업데이트할 패키지의 번호를 선택하세요 (콤마로 구분하여 다중 선택 가능): 381

[의존성 및 실제로 설치/업데이트될 패키지 목록 미리보기]
Upgrading:
 tuned           noarch           2.16.0-1.el8           baseos           312 k

위 패키지 및 의존성까지 모두 업데이트됩니다.
계속 진행하시겠습니까? (y/N): y

## check patch history
cat /var/log/recent_patch.log
[2025-06-09 12:46:08] 선택한 패키지 업데이트가 성공적으로 완료되었습니다: tuned.noarch
[2025-06-09 12:46:08] 업데이트된 패키지 및 버전 정보:
[2025-06-09 12:46:08] tuned 2.15.0-2.el8.noarch -> 2.16.0-1.el8.noarc