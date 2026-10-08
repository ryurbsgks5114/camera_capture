from config import OUTPUT_DIR

# ==========================================
# 저장 폴더 생성 및 경로 반환 함수
# ==========================================
def get_date_directory(today_str):
    date_dir = OUTPUT_DIR / today_str
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir