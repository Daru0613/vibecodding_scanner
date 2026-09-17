# OpenWeb KR Vibe Coding Collector

중부대학교 2026학년도 2학기 “오픈웹에서의 유출 정보 생태 파악 연구”를 위한 공개 웹 URL 수집·분류 도구입니다. 한 사이트를 깊게 크롤링하지 않고 공개된 여러 사이트의 메인 HTML을 한 번씩 얕게 확인합니다. 공격, exploit, 인증 우회, CAPTCHA/WAF 우회 및 취약점 검사는 수행하지 않습니다.

## 설치

Python 3.12 이상을 권장합니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 실행

```powershell
python main.py
python main.py --limit 1000
python main.py --resume
python main.py --source commoncrawl
python main.py --source ct
python main.py --source github
python main.py --output results/csv/custom.csv --jsonl results/jsonl/custom.jsonl
python main.py --concurrency 5
```

기본값은 전역 동시 요청 5개, 도메인별 1개, 읽기 제한 8초, 재시도 0회, 리다이렉트 3회, 응답 크기 2MB입니다. 최초 스캔에서는 연결된 JavaScript 파일을 추가로 내려받지 않습니다. 중단된 작업은 `collector.db`의 상태를 이용해 `--resume`으로 이어갑니다.

실행 중 CMD에는 수집원 완료율과 확보 후보 수가 먼저 표시되고, 이어서 사이트 스캔 퍼센트 게이지, 완료/전체 수, HTTP 성공 수, CSV 저장 수, 오류 수, 경과시간과 예상 남은 시간(ETA)이 한 줄로 갱신됩니다. 비동기 완료 순서와 무관하게 전체 처리량 기준으로 계산됩니다.

## 수집원

- Common Crawl: 공개 웹 크롤링 인덱스에서 URL 후보를 얻습니다. `source_seen_at`은 Common Crawl이 URL을 관찰한 시각이지 사이트 수정 시각이 아닙니다.
- Certificate Transparency(CT): 공개 TLS 인증서 로그에서 호스트 후보를 얻습니다. 인증서 시각을 사이트 생성·수정 시각으로 간주하지 않습니다.
- GitHub: 저장소를 분석하지 않고 repository metadata, 설명 및 공개 README에 명시된 외부 배포 URL만 찾습니다. GitHub 저장소·raw URL은 스캔 대상에서 제외합니다.
- Seed/Search: 설정에 지정한 공개 링크 파일 또는 검색 API 결과를 후보로 사용합니다. 검색 API 키가 없으면 해당 수집원은 조용히 건너뜁니다.

CT와 Common Crawl은 기본 활성화되어 있습니다. `config/settings.yaml`에서 활성 여부와 쿼리를 조정할 수 있습니다. `lovable.app`, `vercel.app` 같은 실제 배포 호스트는 해외 TLD라는 이유로 제외하지 않습니다.

## 판별 기준

Korea Detector는 `lang=ko`, 사용자에게 보이는 글의 한글 비율, 국내 전화번호·주소·화폐·조직 표현과 `.kr`을 조합해 `KR`, `KR_POSSIBLE`, `UNKNOWN`으로 분류합니다. script, style, noscript 내용은 한글 비율에서 제외합니다. `.kr`이 없다는 이유로 감점하거나 제외하지 않습니다.

Lovable Detector는 호스팅 도메인, analytics 경로, 전용 헤더, HTML·runtime 흔적을 근거로 `LOVABLE_CONFIRMED`, `LOVABLE_PROBABLE`, `NO_LOVABLE_EVIDENCE`를 기록합니다.

Claude Detector는 확정 가능한 배포 인프라 흔적이 일반적으로 없으므로 Tailwind utility 밀집도, Lucide 형태 SVG, 반복 섹션 주석 및 UI 구조의 조합만 보조적으로 사용합니다. 결과는 `CLAUDE_POSSIBLE` 또는 `NO_CLAUDE_EVIDENCE`이며 Claude 사용을 확정한다는 의미가 아닙니다. React, Next.js, Vite, Tailwind, Lucide, TanStack, Supabase, Firebase는 참고용 framework/libraries 정보로만 기록합니다.

CSV에는 고신뢰도 바이브코딩 후보만 기록합니다. Lovable 또는 다른 빌더의 기술적 흔적, 혹은 직접적인 Claude Artifact 흔적이 있어야 하며 Tailwind·Lucide·일반 UI 구조만으로는 출력하지 않습니다. YouTube 등 영상·소셜 플랫폼, 중국 도메인과 중국어 중심 페이지도 제외합니다. 제외된 처리 기록은 연구 감사용 SQLite에 남습니다.

## 결과 파일

CSV는 사람이 검토하기 쉬운 16개 핵심 컬럼만 저장합니다. URL·제목·수집 출처·원본 관찰 시각·HTTP 결과·Lovable/Claude 판정과 근거·framework·추가 조사 필요 여부를 포함합니다. `collected_at`, `checked_at`, 한국 관련성 상세 값은 CSV에서 제외하지만 JSONL과 SQLite에는 재검토를 위해 유지합니다. evidence 배열은 CSV에서는 JSON 문자열, JSONL에서는 구조화된 객체로 저장됩니다.

시간 필드의 의미는 다음과 같습니다.

- `source_seen_at`: 외부 수집원이 URL 또는 호스트를 관찰한 시각. 알 수 없으면 비워 두며 임의 생성하지 않습니다.
- `collected_at`: 이 프로그램이 후보를 가져온 시각.
- `checked_at`: 실제 사이트에 HTTP GET을 보낸 시각.
- `http_last_modified`: 서버가 응답한 Last-Modified 값. 사이트 생성일로 간주하지 않습니다.

## 테스트

```powershell
python -m pytest -q
python test_collect_100.py
```

`test_collect_100.py`는 기존 파일명을 유지하지만 현재는 활성화된 실제 Collector로 최대 500개 후보를 수집합니다. CSV는 `results/csv/test_results_500.csv`, JSONL은 `results/jsonl/test_results_500.jsonl`에 저장됩니다. 외부 API, 네트워크 상태 및 rate limit에 따라 후보 수와 실행 결과가 달라질 수 있습니다.

## 탐지 규칙과 향후 Security Detector

빌더 서명은 `config/signatures.yaml`에 추가할 수 있습니다. 일반 프레임워크 흔적 하나만으로 특정 빌더라고 판정해서는 안 됩니다.

`scanner/placeholder.py`는 향후 사용자가 검증한 취약점·개인정보 노출·보안 설정 오류 Detector를 연결하기 위한 자리입니다. 현재 버전은 그런 검사를 수행하지 않으며, 추가할 때에도 명시적 허가와 별도 정책 아래 구현해야 합니다.
