import subprocess
import time
from datetime import datetime
from ftplib import FTP
from config import (
    SIDE_CAMERA,
    TOP_CAMERA,
    INTERVAL_MINUTES,
    OUTPUT_DIR,
    FTP_HOST,
    FTP_PORT,
    FTP_USER,
    FTP_PASSWORD,
    FTP_BASE_DIR
)

# ==========================================
# FTP 폴더 생성 함수
# ==========================================
def create_ftp_directory(ftp, directory):
    directories = directory.strip("/").split("/")

    ftp.cwd("/")

    for folder in directories:
        try:
            ftp.cwd(folder)
        except Exception:
            ftp.mkd(folder)
            ftp.cwd(folder)

# ==========================================
# FTP 사진 업로드 함수
# ==========================================
def upload_to_ftp(filename, date_folder):
    try:
        ftp = FTP()

        # FTP 서버 연결
        ftp.connect(
            FTP_HOST,
            FTP_PORT,
            timeout=10
        )

        # 로그인
        ftp.login(
            FTP_USER,
            FTP_PASSWORD
        )

        # Passive Mode 사용
        ftp.set_pasv(True)

        # 날짜별 FTP 폴더 경로
        remote_directory = (
            FTP_BASE_DIR
            + "/"
            + date_folder
        )

        # 폴더 생성 / 이동
        create_ftp_directory(
            ftp,
            remote_directory
        )

        # 파일 업로드
        with open(filename, "rb") as file:
            ftp.storbinary(
                "STOR " + filename.name,
                file
            )
        print("----------------------------------------")
        print("FTP 업로드 성공")
        print("----------------------------------------")

        # FTP 연결 종료
        ftp.quit()

        return True
    except Exception as error:
        print("FTP 업로드 실패")
        print("오류:", error)

        return False

# ==========================================
# 카메라 사진 촬영 함수
# ==========================================
def capture_image(camera_device, filename):
    print("----------------------------------------")
    print("카메라:", camera_device)

    command = [
        "v4l2-ctl",
        "-d",
        camera_device,
        "--stream-mmap",
        "--stream-count=1",
        "--stream-to=" + str(filename)
    ]

    try:
        subprocess.run(
            command,
            check=True
        )

        print("촬영 완료")
        print("파일:", filename)
        print("----------------------------------------")

        return True
    except subprocess.CalledProcessError as error:
        print("촬영 실패")
        print("카메라:", camera_device)
        print("오류 코드:", error.returncode)

        return False

# ==========================================
# 두 카메라 촬영 함수
# ==========================================
def capture_cameras():
    # 촬영 시작 시간
    capture_start = time.time()

    # 현재 시간
    now = datetime.now()

    # 파일명에 사용할 시간
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    # 오늘 날짜 폴더
    today = datetime.now().strftime("%Y%m%d")

    # 오늘 날짜에 해당하는 저장 폴더
    date_dir = OUTPUT_DIR / today

    # 폴더가 없으면 생성
    date_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------
    # 사진 파일 이름
    # --------------------------------------
    side_filename = date_dir / (
        "S_" + timestamp + ".jpg"
    )

    top_filename = date_dir / (
        "T_" + timestamp + ".jpg"
    )

    print("========================================")
    print("촬영 시작")
    print(
        "촬영 시간:",
        now.strftime("%Y-%m-%d %H:%M:%S")
    )
    print("========================================")

    # --------------------------------------
    # 사이드 카메라 촬영
    # --------------------------------------
    side_success = capture_image(
        SIDE_CAMERA,
        side_filename
    )

    # --------------------------------------
    # 탑 카메라 촬영
    # --------------------------------------
    top_success = capture_image(
        TOP_CAMERA,
        top_filename
    )

    # --------------------------------------
    # 촬영에 걸린 시간 계산
    # --------------------------------------
    capture_elapsed = time.time() - capture_start

    print("========================================")
    print("촬영 작업 완료")
    print(
        "촬영 소요 시간:",
        round(capture_elapsed, 2),
        "초"
    )
    
    # 촬영 결과 확인
    if side_success and top_success:
        print("사이드 / 탑 카메라 촬영 성공")
    elif side_success:
        print("사이드 카메라만 촬영 성공")
    elif top_success:
        print("탑 카메라만 촬영 성공")
    else:
        print("두 카메라 모두 촬영 실패")

    print("========================================")

    # --------------------------------------
    # FTP 업로드
    # --------------------------------------
    if side_success:
        upload_to_ftp(
            side_filename,
            today
        )

    if top_success:
        upload_to_ftp(
            top_filename,
            today
        )

    return capture_elapsed

# ==========================================
# 다음 촬영까지 대기
# ==========================================
def wait_until_next_capture(capture_elapsed):
    interval_seconds = INTERVAL_MINUTES * 60

    # 촬영 시간만큼 다음 대기 시간을 줄인다.
    wait_seconds = interval_seconds - capture_elapsed

    # 촬영 자체가 설정된 간격보다 오래 걸린 경우
    if wait_seconds < 0:
        wait_seconds = 0

    print(
        "다음 촬영까지",
        round(wait_seconds, 2),
        "초 대기합니다."
    )

    time.sleep(wait_seconds)

# ==========================================
# 프로그램 메인
# ==========================================

def main():
    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작")
    print("========================================")
    print("사이드 카메라:", SIDE_CAMERA)
    print("탑 카메라:", TOP_CAMERA)
    print("촬영 간격:", INTERVAL_MINUTES, "분")
    print("사진 저장 위치:", OUTPUT_DIR)
    print("종료하려면 Ctrl + C 를 누르세요.")

    # ======================================
    # 자동 촬영 반복
    # ======================================
    while True:
        capture_elapsed = capture_cameras()

        wait_until_next_capture(
            capture_elapsed
        )

# ==========================================
# 프로그램 실행
# ==========================================
if __name__ == "__main__":
    main()