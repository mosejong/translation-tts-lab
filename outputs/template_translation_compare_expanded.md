# Expanded Template-Based Translation Experiment

- 실험일: 2026-05-06
- 모델: facebook/nllb-200-distilled-600M
- 디바이스: cpu
- 샘플 수: 20

## 최종 비교

| 방식 | 용어 보존율 | 평균 추론시간 |
|---|---:|---:|
| Baseline NLLB | 5/37 (14%) | 0.82s |
| Strategy A 직접치환 | 15/37 (41%) | 0.79s |
| Template-based | 37/37 (100%) | 0.00s |

## 해석

- 이 실험은 전체 번역 자연스러움이 아니라 핵심 학교 용어 보존율을 측정한다.
- 템플릿 방식은 준비물/제출물/납부/참여/금지 문장을 구조화해 NLLB 오역 구간을 우회한다.
- review_required는 템플릿 미적용 또는 용어 누락 케이스를 후속 검수 대상으로 표시한다.

## 샘플별 결과

### [1] 대회에 나가면 도화지와 색칠 도구를 준비해 주세요

- 유형: `prepare`
- 항목: 도화지 | 색칠 도구
- 기대 용어: giấy vẽ | đồ dùng tô màu
- Baseline: 0/2 / Nếu bạn đi dự, hãy chuẩn bị đồ sơn và công cụ vẽ.
- Strategy A: 2/2 / Nếu bạn đi dự, hãy chuẩn bị giấy vẽ và đồ dùng tô màu.
- Template: 2/2 / Vui lòng chuẩn bị giấy vẽ và đồ dùng tô màu.
- review_required: N

### [2] 유성매직과 사인펜을 준비해 주세요

- 유형: `prepare`
- 항목: 유성매직 | 사인펜
- 기대 용어: bút dạ dầu | bút lông
- Baseline: 0/2 / Hãy chuẩn bị cho tôi một cái bút và ký hiệu.
- Strategy A: 2/2 / Hãy chuẩn bị bút dạ dầu và bút lông.
- Template: 2/2 / Vui lòng chuẩn bị bút dạ dầu và bút lông.
- review_required: N

### [3] 풍선과 찰흙을 가져오세요

- 유형: `bring`
- 항목: 풍선 | 찰흙
- 기대 용어: bóng bay | đất sét
- Baseline: 0/2 / Mang bóng và lùn đi.
- Strategy A: 1/2 / Hãy mang bóng bay và sét.
- Template: 2/2 / Vui lòng mang theo bóng bay và đất sét.
- review_required: N

### [4] 실내화와 물통을 챙겨 주세요

- 유형: `bring`
- 항목: 실내화 | 물통
- 기대 용어: giày trong nhà | bình nước
- Baseline: 1/2 / Hãy lấy đồ nội thất và bình nước.
- Strategy A: 0/2 / Giày trong nhà và nước bình.
- Template: 2/2 / Vui lòng mang theo giày trong nhà và bình nước.
- review_required: N

### [5] 수채화 물감과 붓을 준비해 주세요

- 유형: `prepare`
- 항목: 수채화 물감 | 붓
- 기대 용어: màu nước | cọ vẽ
- Baseline: 0/2 / Hãy chuẩn bị một cái bơm và nước lọc.
- Strategy A: 0/2 / Hãy chuẩn bị cho chúng tôi nước và màu sắc.
- Template: 2/2 / Vui lòng chuẩn bị màu nước và cọ vẽ.
- review_required: N

### [6] 전교생은 체육복과 실내화를 지참해 주세요

- 유형: `bring`
- 항목: 체육복 | 실내화
- 기대 용어: quần áo thể dục | giày trong nhà
- Baseline: 0/2 / Các bạn, hãy tham gia vào buổi tập thể dục và nội thất.
- Strategy A: 0/2 / Các bạn, hãy tham gia phòng tập thể dục và giày trong.
- Template: 2/2 / Dành cho toàn thể học sinh: Vui lòng mang theo quần áo thể dục và giày trong nhà.
- review_required: N

### [7] 받아쓰기 공책과 클리어 화일을 제출해 주세요

- 유형: `submit`
- 항목: 받아쓰기 공책 | 클리어 화일
- 기대 용어: vở chính tả | túi đựng tài liệu
- Baseline: 0/2 / Xin gửi giấy tờ nhận và thư xóa.
- Strategy A: 1/2 / Xin hãy gửi vở chính tả và tài liệu trong túi.
- Template: 2/2 / Vui lòng nộp vở chính tả và túi đựng tài liệu.
- review_required: N

### [8] 물감과 붓, 도화지를 담임선생님께 제출해 주세요

- 유형: `submit`
- 항목: 물감 | 붓 | 도화지
- 기대 용어: màu vẽ | cọ vẽ | giấy vẽ
- Baseline: 0/3 / Hãy đưa cho ngài làm việc với bơm, bút và vải.
- Strategy A: 3/3 / Hãy gửi màu vẽ và cọ vẽ, giấy vẽ cho giáo sư.
- Template: 3/3 / Vui lòng nộp màu vẽ, cọ vẽ và giấy vẽ cho giáo viên chủ nhiệm.
- review_required: N

### [9] 금요일까지 참가 동의서를 담임선생님께 제출해 주세요

- 유형: `submit`
- 항목: 참가 동의서
- 기대 용어: giấy đồng ý tham gia
- Baseline: 0/1 / Hãy gửi giấy đồng ý cho ngài giám đốc vào thứ Sáu.
- Strategy A: 1/1 / Hãy gửi giấy đồng ý tham gia cho ngài giáo sư vào thứ Sáu.
- Template: 1/1 / Vui lòng nộp giấy đồng ý tham gia cho giáo viên chủ nhiệm.
- review_required: N

