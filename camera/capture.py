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