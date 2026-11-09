
import subprocess
import threading

from config import CAPTURE_WIDTH, CAPTURE_HEIGHT


# ==========================================
# 미리보기 상태 및 데이터 관리
# ==========================================

_preview_processes = {}
_preview_threads = {}
_latest_frames = {}

_preview_lock = threading.Lock()
_preview_running = False


# ==========================================
# FFmpeg JPEG 프레임 읽기
# ==========================================

def _read_preview_frames(view, process):

    buffer = bytearray()

    while process.poll() is None:

        try:
            chunk = process.stdout.read(4096)

            if not chunk:
                break

            buffer.extend(chunk)

            while True:

                start = buffer.find(b"\xff\xd8")

                if start < 0:
                    buffer.clear()
                    break

                end = buffer.find(b"\xff\xd9", start + 2)

                if end < 0:
                    if start > 0:
                        del buffer[:start]

                    break

                frame = bytes(buffer[start:end + 2])

                del buffer[:end + 2]

                # 가장 최근 프레임만 유지
                with _preview_lock:
                    _latest_frames[view] = frame

            # 비정상적인 버퍼 증가 방지
            if len(buffer) > 10 * 1024 * 1024:
                buffer.clear()

        except (OSError, ValueError) as error:

            print(
                "[미리보기 프레임 수신 실패]",
                view,
                error
            )

            break

    print("[미리보기 스트림 종료]", view)


# ==========================================
# 미리보기 시작
# ==========================================

def start_preview(cameras):

    global _preview_running

    if _preview_running:
        return False, "이미 미리보기가 실행 중입니다.", []

    preview_targets = {}

    for view in ("side", "top"):

        camera = cameras.get(view)

        if not camera:
            continue

        device_name = camera.get("dshow_device_name")

        if device_name:
            preview_targets[view] = device_name

    if not preview_targets:
        return False, "미리보기에 사용할 카메라가 없습니다.", []

    with _preview_lock:

        _preview_running = True
        _latest_frames.clear()

    started_views = []

    try:

        for view, device_name in preview_targets.items():

            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-nostats",

                "-rtbufsize", "100M",

                "-f", "dshow",
                "-video_size",
                "{}x{}".format(
                    CAPTURE_WIDTH,
                    CAPTURE_HEIGHT
                ),

                "-i",
                "video={}".format(device_name),

                # 초당 5프레임만 전달
                # 해상도 축소는 하지 않음
                "-vf", "fps=5",

                # 실제 촬영과 동일한 JPEG 품질 설정
                "-q:v", "2",

                "-f", "image2pipe",
                "-vcodec", "mjpeg",
                "pipe:1"
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )

            _preview_processes[view] = process

            reader = threading.Thread(
                target=_read_preview_frames,
                args=(view, process),
                name="Preview-{}".format(view),
                daemon=True
            )

            _preview_threads[view] = reader
            reader.start()

            started_views.append(view)

        return True, "미리보기를 시작했습니다.", started_views

    except OSError as error:

        stop_preview()

        return (
            False,
            "FFmpeg 미리보기 실행 실패: {}".format(error),
            []
        )


# ==========================================
# 최신 미리보기 프레임 가져오기
# ==========================================

def get_preview_frame(view):

    with _preview_lock:
        return _latest_frames.get(view)


# ==========================================
# 미리보기 종료
# ==========================================

def stop_preview():

    global _preview_running

    with _preview_lock:
        _preview_running = False

    for process in list(_preview_processes.values()):

        try:

            if process.poll() is None:

                process.terminate()

                try:
                    process.wait(timeout=2)

                except subprocess.TimeoutExpired:

                    process.kill()
                    process.wait(timeout=2)

        except OSError as error:

            print("[미리보기 프로세스 종료 실패]", error)

    _preview_processes.clear()

    for thread in list(_preview_threads.values()):
        thread.join(timeout=1)

    _preview_threads.clear()

    with _preview_lock:
        _latest_frames.clear()

    print("[미리보기] 모든 스트림 종료")
