# Manuscript CI 사용 가이드

[README 한국어](README_KO.md) | [README English](README.md) | [스킬 한국어](SKILL_KO.md) | [기여 가이드 한국어](CONTRIBUTING_KO.md)

Manuscript CI는 **AI가 책을 대신 써주는 도구가 아니다.** 이미 쓴 원고를 읽고, 문제가 분명한 부분만 작게 고친 뒤, 그 수정이 원문보다 실제로 나은지 다시 검증하는 교정 도구다.

핵심 원칙은 하나다.

> **원문이 기본값이다. 더 좋아 보인다는 이유만으로 고치지 않는다.**

## 1. 어떤 책에 잘 맞나

첫 버전은 특히 다음 원고에 잘 맞는다.

- 기술서
- 비즈니스·경영서
- 실무 경험을 담은 논픽션
- 보고서형 책
- 여러 장에 걸쳐 개념·수치·사례가 반복되는 책
- 저자 고유의 말투를 유지해야 하는 원고

소설에도 쓸 수 있지만, 현재 기본 rubric은 논픽션 교정에 더 가깝다.

## 2. 가장 쉬운 사용법: AI 에이전트 스킬

Codex, Claude Code, Gemini CLI처럼 책 저장소를 직접 읽을 수 있는 AI 에이전트를 쓰고 있다면 CLI 설치보다 `SKILL.md`부터 써보는 것을 권장한다. 사람이 읽기 쉬운 한국어 설명은 [`SKILL_KO.md`](SKILL_KO.md)에 있다.

책 저장소에서 에이전트에게 다음처럼 요청한다.

```text
이 저장소의 Manuscript CI SKILL.md 원칙으로 책 전체를 먼저 감사(audit)해줘.
원문보다 확실히 나은 수정만 제안하고 저자 목소리는 보존해줘.
WRITING_BRIEF.md, DEDUP_DECISIONS.md, REVIEW_RUBRIC.md를 우선 규칙으로 사용해줘.
```

아직 세 규칙 파일이 없다면 아래 CLI의 `init`으로 만들거나 `templates/`에서 복사하면 된다.

## 3. CLI 설치

Python 3.11 이상이 필요하다.

사용만 할 때는 GitHub에서 바로 설치할 수 있다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/ksangki/manuscript-ci.git"
```

개발하거나 코드를 수정하려면:

```bash
git clone https://github.com/ksangki/manuscript-ci.git
cd manuscript-ci
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows PowerShell에서는:

```powershell
.venv\Scripts\Activate.ps1
```

## 4. 내 책에 초기 파일 만들기

책 저장소 루트에서:

```bash
manuscript-ci init .
```

네 파일이 생긴다.

```text
manuscript-ci.toml
WRITING_BRIEF.md
DEDUP_DECISIONS.md
REVIEW_RUBRIC.md
```

처음에는 이 네 파일을 잘 쓰는 게 프로그램 자체보다 중요하다.

## 5. WRITING_BRIEF.md 작성법

여기에는 “좋은 글의 일반론”이 아니라 **내 책에서 지켜야 할 것**을 적는다.

예:

```markdown
# Writing Brief

- 독자: AI 전환을 실제로 추진하는 중간 리더
- 문체: 한국어 평서체 -다/-한다
- 경험담은 실제 경험만 쓴다.
- 외부 수치에서 원인을 임의로 추론하지 않는다.
- 컨설팅 보고서처럼 매끈한 문장보다 실무자 목소리를 우선한다.
- 같은 개념의 이름은 장마다 바꾸지 않는다.
- '반드시', '유일', '대부분' 같은 강한 표현은 근거가 있을 때만 쓴다.
- 이미 좋은 문장은 더 매끈하게 만들기 위한 이유만으로 고치지 않는다.
```

## 6. DEDUP_DECISIONS.md 작성법

책이 길어지면 같은 아이디어를 여러 번 “처음처럼” 설명하게 된다. 이 파일에는 **어느 장이 그 개념의 주인인지** 적는다.

```markdown
# Dedup Decisions

- 2장: 기존 모델과의 차이를 처음 발견하는 장
- 5장: 다섯 단계 설계 이유를 설명하는 장
- 7장: 셀프 진단의 편향과 방어 장치를 설명하는 장
- 10장: 인계 문제의 본 진단을 담당하는 장
- 13장: 재진단 주기와 다음 행동 선택을 담당하는 장
```

뒤의 장에서는 필요하면 이름만 다시 부르고, 정의 전체를 반복하지 않는 식으로 사용한다.

## 7. REVIEW_RUBRIC.md 작성법

기본 템플릿을 그대로 시작해도 된다. 중요한 것은 **문장이 예뻐졌는가보다 책이 정확해졌는가**에 더 높은 점수를 주는 것이다.

추천 비중:

```text
사실·근거 규율           20
논리 일관성              18
장간 일관성              16
저자 목소리              16
중복 억제                12
독자 효용                10
문장 명료성               8
총점                     100
```

