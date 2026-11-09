
import base64
import time
from datetime import datetime

from camera.capture import (
    CameraFrameStream,
    create_thumbnail
)
from camera.discovery import (
    get_cached_cameras,
    initialize_camera_mapping,
    clear_camera_mapping
)
from camera.storage import get_date_directory
from config import (
    ENABLE_TOP_CAMERA,
    INTERVAL_MINUTES,
    OUTPUT_DIR,
    CAMERA_PREOPEN_SECONDS,
    FRAME_MAX_AGE_MS,
    CAMERA_SYNC_TOLERANCE_MS
)
from services.ftp_service import upload_to_ftp


# ==========================================
# 전역 상태 변수 관리
# ==========================================
is_running = False
capture_thread = None
current_interval_minutes = None


# ==========================================
# 카메라 스트림 생성 및 시작
# ==========================================
def start_camera_streams():
    """
    캐시된 카메라 정보를 이용하여 스트림을 시작한다.

    Top 카메라가 비활성화된 경우 Side 카메라만 시작한다.
    스트림 생성 도중 예외가 발생해도 이미 시작된 스트림을 종료한다.
    """

    detected_cameras = get_cached_cameras()

    if detected_cameras is None:
        print("[촬영 실패] 카메라 자동 매칭 정보가 초기화되지 않았습니다.")
        return None

    side_camera = detected_cameras.get("side")
    top_camera = detected_cameras.get("top")

    if not side_camera:
        print("[촬영 실패] 사이드 카메라를 찾을 수 없습니다.")
        return None

    streams = {}

    try:
        # Side 카메라 스트림 생성
        streams["side"] = CameraFrameStream(
            side_camera,
            side_camera["dshow_device_name"]
        )

        if not streams["side"].start():
            print("[촬영 실패] 사이드 카메라 스트림을 시작하지 못했습니다.")
            stop_camera_streams(streams)
            return None

        # Top 카메라가 활성화된 경우에만 스트림 생성
        if ENABLE_TOP_CAMERA:

            if not top_camera:
                print("[촬영 실패] 탑 카메라를 찾을 수 없습니다.")
                stop_camera_streams(streams)
                return None

            streams["top"] = CameraFrameStream(
                top_camera,
                top_camera["dshow_device_name"]
            )

            if not streams["top"].start():
                print("[촬영 실패] 탑 카메라 스트림을 시작하지 못했습니다.")
                stop_camera_streams(streams)
                return None

        return streams

    except Exception as error:
        print("[카메라 스트림 생성 오류]", error)
        stop_camera_streams(streams)
        return None


# ==========================================
# 카메라 스트림 종료
# ==========================================
def stop_camera_streams(streams):
    if not streams:
        return

    for view, stream in streams.items():

        try:
            stream.stop()

        except Exception as error:
            print("[{} 카메라 스트림 종료 오류]".format(view), error)


# ==========================================
# 프레임 유효성 및 동기화 검사
# ==========================================
def validate_camera_frames(streams):
    """
    최신 프레임의 유효성과 Side/Top 간 시간 차이를 검사한다.

    반환:
        성공: {"side": frame, "top": frame}
        실패: None
    """

    if not streams:
        print("[프레임 검증 실패] 카메라 스트림이 없습니다.")
        return None

    frames = {}

    for view, stream in streams.items():

        if not stream.is_running():
            print("[프레임 검증 실패] {} 카메라 스트림이 종료되었습니다.".format(view))
            return None

        frame = stream.get_latest_frame()

        if frame is None:
            print("[프레임 검증 실패] {} 카메라 프레임이 없습니다.".format(view))
            return None

        frames[view] = frame

    # 프레임 경과 시간 검사
    capture_time = time.monotonic()
    max_age_seconds = FRAME_MAX_AGE_MS / 1000.0

    for view, frame in frames.items():

        frame_age = capture_time - frame["received_at"]

        if frame_age < 0 or frame_age > max_age_seconds:
            print(
                "[프레임 검증 실패] {} 카메라 프레임이 오래되었습니다. "
                "경과 시간: {:.1f}ms".format(
                    view,
                    frame_age * 1000
                )
            )
            return None

    # Side / Top 두 카메라를 사용하는 경우 시간 차이 검사
    if ENABLE_TOP_CAMERA:

        side_time = frames["side"]["received_at"]
        top_time = frames["top"]["received_at"]

        sync_difference = abs(side_time - top_time)

        tolerance_seconds = CAMERA_SYNC_TOLERANCE_MS / 1000.0

        if sync_difference > tolerance_seconds:
            print(
                "[프레임 검증 실패] Side / Top 프레임 시간 차이 초과: "
                "{:.1f}ms".format(sync_difference * 1000)
            )
            return None

    print("[프레임 검증 성공]")

    for view, frame in frames.items():
        print(
            "{} 프레임 번호: {}".format(
                view,
                frame["sequence"]
            )
        )

    return frames


