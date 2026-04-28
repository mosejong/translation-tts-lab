"""GPT/Gemini 검수 결과 기반 term_glossary.csv 일괄 수정."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

GLOSSARY_PATH = Path(__file__).parent / "term_glossary.csv"

# {한국어: {lang_code: 수정값}}
CORRECTIONS = {
    # 전 언어 공통
    "스쿨뱅킹": {
        "vi": "School Banking",
        "en": "School Banking",
        "zh": "School Banking（学校自动扣款服务）",
        "th": "School Banking",
        "ms": "School Banking",
        "mn": "School Banking",
        "ru": "School Banking",
        "ja": "スクールバンキング",
    },
    "키즈노트": {
        "vi": "Kids Note(키즈노트)", "en": "Kids Note(키즈노트)",
        "zh": "Kids Note(키즈노트)", "th": "Kids Note(키즈노트)",
        "ms": "Kids Note(키즈노트)", "mn": "Kids Note(키즈노트)",
        "ru": "Kids Note(키즈노트)", "ja": "Kids Note(키즈노트)",
    },
    "학교종이": {
        "vi": "Hakgyo Jongi(학교종이)", "en": "Hakgyo Jongi(학교종이)",
        "zh": "Hakgyo Jongi(학교종이)", "th": "Hakgyo Jongi(학교종이)",
        "ms": "Hakgyo Jongi(학교종이)", "mn": "Hakgyo Jongi(학교종이)",
        "ru": "Hakgyo Jongi(학교종이)", "ja": "Hakgyo Jongi（학교종이）",
    },
    "하이클래스": {
        "vi": "HiClass(하이클래스)", "en": "HiClass(하이클래스)",
        "zh": "HiClass(하이클래스)", "th": "HiClass(하이클래스)",
        "ms": "HiClass(하이클래스)", "mn": "HiClass(하이클래스)",
        "ru": "HiClass(하이클래스)", "ja": "HiClass（ハイクラス）",
    },
    "e알리미": {
        "vi": "e-Alimi(e알리미)", "en": "e-Alimi(e알리미)",
        "zh": "e-Alimi(e알리미)", "th": "e-Alimi(e알리미)",
        "ms": "e-Alimi(e알리미)", "mn": "e-Alimi(e알리미)",
        "ru": "e-Alimi(e알리미)", "ja": "e-Alimi（e알리미）",
    },
    "코로나": {
        "vi": "COVID-19", "en": "COVID-19", "zh": "COVID-19",
        "th": "COVID-19", "ms": "COVID-19", "mn": "COVID-19",
        "ru": "COVID-19", "ja": "COVID-19",
    },
    "원": {
        "vi": "won (KRW)", "en": "KRW (Korean won)", "zh": "韩元 (KRW)",
        "th": "วอนเกาหลี (KRW)", "ms": "KRW (won Korea)",
        "mn": "солонгос вон (KRW)", "ru": "корейская вона (KRW)", "ja": "ウォン (KRW)",
    },
    "출석인정": {
        "vi": "được tính là có mặt", "en": "Recognized attendance",
        "zh": "视为出席", "th": "นับว่าเข้าเรียน",
        "ms": "dikira hadir", "mn": "ирцэд тооцох",
        "ru": "считается присутствующим", "ja": "出席として認める",
    },
    "수행평가": {
        "vi": "đánh giá thực hiện", "en": "Performance assessment",
        "zh": "学业表现评价", "th": "การประเมินผลการเรียน",
        "ms": "penilaian prestasi", "mn": "гүйцэтгэлийн үнэлгээ",
        "ru": "оценivание выполнения задания", "ja": "パフォーマンス評価",
    },
    "귀가 동의서": {
        "vi": "giấy đồng ý về cách về nhà", "en": "Home dismissal consent form",
        "zh": "放学回家同意书", "th": "ใบยินยอมการกลับบ้าน",
        "ms": "borang kebenaran balik rumah", "mn": "гэртээ харих зөвшөөрлийн маягт",
        "ru": "согласие на самостоятельный уход домой", "ja": "帰宅方法同意書",
    },
    "귀가 동의": {
        "vi": "đồng ý về cách về nhà", "en": "Home dismissal consent",
        "zh": "放学回家同意", "th": "ยินยอมการกลับบ้าน",
        "ms": "kebenaran balik rumah", "mn": "гэртээ харих зөвшөөрөл",
        "ru": "согласие на уход домой", "ja": "帰宅方法の同意",
    },
    # vi 수정
    "출결":           {"vi": "tình trạng chuyên cần", "th": "การมาเรียน/การขาดเรียน"},
    "급식":           {"vi": "bữa ăn ở trường", "zh": "校餐", "ru": "питание в школе"},
    "급식비":         {"vi": "tiền ăn ở trường"},
    "신체검사":       {"vi": "kiểm tra thể chất"},
    "투약 의뢰서":    {"vi": "phiếu yêu cầu cho trẻ uống thuốc", "zh": "服药委托书", "ms": "borang permohonan pemberian ubat"},
    "개인정보 동의서":{"vi": "giấy đồng ý cung cấp/sử dụng thông tin cá nhân"},
    "학부모 상담":    {"vi": "buổi trao đổi với phụ huynh", "th": "การพบครูของผู้ปกครอง"},
    "수련회":         {"vi": "buổi sinh hoạt tập thể", "ms": "kem sekolah"},
    "보호자 서명":    {"vi": "chữ ký của phụ huynh/người giám hộ"},
    # en/zh/th/ms 수정
    "체험학습":       {"en": "Field trip", "zh": "校外体험활동", "th": "กิจกรรมเรียนรู้นอกห้องเรียน", "ms": "aktiviti pembelajaran luar kelas", "mn": "танин мэдэхүйн аялал", "ru": "учебная экскурсия"},
    "현장체험학습":   {"ms": "lawatan sambil belajar di luar sekolah", "mn": "сургалтын аялал"},
    "방과후학교":     {"en": "After-school programs", "zh": "课后班", "th": "กิจกรรมหลังเลิกเรียน", "ms": "program selepas sekolah", "ru": "занятия после школы"},
    "원복":           {"en": "Kindergarten/Preschool uniform", "th": "ชุดนักเรียน/ชุดอนุบาล"},
    "방학 과제":      {"en": "Vacation homework"},
    "실습복":         {"en": "Activity clothes", "zh": "活动服", "ja": "活動着"},
    "상담":           {"en": "Consultation"},
    "학부모 총회":    {"en": "General parent meeting"},
    "식단표":         {"zh": "每周菜单"},
    "미세먼지":       {"zh": "PM2.5 / 细颗粒物", "ms": "habuk halus / PM2.5"},
    "손 소독제":      {"zh": "手部消毒液"},
    "체험학습비":     {"zh": "校外活动费"},
    "등원":           {"th": "ไปโรงเรียน/ไปศูนย์เด็กเล็ก", "ms": "hadir ke tadika/sekolah"},
    "하원":           {"th": "กลับบ้านจากโรงเรียน/ศูนย์เด็กเล็ก", "ms": "pulang dari tadika/sekolah", "mn": "цэцэрлэгээс гэртээ харих"},
    "참가 여부":      {"ms": "penyertaan", "ru": "участие"},
    "원장":           {"ms": "pengarah tadika"},
    # mn 수정
    "조퇴":           {"mn": "эрт харих"},
    "종업식":         {"mn": "хичээлийн жилийн хаалтын ёслол"},
    "학년":           {"mn": "ангийн түвшин"},
    "반":             {"mn": "анги"},
    # ru 수정
    "신청서":         {"ru": "заявление"},
    "확인서":         {"ru": "справка"},
    "생활지도":       {"ru": "правила поведения"},
    # ja 수정
    "방학":           {"ja": "長期休み"},
    "개학":           {"ja": "始業日"},
}


def main():
    with GLOSSARY_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    total = 0
    for row in rows:
        korean = row["korean"]
        if korean in CORRECTIONS:
            for lang, new_val in CORRECTIONS[korean].items():
                col = f"preferred_{lang}"
                if col in row and row[col] != new_val:
                    row[col] = new_val
                    total += 1

    with GLOSSARY_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"수정 완료: {total}개 셀 업데이트")
    print(f"수정된 용어: {len(CORRECTIONS)}개")


if __name__ == "__main__":
    main()
