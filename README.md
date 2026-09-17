# OpenWeb KR Vibe Coding Site Collector & Fingerprint Detector

공개 웹 인덱스에서 후보 URL을 얻고, 최소한의 공개 HTTP 요청으로 한국 관련성과 AI 사이트 빌더의 고유 흔적을 기록하는 연구용 도구입니다. 현재 버전은 취약점·개인정보·인증정보를 탐지하거나 저장하지 않습니다.

## 연구 및 안전 범위

- 공개 페이지, 공개 Certificate Transparency, 선택적으로 공개 Common Crawl 인덱스와 사용자가 지정한 공개 링크 파일만 사용합니다.
- 로그인/CAPTCHA/WAF/접근제어를 우회하지 않으며 401·403은 즉시 중단합니다.
- 관리 페이지 탐색, 엔드포인트 열거, 브루트포스, exploit, 비공개 API 접근을 하지 않습니다.
- 동일 도메인 요청은 기본 1개, 전체 동시 요청은 10개입니다. 브라우저 자동화는 사용하지 않습니다.
- `robots.txt`와 사이트 정책을 확인하고, 권한과 연구윤리에 맞게 수집기 쿼리를 설정할 책임은 실행자에게 있습니다.

## 설치와 실행

Python 3.12 이상을 권장합니다.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --limit 1000 --output results.csv
```

주요 옵션은 `--country korea`, `--builder lovable`, `--resume`, `--max-concurrency 10`, `--jsonl results.jsonl`입니다. API 키는 내장하지 않습니다. 기본 수집은 공개 프로젝트가 명시한 별도 홈페이지 URL과 검색 API 결과를 이용합니다. GitHub 저장소·GitHub Pages·raw 콘텐츠 링크는 결과에서 제외하며, Lovable·Vercel·Netlify·Cloudflare Pages·Replit·Base44 같은 플랫폼 호스팅 주소도 제외해 커스텀 도메인을 우선합니다. Brave 검색은 `BRAVE_SEARCH_API_KEY`, Google 검색을 선택하면 `GOOGLE_API_KEY`와 `GOOGLE_CSE_ID` 환경변수를 사용합니다. 키가 없어도 공개 프로젝트 메타데이터 기반 수집은 동작하지만 후보 수가 적을 수 있습니다. 플랫폼 자체 도메인이 필요하면 `config/settings.yaml`의 `excluded_domain_suffixes`에서 해당 도메인을 제거하십시오.

## 판정 방식

한국 관련성은 `.kr`만으로 제한하지 않습니다. 보이는 본문 텍스트의 한글 비율, `lang=ko`, 한국 전화번호·주소·통화·기관 표현을 합산합니다. script/style 내용은 한글 비율에서 제외됩니다. 서버 위치는 판정 근거로 사용하지 않습니다.

빌더 판정은 `config/signatures.yaml`의 고유 증거만 합산합니다. React/Vite/Next.js/Tailwind 등의 일반 기술은 framework 정보로만 저장하며 빌더 점수에 반영하지 않습니다. 점수 등급은 80+ CONFIRMED, 50–79 PROBABLE, 30–49 POSSIBLE, 그 미만 UNKNOWN입니다.

## 결과 구조

CSV의 첫 6개 컬럼은 `바이브코딩 유추 플랫폼`, `링크`, `바이브코딩 의심 점수`, `취약점`, `취약한 데이터`, `게시날짜`입니다. 그 뒤에 `site_id`, 원본/최종 URL, HTTP 상태, 한국 점수, 상세 빌더 증거 등 연구·감사용 컬럼이 이어집니다. 게시 날짜는 공개 HTML 메타데이터나 `<time datetime>`에서 명시적으로 확인되는 경우에만 기록합니다. 현재 버전은 취약점이나 개인정보를 검사하지 않으므로 `취약점`은 `NOT_SCANNED`, `취약한 데이터`는 빈 값으로 출력합니다. JSONL은 상세 자료를 중첩 구조로 보존하며 원본 HTML은 저장하지 않습니다.

## 시그니처와 새 빌더 추가

`config/signatures.yaml`에 `platform`, `signature_name`, `type`, `pattern`, `weight`, `confidence`, `description`을 추가합니다. 여러 문자열이 모두 있어야 하는 경우 `match: all`을 사용합니다. 새 로직이 필요하면 `FingerprintDetector` 인터페이스를 구현한 `fingerprint/new_builder.py`를 만들고 엔진에 등록할 수 있습니다.

## 테스트

```bash
pytest -q
python test_collect_100.py
```

두 번째 명령은 실제 collector → 정규화/중복제거 → GET → 한국 관련성 → fingerprint → CSV/JSONL 흐름을 최대 100개 후보로 축소 실행합니다. 기본 전역 동시성은 5이고 도메인별 1, 재시도 1회입니다. 결과는 `test_results_100.csv`와 `.jsonl`입니다. 이는 외부 서비스 상태와 공개 인덱스 결과에 의존하는 스모크 테스트입니다.

## 향후 Security Scanner 확장

`scanner/placeholder.py`가 분리된 확장 지점입니다. 향후에도 명시적 허가와 별도 정책 하에서 구현해야 하며, 개인정보 후보는 원문 대신 `finding_type`, `masked_value`, `value_hash`, `source_url`, `location`만 보존하도록 설계합니다.