# ==========================================
# 촬영 완료 시 WebSocket 이벤트 전송
# ==========================================
def emit_photo_saved(socketio, filename, view, captured_at):

    if socketio is None:
        return

    try:
        thumbnail_data = create_thumbnail(filename)

        if not thumbnail_data:
            print(
                "[WebSocket] 썸네일 데이터가 없어 이벤트 전송을 건너뜁니다:",
                filename.name
            )
            return

        event_data = {
            "type": "photo_saved",
            "view": view,
            "filename": filename.name,
            "path": str(filename),
            "captured_at": captured_at,
            "preview_data": base64.b64encode(
                thumbnail_data
            ).decode("ascii")
        }

        socketio.emit("photo_saved", event_data)

        print("[WebSocket] 사진 썸네일 이벤트 전송:", filename.name)

    except Exception as error:
        print("[WebSocket] 사진 이벤트 전송 실패:", error)


# ==========================================
# FTP 업로드 및 임시 파일 정리
# ==========================================
def upload_and_cleanup(filename, today, ftp_config, delete_after_upload=False):
    """
    FTP 업로드를 수행한다.

    delete_after_upload=True이면 업로드 성공 여부와 관계없이
    FTP 임시 파일을 정리한다.
    """

    try:
        upload_to_ftp(filename, today, ftp_config)

    except Exception as error:
        print("[FTP 업로드 오류] {}: {}".format(filename.name, error))

    finally:
        if delete_after_upload:

            try:
                filename.unlink()
                print("[FTP 임시 파일 삭제]", filename.name)

            except FileNotFoundError:
                pass

            except OSError as error:
                print(
                    "[FTP 임시 파일 삭제 실패] {}: {}".format(
                        filename.name,
                        error
                    )
                )


