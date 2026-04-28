"""
가정통신문 핵심 필드 regex 추출기.
summary.dates / times / amounts / deadlines / places / supplies 반환.

사용법:
    python extract_summary.py              # 내장 샘플 2개로 검증
    python extract_summary.py --file x.txt
"""
import re
import json
import argparse
from pathlib import Path

# ── 패턴 정의 ──────────────────────────────────────────────────

# 날짜: 2026년 5월 14일(수), 5월 14일, 5/14
_DATE = re.compile(
    r"(?:20\d{2}(?:학년도)?\s*)?(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:\([월화수목금토일]\))?"
)

# 시간: 오전 9시, 오후 2시 30분, 9:00, 09시
_TIME = re.compile(
    r"(?P<ampm>오[전후])?\s*(?P<hour>\d{1,2})시(?:\s*(?P<min>\d{1,2})분)?"
)

# 금액: 15,000원, 5000원, 약 1만원
_AMOUNT = re.compile(
    r"(?:약\s*)?(?P<num>[\d,]+)\s*원"
)

# 마감: 5월 9일(금)까지 제출, ~5월 9일
_DEADLINE = re.compile(
    r"(?:20\d{2}(?:학년도)?\s*)?(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:\([월화수목금토일]\))?\s*까지(?:\s*(?P<action>제출|납부|신청|회신|내주세요|보내주세요))?"
)

# 장소: ■ 장소: ... / 장소: ... / 에서 앞 명사구 (한계 있음)
_PLACE_LABEL = re.compile(
    r"(?:■\s*)?장소\s*[:：]\s*(?P<place>[^\n■\r]{2,30})"
)

# 준비물: ■ 준비물: 도시락, 물통, ... (쉼표/·/공백 구분)
_SUPPLY_LABEL = re.compile(
    r"(?:■\s*)?준비물\s*[:：]\s*(?P<items>[^\n■\r]{2,200})"
)
_SUPPLY_SEP = re.compile(r"[,·，、]\s*|\s{2,}")


# ── 추출 함수 ──────────────────────────────────────────────────

def extract_dates(text: str) -> list[dict]:
    seen, results = set(), []
    for m in _DATE.finditer(text):
        ko = m.group(0).strip()
        key = (m.group("month"), m.group("day"))
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "ko": ko,
            "month": int(m.group("month")),
            "day": int(m.group("day")),
            "source": "regex",
        })
    return results


def extract_times(text: str) -> list[dict]:
    seen, results = set(), []
    for m in _TIME.finditer(text):
        hour = int(m.group("hour"))
        ampm = m.group("ampm") or ""
        minute = int(m.group("min") or 0)
        # 금액 숫자가 섞이는 경우 제외 (시간은 보통 1~12시)
        if hour > 24:
            continue
        ko = m.group(0).strip()
        key = (ampm, hour, minute)
        if key in seen:
            continue
        seen.add(key)
        if ampm == "오후" and hour < 12:
            hour24 = hour + 12
        elif ampm == "오전" and hour == 12:
            hour24 = 0
        else:
            hour24 = hour
        results.append({
            "ko": ko,
            "hour24": hour24,
            "minute": minute,
            "source": "regex",
        })
    return results


def extract_amounts(text: str) -> list[dict]:
    seen, results = set(), []
    for m in _AMOUNT.finditer(text):
        raw = m.group("num").replace(",", "")
        if not raw.isdigit():
            continue
        value = int(raw)
        ko = m.group(0).strip()
        if value in seen:
            continue
        seen.add(value)
        results.append({
            "ko": ko,
            "value": value,
            "source": "regex",
        })
    return results


def extract_deadlines(text: str) -> list[dict]:
    seen, results = set(), []
    for m in _DEADLINE.finditer(text):
        ko = m.group(0).strip()
        key = (m.group("month"), m.group("day"))
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "ko": ko,
            "month": int(m.group("month")),
            "day": int(m.group("day")),
            "action": m.group("action") or "",
            "source": "regex",
        })
    return results


