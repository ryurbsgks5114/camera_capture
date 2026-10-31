import subprocess
from config import CAPTURE_WIDTH, CAPTURE_HEIGHT

# ==========================================
# 카메라 사진 촬영 함수
# ==========================================
def capture_image(camera_device, filename):
    # 카메라 검색 결과에서 DirectShow 장치 이름 가져오기
    camera_name = camera_device["name"]

    print("----------------------------------------")
    print("카메라:", camera_name)

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
        "video={}".format(camera_name),
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
        # FFmpeg를 실행하여 사진 한 장 촬영
        # 촬영이 끝나면 FFmpeg 프로세스가 종료되면서 카메라 연결도 해제됨
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
        # 원본 사진을 읽어 작은 JPEG 썸네일 데이터를 메모리로 생성
        result = subprocess.run(command, capture_output=True, check=True, timeout=15)
        
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