# ==========================================
# 두 카메라 촬영 함수
# ==========================================
def capture_cameras(
    storage_mode="both",
    ftp_config=None,
    socketio=None,
    local_path=None,
    camera_streams=None
):
    """
    카메라 최신 프레임을 검증하고 메모리에 확정한 뒤 저장한다.

    camera_streams가 전달되지 않으면 직접 스트림을 시작하고
    CAMERA_PREOPEN_SECONDS 동안 워밍업을 진행한다.

    프레임을 메모리에 복사한 직후 카메라 스트림을 종료한다.
    이후 저장, 썸네일 생성, WebSocket 전송 및 FTP 업로드를 진행한다.
    """

    capture_start = time.monotonic()

    streams = camera_streams

    try:
        # 단독 호출 시 카메라 스트림 직접 시작
        if streams is None:

            streams = start_camera_streams()

            if streams is None:
                return time.monotonic() - capture_start

            print(
                "[카메라 워밍업] {}초 동안 프레임을 수신합니다.".format(
                    CAMERA_PREOPEN_SECONDS
                )
            )

            time.sleep(CAMERA_PREOPEN_SECONDS)

        # 프레임 검증 및 메모리 확정
        confirmed_frames = validate_camera_frames(streams)

        if confirmed_frames is None:
            print("[촬영 실패] 프레임 검증에 실패했습니다.")
            return time.monotonic() - capture_start

        # 프레임 데이터를 별도 메모리 변수에 복사
        confirmed_images = {
            view: bytes(frame["data"])
            for view, frame in confirmed_frames.items()
        }

        # 프레임 확정 시각
        now = datetime.now()

    finally:
        # 저장 및 후처리 전에 카메라 연결 종료
        stop_camera_streams(streams)

    # ======================================
    # 사진 파일 저장
    # ======================================

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y%m%d")

    if storage_mode in ("local", "both"):
        storage_path = local_path or OUTPUT_DIR
    else:
        storage_path = OUTPUT_DIR

    date_dir = get_date_directory(today, storage_path)

    side_filename = date_dir / ("S_" + timestamp + ".jpg")
    top_filename = date_dir / ("T_" + timestamp + ".jpg")

    captured_at = now.strftime("%Y-%m-%d %H:%M:%S")

    print("========================================")
    print("촬영 프레임 확정 완료")
    print("촬영 시간:", captured_at)
    print("========================================")

    side_success = False
    top_success = False

    try:
        # 검증이 통과한 이미지 데이터만 저장
        side_filename.write_bytes(confirmed_images["side"])
        side_success = True

        if ENABLE_TOP_CAMERA:
            top_filename.write_bytes(confirmed_images["top"])
            top_success = True

    except OSError as error:
        print("[사진 저장 실패]", error)

        # 두 사진을 함께 확정하는 구조이므로
        # 한쪽 저장에 실패하면 다른 쪽도 제거한다.
        for filename in (side_filename, top_filename):

            try:
                filename.unlink(missing_ok=True)

            except OSError as cleanup_error:
                print("[사진 파일 정리 실패]", cleanup_error)

        return time.monotonic() - capture_start

    # ======================================
    # WebSocket 썸네일 이벤트 전송
    # ======================================

    if side_success:
        emit_photo_saved(
            socketio,
            side_filename,
            "side",
            captured_at
        )

    if top_success:
        emit_photo_saved(
            socketio,
            top_filename,
            "top",
            captured_at
        )

    # ======================================
    # 촬영 결과 출력
    # ======================================

    capture_elapsed = time.monotonic() - capture_start

    print("========================================")
    print("촬영 작업 완료")
    print("촬영 소요 시간:", round(capture_elapsed, 2), "초")

    if side_success and top_success:
        print("사이드 / 탑 카메라 촬영 성공")

    elif side_success:
        print("사이드 카메라 촬영 성공 (Top 카메라 비활성화)")

    else:
        print("촬영 실패")

    print("========================================")

    # ======================================
    # FTP 업로드
    # ======================================

    if storage_mode == "both":

        if side_success:
            upload_and_cleanup(
                side_filename,
                today,
                ftp_config
            )

        if top_success:
            upload_and_cleanup(
                top_filename,
                today,
                ftp_config
            )

    elif storage_mode == "ftp":

        if side_success:
            upload_and_cleanup(
                side_filename,
                today,
                ftp_config,
                delete_after_upload=True
            )

        if top_success:
            upload_and_cleanup(
                top_filename,
                today,
                ftp_config,
                delete_after_upload=True
            )

    return time.monotonic() - capture_start


# ==========================================
# 지정된 시각까지 대기
# ==========================================
def wait_until(target_time):
    """
    monotonic 기준 지정 시각까지 대기한다.
    촬영 중지 요청이 들어오면 대기를 중단한다.
    """

    while is_running:

        remaining = target_time - time.monotonic()

        if remaining <= 0:
            return True

        time.sleep(min(0.2, remaining))

    return False


