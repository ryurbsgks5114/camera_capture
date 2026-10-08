import subprocess

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
        subprocess.run(command, check=True)

        print("촬영 완료")
        print("파일:", filename)
        print("----------------------------------------")

        return True
    except subprocess.CalledProcessError as error:
        print("촬영 실패")
        print("카메라:", camera_device)
        print("오류 코드:", error.returncode)

        return False