def extract_places(text: str) -> list[dict]:
    results = []
    for m in _PLACE_LABEL.finditer(text):
        place = m.group("place").strip().rstrip(".")
        if place:
            results.append({"ko": place, "source": "label"})
    return results


def extract_supplies(text: str) -> list[dict]:
    results = []
    for m in _SUPPLY_LABEL.finditer(text):
        raw = m.group("items").strip()
        items = [s.strip() for s in _SUPPLY_SEP.split(raw) if s.strip()]
        for item in items:
            # 너무 긴 건 준비물이 아닐 가능성 높음
            if len(item) <= 20:
                results.append({"ko": item, "source": "label"})
    return results


def extract_all(text: str) -> dict:
    return {
        "dates":     extract_dates(text),
        "times":     extract_times(text),
        "amounts":   extract_amounts(text),
        "deadlines": extract_deadlines(text),
        "places":    extract_places(text),
        "supplies":  extract_supplies(text),
    }


# ── 샘플 ──────────────────────────────────────────────────────

SAMPLE_1 = """\
2026학년도 3학년 현장체험학습 안내

■ 체험학습 일시: 2026년 5월 14일(수) 오전 9시 출발
■ 장소: 서울숲 생태체험관
■ 대상: 3학년 전체 학생
■ 이동수단: 전세버스 이용 (학교 정문 앞 탑승)
■ 준비물: 도시락, 물통, 돗자리, 편한 운동화, 여벌 옷
■ 참가비: 15,000원 (5월 9일(금)까지 스쿨뱅킹으로 납부)
■ 제출 서류: 체험학습 동의서를 5월 9일(금)까지 담임교사에게 제출
"""

SAMPLE_2 = """\
2026학년도 3학년 생존수영 교육 안내

■ 교육 기간: 2026년 6월 3일(수) ~ 6월 5일(금)
■ 교육 장소: 갈산스포츠센터 수영장
■ 이동 방법: 전세버스 이용
■ 준비물: 수영복, 수영모, 수경, 수건, 여벌 속옷, 물통
■ 참가비: 12,000원
■ 납부 기한: 2026년 5월 29일(금)까지 스쿨뱅킹으로 납부
■ 제출 서류: 생존수영 참가 동의서와 건강 상태 확인서를 2026년 5월 29일(금)까지 담임교사에게 제출
"""

SAMPLE_3 = """\
알림장 2026.04.15 준비물 안내

내일 오전 10시에 음악 수업이 있습니다.
준비물: 리코더, 음악 교과서
5월 1일까지 방과후 신청서를 내 주세요.
급식비 45,000원은 4월 30일까지 납부 바랍니다.
"""


# ── 메인 ──────────────────────────────────────────────────────

def print_result(label: str, result: dict):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    for field, items in result.items():
        if not items:
            print(f"  {field:12s}: (없음)")
            continue
        for item in items:
            ko = item.get("ko", "")
            extra = ""
            if "value" in item:
                extra = f"  → {item['value']:,}원"
            elif "hour24" in item:
                extra = f"  → {item['hour24']:02d}:{item['minute']:02d}"
            elif "month" in item and "day" in item:
                extra = f"  → {item['month']}월 {item['day']}일"
                if "action" in item and item["action"]:
                    extra += f" ({item['action']})"
            print(f"  {field:12s}: {ko}{extra}  [{item.get('source','')}]")


def run_validation(samples: list[tuple[str, str]]):
    total_fields = 0
    found_fields = 0
    for label, text in samples:
        result = extract_all(text)
        print_result(label, result)
        for items in result.values():
            total_fields += 1
            if items:
                found_fields += 1

    print(f"\n[검증 요약] {len(samples)}개 샘플 / 필드 추출률: {found_fields}/{total_fields*len(samples)//len(samples)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="", help="텍스트 파일 경로")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        result = extract_all(text)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_result(args.file, result)
        return

    run_validation([
        ("샘플1: 현장체험학습", SAMPLE_1),
        ("샘플2: 생존수영 교육", SAMPLE_2),
        ("샘플3: 알림장 준비물", SAMPLE_3),
    ])


if __name__ == "__main__":
    main()
