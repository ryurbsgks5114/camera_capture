from ftplib import FTP, error_perm, all_errors
from config import (
    FTP_HOST,
    FTP_PORT,
    FTP_USER,
    FTP_PASSWORD,
    FTP_BASE_DIR
)

# ==========================================
# FTP 설정 가져오는 함수
# ==========================================
def _resolve_ftp_config(ftp_config=None):
    if ftp_config is None:
        return {
            "host": FTP_HOST,
            "port": int(FTP_PORT),
            "user": FTP_USER,
            "password": FTP_PASSWORD,
            "base_dir": FTP_BASE_DIR
        }

    return {
        "host": ftp_config["host"],
        "port": int(ftp_config["port"]),
        "user": ftp_config["user"],
        "password": ftp_config["password"],
        "base_dir": ftp_config["base_dir"]
    }

# ==========================================
# FTP 연결 및 로그인 공통 함수
# ==========================================
def _connect_ftp(ftp_config=None):
    # FTP 설정값 가져오기
    settings = _resolve_ftp_config(ftp_config)

    ftp = FTP()

    try:
        # FTP 서버 연결
        ftp.connect(settings["host"], settings["port"], timeout=10)
        # 로그인
        ftp.login(settings["user"], settings["password"])
        # Passive Mode 사용
        ftp.set_pasv(True)

        return ftp, settings
    except Exception:
        try:
            ftp.close()
        except Exception:
            pass
        raise

# ==========================================
# FTP 연결, 저장 경로 접근 가능 여부 검사 함수
# ==========================================
def validate_ftp_connection(ftp_config):
    ftp = None

    try:
        ftp, settings = _connect_ftp(ftp_config)
        ftp.cwd(settings["base_dir"])

        return True, "FTP 연결 및 저장 경로 확인에 성공했습니다."
    except error_perm as error:
        return False, "FTP 인증 또는 경로 권한 오류: {}".format(error)
    except all_errors as error:
        return False, "FTP 연결 또는 통신 오류: {}".format(error)
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                try:
                    ftp.close()
                except Exception:
                    pass

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
    ftp = None

    try:
        ftp, settings = _connect_ftp(ftp_config)

        # 날짜별 FTP 폴더 경로
        remote_directory = settings["base_dir"].rstrip("/") + "/" + date_folder

        # 폴더 생성 / 이동
        create_ftp_directory(ftp, remote_directory)

        # 파일 업로드
        with open(filename, "rb") as file:
            ftp.storbinary("STOR " + filename.name, file)

        print("----------------------------------------")
        print("FTP 업로드 성공")
        print("----------------------------------------")

        return True
    except Exception as error:
        print("FTP 업로드 실패")
        print("오류:", error)

        return False
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                try:
                    ftp.close()
                except Exception:
                    pass