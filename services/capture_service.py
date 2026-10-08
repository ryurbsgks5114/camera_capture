import time
from datetime import datetime
from config import SIDE_CAMERA, TOP_CAMERA, INTERVAL_MINUTES, OUTPUT_DIR
from camera.capture import capture_image
from camera.storage import get_date_directory
from services.ftp_service import upload_to_ftp

# 전역 상태 변수 관리
is_running = False
capture_thread = None
current_interval_minutes = None

# ==========================================
# 두 카메라 촬영 함수
# ==========================================
def capture_cameras(storage_mode="both", ftp_config=None):
    # 촬영 시작 시간
    capture_start = time.time()

    # 현재 시간
    now = datetime.now()

    # 파일명에 사용할 시간
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    # 오늘 날짜 폴더
    today = now.strftime("%Y%m%d")

    # 저장 폴더 생성 및 경로 할당
    date_dir = get_date_directory(today)

    # 사진 파일 이름
    side_filename = date_dir / ("S_" + timestamp + ".jpg")
    top_filename = date_dir / ("T_" + timestamp + ".jpg")

    print("========================================")
    print("촬영 시작")
    print("촬영 시간:", now.strftime("%Y-%m-%d %H:%M:%S"))
    print("========================================")

    # 사이드, 탑 카메라 촬영
    side_success = capture_image(SIDE_CAMERA, side_filename)
    top_success = capture_image(TOP_CAMERA, top_filename)

    # 촬영에 걸린 시간 계산
    capture_elapsed = time.time() - capture_start

    print("========================================")
    print("촬영 작업 완료")
    print("촬영 소요 시간:", round(capture_elapsed, 2), "초")

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
    if storage_mode == "both":
        if side_success:
            upload_to_ftp(side_filename, today, ftp_config)
        if top_success:
            upload_to_ftp(top_filename, today, ftp_config)
    elif storage_mode == "ftp":
        if side_success:
            upload_success = upload_to_ftp(side_filename, today, ftp_config)
            if upload_success:
                try:
                    side_filename.unlink()
                except FileNotFoundError:
                    pass
        if top_success:
            upload_success = upload_to_ftp(top_filename, today, ftp_config)
            if upload_success:
                try:
                    top_filename.unlink()
                except FileNotFoundError:
                    pass
    elif storage_mode == "local":
        pass

    return capture_elapsed

# ==========================================
# 자동 촬영 루프 함수
# ==========================================
def capture_loop(start_time, interval_minutes, storage_mode, ftp_config):
    global is_running

    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작")
    print("========================================")
    print("촬영 예정 시간:", start_time)
    print("촬영 간격:", interval_minutes, "분")
    print("저장 방식:", storage_mode)
    print("========================================")

    # ======================================
    # 시작 시간 계산
    # ======================================
    now = datetime.now()
    target_time = datetime.combine(now.date(), start_time)

    # 지정한 시작 시간이 이미 지났으면 바로 실행, 아니면 대기 시간 계산
    if target_time <= now:
        next_capture_time = time.monotonic()
    else:
        wait_seconds = (target_time - now).total_seconds()
        next_capture_time = time.monotonic() + wait_seconds

    interval_seconds = interval_minutes * 60

    # ======================================
    # 반복 촬영 루프
    # ======================================
    while is_running:
        wait_seconds = next_capture_time - time.monotonic()

        # 남은 시간이 있으면 1초 간격으로 확인하며 대기 (빠른 종료 대응)
        if wait_seconds > 0:
            print("다음 촬영까지:", round(wait_seconds, 2), "초 대기합니다.")

            while is_running:
                wait_seconds = next_capture_time - time.monotonic()
                if wait_seconds <= 0:
                    break
                time.sleep(min(1, wait_seconds))

        # 대기 중 정지 신호(is_running=False)를 받은 경우 종료
        if not is_running:
            break

        # 카메라 촬영 및 저장 수행
        capture_cameras(storage_mode=storage_mode, ftp_config=ftp_config)

        # 다음 촬영 예정 시간 업데이트
        next_capture_time += interval_seconds
        current_time = time.monotonic()

        # 촬영 처리 지연으로 다음 예정 시간이 이미 지났다면 현재 시간 기준으로 재설정
        if next_capture_time <= current_time:
            next_capture_time = current_time + interval_seconds

    print()
    print("========================================")
    print("촬영 작업 종료")
    print("========================================")

# ==========================================
# 다음 촬영 시점까지의 대기 시간 계산 및 대기 함수(라즈베리 파이 단독 실행 경우 - main.py 돌리기 위해서)
# ==========================================
def wait_until_next_capture(capture_elapsed):
    interval_seconds = INTERVAL_MINUTES * 60

    # 촬영 시간만큼 다음 대기 시간을 줄인다.
    wait_seconds = interval_seconds - capture_elapsed

    # 촬영 자체가 설정된 간격보다 오래 걸린 경우
    if wait_seconds < 0:
        wait_seconds = 0

    print("다음 촬영까지", round(wait_seconds, 2), "초 대기합니다.")

    time.sleep(wait_seconds)

# ==========================================
# 라즈베리 파이 단독 실행 전용 무한 촬영 루프 함수
# ==========================================
def run_standalone_capture():
    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작 (단독 실행)")
    print("========================================")
    print("사이드 카메라:", SIDE_CAMERA)
    print("탑 카메라:", TOP_CAMERA)
    print("촬영 간격:", INTERVAL_MINUTES, "분")
    print("사진 저장 위치:", OUTPUT_DIR)
    print("종료하려면 Ctrl + C 를 누르세요.")

    while True:
        capture_elapsed = capture_cameras(storage_mode="both")
        
        # 소요 시간을 고려하여 다음 촬영 시점까지 대기
        wait_until_next_capture(capture_elapsed)