from pathlib import Path
from config import OUTPUT_DIR

# ==========================================
# 저장 폴더 생성 및 경로 반환 함수
# ==========================================
def get_date_directory(today_str, base_path=None):
    # 별도 저장 경로가 전달되지 않으면 기존 기본 저장 폴더 사용
    root_dir = Path(base_path) if base_path else OUTPUT_DIR

    # 날짜별 저장 폴더 경로 생성
    date_dir = root_dir / today_str

    # 폴더가 없으면 상위 폴더까지 생성
    date_dir.mkdir(parents=True, exist_ok=True)

    return date_dir