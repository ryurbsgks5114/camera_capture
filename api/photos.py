import re
from pathlib import Path
from flask import Blueprint, jsonify, send_from_directory
from config import OUTPUT_DIR

photos_bp = Blueprint("photos", __name__)

# ==========================================
# 촬영 사진 다운로드 API
# ==========================================
@photos_bp.route("/photos/<date>/<filename>", methods=["GET"])
def download_photo(date, filename):
    # 날짜 형식 검증: YYYYMMDD
    if not re.fullmatch(r"\d{8}", date):
        return jsonify({
            "success": False,
            "message": "날짜 형식이 올바르지 않습니다."
        }), 400

    # 파일명 형식 검증: S_YYYYMMDD_HHMMSS.jpg 또는 T_YYYYMMDD_HHMMSS.jpg
    if not re.fullmatch(r"[ST]_\d{8}_\d{6}\.jpg", filename):
        return jsonify({
            "success": False,
            "message": "사진 파일명이 올바르지 않습니다."
        }), 400

    # URL의 날짜와 사진 파일명의 날짜가 일치하는지 확인
    filename_date = filename[2:10]

    if filename_date != date:
        return jsonify({
            "success": False,
            "message": "요청 날짜와 사진 파일의 날짜가 일치하지 않습니다."
        }), 400

    # 해당 날짜의 사진 저장 폴더가 존재하는지 확인
    date_dir = Path(OUTPUT_DIR) / date

    if not date_dir.is_dir():
        return jsonify({
            "success": False,
            "message": "해당 날짜의 사진 폴더가 없습니다."
        }), 404

    # 요청한 사진 파일이 존재하는지 확인
    photo_path = date_dir / filename

    if not photo_path.is_file():
        return jsonify({
            "success": False,
            "message": "요청한 사진 파일을 찾을 수 없습니다."
        }), 404

    # 모든 검증이 완료된 사진 파일을 반환
    return send_from_directory(
        str(date_dir),
        filename,
        mimetype="image/jpeg",
        as_attachment=True
    )