# ==========================================
# 자동 촬영 루프 함수
# ==========================================
def capture_loop(
    start_time,
    interval_minutes,
    storage_mode,
    ftp_config,
    socketio=None,
    local_path=None
):
    global is_running
    global current_interval_minutes

    print()
    print("========================================")
    print(" Camera Capture 프로그램 시작")
    print("========================================")
    print("촬영 예정 시간:", start_time)
    print("촬영 간격:", interval_minutes, "분")
    print("저장 방식:", storage_mode)
    print("========================================")

    try:
        now = datetime.now()
        target_time = datetime.combine(now.date(), start_time)

        # 기존 동작 유지:
        # 예약 시간이 이미 지났으면 즉시 촬영 사이클 시작
        if target_time <= now:
            next_capture_time = time.monotonic()

        else:
            wait_seconds = (target_time - now).total_seconds()
            next_capture_time = time.monotonic() + wait_seconds

        interval_seconds = interval_minutes * 60
        preopen_seconds = CAMERA_PREOPEN_SECONDS

        while is_running:

            streams = None
            capture_started = False

            try:
                # 다음 촬영 예정 시각보다 5초 먼저 카메라 연결
                preopen_time = next_capture_time - preopen_seconds

                # 예약 시간이 미래라면 사전 연결 시점까지 대기
                if not wait_until(preopen_time):
                    break

                if not is_running:
                    break

                print()
                print("[카메라 사전 연결] 촬영 예정 시각:", datetime.now())

                # Side / Top 카메라 스트림 시작
                streams = start_camera_streams()

                if streams is None:
                    print("[촬영 실패] 카메라 스트림을 시작하지 못했습니다.")

                else:
                    # 실제 스트림 시작 시점 기준 5초 워밍업
                    stream_start_time = time.monotonic()
                    warmup_complete_time = stream_start_time + preopen_seconds

                    # 예약 시각과 워밍업 완료 시각 중 더 늦은 시점에 촬영
                    capture_ready_time = max(
                        next_capture_time,
                        warmup_complete_time
                    )

                    # 예약 시각까지 또는 워밍업 완료까지 대기
                    if wait_until(capture_ready_time) and is_running:

                        capture_started = True

                        capture_cameras(
                            storage_mode=storage_mode,
                            ftp_config=ftp_config,
                            socketio=socketio,
                            local_path=local_path,
                            camera_streams=streams
                        )

            except Exception as error:
                # 해당 회차에서 발생한 예외를 기록하고
                # 촬영 루프 전체가 비정상 종료되지 않도록 처리한다.
                print("[촬영 회차 예외 발생]", error)

            finally:
                # 촬영 함수가 실행되지 못한 경우에만 여기서 스트림 종료
                # capture_cameras가 실행되었다면 해당 함수의 finally에서 종료한다.
                if streams is not None and not capture_started:
                    stop_camera_streams(streams)

            if not is_running:
                break

            # 다음 촬영 예정 시간 업데이트
            next_capture_time += interval_seconds

            current_time = time.monotonic()

            # 촬영 처리 지연으로 다음 예정 시간이 이미 지났다면
            # 현재 시각을 기준으로 다음 간격을 다시 계산
            if next_capture_time <= current_time:
                next_capture_time = current_time + interval_seconds

    except Exception as error:
        # 촬영 루프 자체의 예외 처리
        print("[촬영 루프 예외 발생]", error)

    finally:
        # ==================================
        # 촬영 루프 종료 상태 정리
        # ==================================

        is_running = False
        current_interval_minutes = None

        print()
        print("========================================")
        print("촬영 작업 종료")
        print("촬영 상태 초기화 완료")
        print("========================================")


# ==========================================
# 다음 촬영 시점까지의 대기 시간 계산 및 대기 함수
# ==========================================
def wait_until_next_capture(capture_elapsed):
    interval_seconds = INTERVAL_MINUTES * 60

    wait_seconds = interval_seconds - capture_elapsed

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

    initialize_camera_mapping()

    detected_cameras = get_cached_cameras()

    if detected_cameras:
        print("사이드 카메라:", detected_cameras["side"])
        print("탑 카메라:", detected_cameras["top"])

    print("촬영 간격:", INTERVAL_MINUTES, "분")
    print("사진 저장 위치:", OUTPUT_DIR)
    print("종료하려면 Ctrl + C 를 누르세요.")

    try:
        while True:
            capture_elapsed = capture_cameras(
                storage_mode="both"
            )

            wait_until_next_capture(capture_elapsed)

    except KeyboardInterrupt:
        print()
        print("[단독 실행] 사용자 종료 요청")

    finally:
        clear_camera_mapping()