## 8. LLM 연결

Manuscript CI는 특정 AI 업체 API를 직접 요구하지 않는다.

`manuscript-ci.toml`에 두 명령을 지정한다.

```toml
[models]
mutator_command = ["./scripts/mutator-wrapper"]
evaluator_command = ["./scripts/evaluator-wrapper"]
timeout_seconds = 180
```

두 wrapper의 계약은 단순하다.

1. prompt를 stdin으로 받는다.
2. 모델에게 전달한다.
3. 모델의 JSON 응답만 stdout에 출력한다.

가능하면 **mutator와 evaluator를 서로 다른 모델**로 두는 것이 좋다. 같은 모델을 써도 되지만, 최소한 pairwise A/B 순서를 뒤집어 두 번 확인한다.

## 9. 한 장 검토

```bash
manuscript-ci review chapters/04.md
```

기본값은 원고를 수정하지 않는다. 결과 예:

```text
Baseline: 88
Iteration 1: KEEP candidate #2 → 91
Iteration 2: DISCARD all candidates
Final: 91
Applied: no
```

실제 반영하려면:

```bash
manuscript-ci review chapters/04.md --apply
```

## 10. 전권 검토

먼저 정적 검사를 권장한다.

```bash
manuscript-ci check chapters/*.md
```

이 검사는 AI 없이 다음을 찾는다.

- 서로 다른 파일에 반복된 긴 문단
- 동일 파일 안의 중복 문단
- 과도하게 반복되는 강한 단정 표현
- 빈 파일과 아주 짧은 파일

그다음 전권 의미 검토:

```bash
manuscript-ci audit-book chapters/*.md
```

각 장에서 핵심 주장·정의·수치·주기·소유 개념을 먼저 추출한 뒤, 그 요약들을 다시 비교해서 다음을 찾는다.

- 같은 용어의 정의가 장마다 달라지는가
- 동일 수치를 다른 의미로 해석하는가
- 분기/반기처럼 운영 주기가 충돌하는가
- 같은 주장을 여러 장이 모두 자기 핵심 주장처럼 설명하는가
- 앞 장에서 이미 정한 것을 뒤에서 다시 처음부터 설명하는가

`audit-book`은 보고만 하고 자동 수정하지 않는다.

## 11. 추천 작업 순서

한 권을 다시 리뷰할 때는 이 순서가 가장 안전하다.

```text
1. git branch 생성
2. WRITING_BRIEF 정리
3. DEDUP_DECISIONS 정리
4. manuscript-ci check
5. manuscript-ci audit-book
6. 문제가 큰 장부터 review
7. git diff로 저자 직접 확인
8. 최종 전권 재독
```

처음부터 전 장을 자동 수정하는 것보다 **중복·충돌을 먼저 찾고, 문제가 있는 장만 수정**하는 편이 저자 목소리를 덜 훼손한다.

## 12. 좋은 수정과 나쁜 수정

좋은 수정:

```text
원문: 이 결과는 통제가 사용량을 늘린다는 뜻이다.
수정: 이 조사에서는 준비도가 높은 조직에서 통제 역량도 함께 높았다. 원인과 결과의 방향은 이 수치만으로 알 수 없다.
```

나쁜 수정:

```text
원문: 그날 회의실 공기가 좀 서늘했다.
수정: 조직 구성원들은 복합적인 감정과 우려를 경험할 수 있다.
```

두 번째는 매끄럽지만 저자의 글을 없앤다. Manuscript CI에서는 이런 수정이 pairwise 단계에서 탈락해야 한다.

## 13. GitHub와 함께 쓰기

원고도 코드처럼 PR 단위로 고치면 좋다.

```text
main
 └─ review/ch05
      ├─ 원고 수정
      ├─ Manuscript CI report
      └─ Pull Request
```

CI에서는 자동 수정하지 말고 **문제 발견만** 하도록 권장한다. 실제 원고 반영은 사람이 PR diff를 보고 선택한다.

## 14. 기존에 쓴 책을 다시 볼 때

오래된 책은 현재 책보다 오히려 재미있는 결과가 나올 수 있다. 당시에는 자연스럽게 썼지만 지금 다시 보면:

- 반복해서 강조한 개념
- 근거보다 강하게 적은 문장
- 장마다 달라진 용어
- 나중 책에서 더 잘 정리된 생각
- 지금의 저자 목소리와 달라진 부분

이 드러난다.

다만 **과거 책을 현재의 문체로 전부 덮어쓰면 안 된다.** 그 책이 쓰인 시기의 목소리도 저자의 기록이다. `WRITING_BRIEF.md`를 책마다 따로 두는 것을 권장한다.

## 관련 문서

- [`README_KO.md`](README_KO.md) — 프로젝트 소개와 빠른 시작
- [`SKILL_KO.md`](SKILL_KO.md) — AI 에이전트용 리뷰 원칙의 한국어 설명
- [`CONTRIBUTING_KO.md`](CONTRIBUTING_KO.md) — 개발·기여 가이드