### [10] 스쿨뱅킹 계좌로 체험학습비를 납부해 주세요

- 유형: `pay`
- 항목: 스쿨뱅킹 계좌 | 체험학습비
- 기대 용어: tài khoản School Banking | phí học tập trải nghiệm
- Baseline: 0/2 / Hãy gửi tiền học phí vào tài khoản ngân hàng của trường.
- Strategy A: 1/2 / Hãy trả tiền cho học tập kinh nghiệm bằng tài khoản School Banking.
- Template: 2/2 / Vui lòng thanh toán tài khoản School Banking và phí học tập trải nghiệm.
- review_required: N

### [11] 발열 또는 기침 증상이 있으면 등교하지 마세요

- 유형: `avoid`
- 항목: 발열 | 기침 | 등교
- 기대 용어: sốt | ho | đi học
- Baseline: 1/3 / Nếu có triệu chứng sưng hoặc ngứa, đừng đi ngang qua.
- Strategy A: 2/3 / Nếu có triệu chứng sốt hoặc ho, đừng đến trường.
- Template: 3/3 / Vui lòng không sốt, ho và đi học.
- review_required: N

### [12] 간식과 물통을 가져오세요

- 유형: `bring`
- 항목: 간식 | 물통
- 기대 용어: đồ ăn nhẹ | bình nước
- Baseline: 1/2 / Mang đồ ăn và bình nước đi.
- Strategy A: 1/2 / Mang đồ ăn nhẹ và nước.
- Template: 2/2 / Vui lòng mang theo đồ ăn nhẹ và bình nước.
- review_required: N

### [13] 우산과 여벌 옷을 준비해 주세요

- 유형: `prepare`
- 항목: 우산 | 여벌 옷
- 기대 용어: cái ô | quần áo dự phòng
- Baseline: 0/2 / Hãy chuẩn bị cho chúng tôi những bộ quần áo của họ.
- Strategy A: 0/2 / Hãy chuẩn bị cho tôi ô và quần áo.
- Template: 2/2 / Vui lòng chuẩn bị cái ô và quần áo dự phòng.
- review_required: N

### [14] 학부모 상담 신청서를 제출해 주세요

- 유형: `submit`
- 항목: 학부모 상담 신청서
- 기대 용어: đơn đăng ký tư vấn phụ huynh
- Baseline: 0/1 / Hãy nộp đơn xin tư vấn cho cha mẹ.
- Strategy A: 0/1 / Xin xin nộp đơn tư vấn cho phụ huynh.
- Template: 1/1 / Vui lòng nộp đơn đăng ký tư vấn phụ huynh.
- review_required: N

### [15] 체육대회 당일에는 운동화와 물통을 지참해 주세요

- 유형: `bring`
- 항목: 운동화 | 물통
- 기대 용어: giày thể thao | bình nước
- Baseline: 1/2 / Hãy mang theo giày và bình nước vào ngày tập thể dục.
- Strategy A: 0/2 / Vào ngày tập thể dục, hãy tham gia giày sport và nước uống.
- Template: 2/2 / Vui lòng mang theo giày thể thao và bình nước.
- review_required: N

### [16] 현장체험학습비 15000원을 납부해 주세요

- 유형: `pay`
- 항목: 현장체험학습비 | 15000원
- 기대 용어: phí học tập trải nghiệm | 15000원
- Baseline: 0/2 / Hãy trả 15 nghìn đồng cho học tập thực tế.
- Strategy A: 0/2 / Hãy trả 15 nghìn đô la cho những trải nghiệm học phí.
- Template: 2/2 / Vui lòng thanh toán phí học tập trải nghiệm và 15000원.
- review_required: N

### [17] 도서관 봉사활동에 참여해 주세요

- 유형: `attend`
- 항목: 도서관 봉사활동
- 기대 용어: hoạt động tình nguyện thư viện
- Baseline: 0/1 / Hãy tham gia vào hoạt động tình nguyện của thư viện.
- Strategy A: 0/1 / Hãy tham gia vào thư viện tình nguyện hoạt động.
- Template: 1/1 / Vui lòng tham gia hoạt động tình nguyện thư viện.
- review_required: N

### [18] 방과후학교 수강신청서를 제출해 주세요

- 유형: `submit`
- 항목: 방과후학교 수강신청서
- 기대 용어: đơn đăng ký lớp học sau giờ học
- Baseline: 0/1 / Xin xin nộp đơn đăng ký học sau trường.
- Strategy A: 0/1 / Hãy nộp đơn xin học giờ.
- Template: 1/1 / Vui lòng nộp đơn đăng ký lớp học sau giờ học.
- review_required: N

### [19] 마스크와 개인 물병을 준비해 주세요

- 유형: `prepare`
- 항목: 마스크 | 개인 물병
- 기대 용어: khẩu trang | bình nước cá nhân
- Baseline: 1/2 / Hãy chuẩn bị mặt nạ và bình nước cá nhân.
- Strategy A: 1/2 / Hãy chuẩn bị khẩu hiệu và bình nước cá nhân.
- Template: 2/2 / Vui lòng chuẩn bị khẩu trang và bình nước cá nhân.
- review_required: N

### [20] 급식비 미납 금액을 납부해 주세요

- 유형: `pay`
- 항목: 급식비 미납 금액
- 기대 용어: tiền ăn ở trường chưa thanh toán
- Baseline: 0/1 / Hãy trả tiền cho khoản phí cấp cứu.
- Strategy A: 0/1 / Tôi muốn trả tiền cho trường học.
- Template: 1/1 / Vui lòng thanh toán tiền ăn ở trường chưa thanh toán.
- review_required: N

