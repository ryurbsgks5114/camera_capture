
import subprocess
import threading
import time

from config import CAPTURE_WIDTH, CAPTURE_HEIGHT


# ==========================================
# 실시간 카메라 프레임 수신 클래스
# ==========================================
class CameraFrameStream:
    """
    FFmpeg를 실행하여 카메라 영상을 실시간으로 수신한다.

    - JPEG 프레임을 계속 수신
    - 메모리에는 최신 프레임 1장만 유지
    - 프레임 수신 시각을 monotonic 기준으로 기록
    - 종료 요청 시 FFmpeg 프로세스 및 스레드 정리
    """

    def __init__(self, camera_device, dshow_device_name):
        self.camera_device = camera_device
        self.camera_name = camera_device.get("name", "Unknown Camera")
        self.dshow_device_name = dshow_device_name

        self.process = None
        self.reader_thread = None

        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        # 최신 프레임 정보
        self.latest_frame = None
        self.frame_count = 0

        # 프레임 수신 오류
        self.error = None

        # JPEG 프레임 파싱용 버퍼
        self.jpeg_buffer = bytearray()

    # ==========================================
    # FFmpeg 실시간 프레임 수신 시작
    # ==========================================
    def start(self):
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError("이미 카메라 스트림이 실행 중입니다.")

        self.stop_event.clear()
        self.latest_frame = None
        self.frame_count = 0
        self.error = None
        self.jpeg_buffer = bytearray()

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-nostats",

            "-f", "dshow",
            "-video_size",
            "{}x{}".format(CAPTURE_WIDTH, CAPTURE_HEIGHT),
            "-i",
            "video={}".format(self.dshow_device_name),

            "-an",
            "-sn",
            "-dn",

            # JPEG 프레임을 표준 출력으로 전달
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-q:v", "2",
            "pipe:1"
        ]

        print("----------------------------------------")
        print("[카메라 스트림 시작]")
        print("카메라:", self.camera_name)
        print("FFmpeg 장치:", self.dshow_device_name)

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )

            # 프레임을 계속 읽는 전용 스레드 실행
            self.reader_thread = threading.Thread(
                target=self._read_frames,
                daemon=True,
                name="CameraFrameReader"
            )

            self.reader_thread.start()

            return True

        except OSError as error:
            self.error = str(error)

            print("[카메라 스트림 실행 실패]", error)

            self.stop()

            return False

    # ==========================================
    # JPEG 프레임 읽기 및 최신 프레임 갱신
    # ==========================================
    def _read_frames(self):
        try:
            while not self.stop_event.is_set():
                if self.process is None or self.process.stdout is None:
                    break

                # FFmpeg 표준 출력에서 데이터 읽기
                chunk = self.process.stdout.read(4096)

                # 프로세스 종료 또는 출력 종료
                if not chunk:
                    break

                self.jpeg_buffer.extend(chunk)

                # 수신 데이터에서 JPEG 프레임 추출
                self._extract_frames()

        except Exception as error:
            if not self.stop_event.is_set():
                self.error = str(error)
                print("[프레임 수신 오류]", error)

        finally:
            print(
                "[프레임 수신 종료]",
                self.camera_name,
                "수신 프레임:",
                self.frame_count
            )

    # ==========================================
    # JPEG 데이터에서 완성된 프레임 추출
    # ==========================================
    def _extract_frames(self):
        while True:
            # JPEG 시작 마커 검색
            start_index = self.jpeg_buffer.find(b"\xff\xd8")

            if start_index == -1:
                # 다음 데이터와 JPEG 시작 마커가 이어질 수 있으므로
                # 마지막 바이트만 유지
                if self.jpeg_buffer[-1:] == b"\xff":
                    self.jpeg_buffer[:] = b"\xff"
                else:
                    self.jpeg_buffer.clear()

                return

            # 시작 마커 앞의 불필요한 데이터 제거
            if start_index > 0:
                del self.jpeg_buffer[:start_index]

            # JPEG 종료 마커 검색
            end_index = self.jpeg_buffer.find(b"\xff\xd9", 2)

            if end_index == -1:
                # 비정상적으로 큰 프레임 버퍼 방지
                if len(self.jpeg_buffer) > 32 * 1024 * 1024:
                    self.jpeg_buffer.clear()

                    print("[프레임 오류] JPEG 데이터 크기 초과")

                return

            # JPEG 프레임 한 장 추출
            frame_data = bytes(self.jpeg_buffer[:end_index + 2])

            # 처리한 데이터 제거
            del self.jpeg_buffer[:end_index + 2]

            # 프레임 수신 시각 기록
            received_at = time.monotonic()

            self._update_latest_frame(frame_data, received_at)

    # ==========================================
    # 최신 프레임 갱신
    # ==========================================
    def _update_latest_frame(self, frame_data, received_at):
        with self.lock:
            self.frame_count += 1

            # 기존 프레임을 새 프레임으로 교체
            self.latest_frame = {
                "data": frame_data,
                "received_at": received_at,
                "sequence": self.frame_count
            }

    # ==========================================
    # 현재 최신 프레임 가져오기
    # ==========================================
    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None

            # 프레임 정보 복사
            return {
                "data": self.latest_frame["data"],
                "received_at": self.latest_frame["received_at"],
                "sequence": self.latest_frame["sequence"]
            }

    # ==========================================
    # 카메라 스트림 상태 확인
    # ==========================================
    def is_running(self):
        return (
            self.process is not None
            and self.process.poll() is None
            and not self.stop_event.is_set()
        )

    # ==========================================
    # FFmpeg 종료 및 프레임 데이터 초기화
    # ==========================================
    def stop(self):
        self.stop_event.set()

        # FFmpeg 프로세스 종료
        if self.process is not None:
            if self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)

                except subprocess.TimeoutExpired:
                    print("[FFmpeg 종료 지연] 강제 종료합니다.")

                    self.process.kill()
                    self.process.wait(timeout=5)

                except OSError as error:
                    print("[FFmpeg 종료 오류]", error)

        # 프레임 수신 스레드 종료 대기
        if self.reader_thread is not None:
            self.reader_thread.join(timeout=5)

            if self.reader_thread.is_alive():
                print("[프레임 수신 스레드] 종료 대기 시간 초과")

        # 표준 출력 파이프 닫기
        if self.process is not None and self.process.stdout is not None:
            try:
                self.process.stdout.close()
            except OSError:
                pass

        # 최신 프레임 및 버퍼 초기화
        with self.lock:
            self.latest_frame = None
            self.jpeg_buffer.clear()

        self.process = None
        self.reader_thread = None

        print("[카메라 스트림 종료]", self.camera_name)


