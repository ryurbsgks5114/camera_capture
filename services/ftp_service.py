from ftplib import FTP
from config import (
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
def upload_to_ftp(filename, date_folder, ftp_config=None):

    if ftp_config is None:
        ftp_host = FTP_HOST
        ftp_port = FTP_PORT
        ftp_user = FTP_USER
        ftp_password = FTP_PASSWORD
        ftp_base_dir = FTP_BASE_DIR
    else:
        ftp_host = ftp_config["host"]
        ftp_port = int(ftp_config["port"])
        ftp_user = ftp_config["user"]
        ftp_password = ftp_config["password"]
        ftp_base_dir = ftp_config["base_dir"]

    try:
        ftp = FTP()

        # FTP 서버 연결
        ftp.connect(ftp_host, ftp_port, timeout=10)

        # 로그인
        ftp.login(ftp_user, ftp_password)

        # Passive Mode 사용
        ftp.set_pasv(True)

        # 날짜별 FTP 폴더 경로
        remote_directory = (ftp_base_dir + "/" + date_folder)

        # 폴더 생성 / 이동
        create_ftp_directory(ftp, remote_directory)

        # 파일 업로드
        with open(filename, "rb") as file:
            ftp.storbinary("STOR " + filename.name, file)

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