# ==========================================
# 기존 단일 사진 촬영 함수
# ==========================================
def capture_image(camera_device, filename, dshow_device_name):
    # 카메라 검색 결과에서 DirectShow 장치 이름 가져오기
    camera_name = camera_device["name"]

    print("----------------------------------------")
    print("카메라:", camera_name)
    print("FFmpeg 장치:", dshow_device_name)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-nostats",
        "-f",
        "dshow",
        "-video_size",
        "{}x{}".format(CAPTURE_WIDTH, CAPTURE_HEIGHT),
        "-i",
        "video={}".format(dshow_device_name),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-update",
        "1",
        "-y",
        str(filename)
    ]

    try:
        subprocess.run(command, check=True, timeout=15)

        print("촬영 완료")
        print("파일:", filename)
        print("----------------------------------------")

        return True

    except subprocess.CalledProcessError as error:
        print("촬영 실패")
        print("카메라:", camera_name)
        print("오류 코드:", error.returncode)

        return False

    except subprocess.TimeoutExpired:
        print("촬영 실패")
        print("카메라:", camera_name)
        print("오류: 촬영 시간 초과")

        return False

    except OSError as error:
        print("촬영 실패")
        print("카메라:", camera_name)
        print("오류:", error)

        return False


# ==========================================
# 촬영된 원본 사진으로 썸네일 생성
# ==========================================
def create_thumbnail(filename):
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-nostats",
        "-i", str(filename),
        "-vf", "scale=480:-1",
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "pipe:1"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            timeout=15
        )

        return result.stdout

    except subprocess.CalledProcessError as error:
        print("[썸네일 생성 실패] FFmpeg 오류:", error.returncode)

        return None

    except subprocess.TimeoutExpired:
        print("[썸네일 생성 실패] 처리 시간 초과")

        return None

    except OSError as error:
        print("[썸네일 생성 실패]", error)

        return None
