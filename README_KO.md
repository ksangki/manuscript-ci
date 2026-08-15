# Manuscript CI

[English](README.md) | **한국어**

**저자의 목소리를 지키는 AI 원고 리뷰.**

Manuscript CI는 책과 장문 원고를 위한 오픈소스 AI 교정 워크플로다. 원고를 그럴듯한 ‘AI 문체’로 다시 쓰는 것이 목적이 아니다. 대신 작은 수정 후보를 만들고, 저자가 정한 규칙에 따라 평가하고, 원문과 수정안을 순서를 바꿔가며 비교한 뒤 **원문보다 확실히 나은 수정만 남긴다.**

쉽게 말하면 원고를 위한 **lint + test + code review**다.

> 우리는 당신의 책을 대신 쓰지 않는다. 고치는 동안 그 책이 당신의 책으로 남도록 지킨다.

## 왜 만들었나

대부분의 AI 글쓰기 도구는 생성과 재작성에 최적화돼 있다. 하지만 책에서 자주 생기는 문제는 조금 다르다.

- 출처가 말한 것보다 더 강한 사실처럼 바뀔 수 있다.
- 장마다 같은 용어의 정의가 조금씩 달라질 수 있다.
- 같은 주장을 표현만 바꿔 여러 번 반복할 수 있다.
- 문장 하나를 매끈하게 만들다가 저자 고유의 목소리가 사라질 수 있다.
- 한 장을 고친 뒤 다른 장과 새 모순이 생길 수 있다.
- ‘더 잘 쓴 것 같은’ 문장이 오히려 덜 정확할 수 있다.

Manuscript CI에서는 **원문이 현 챔피언(incumbent)** 이다. 수정안은 원문을 이겨야 살아남는다.

## 핵심 루프

```text
원고
  ↓
작은 수정 후보
  ↓
rubric 점수 평가
  ↓
원문 vs 수정안 pairwise 비교
  ↓
순서를 뒤집어 다시 비교
  ↓
두 번 모두 수정안이 이길 때만 KEEP
  ↓
리포트 / 선택적 반영
```

책 전체를 대상으로는 장간 중복 주장, 용어 변화, 숫자 충돌, 개념 소유권 중복, 운영 주기 불일치 등을 찾는 전권 감사(audit)도 지원한다.

## 5분 만에 시작하기

Python 3.11 이상이 필요하다.

### 방법 A — AI 에이전트 스킬로 사용

Codex, Claude Code, Gemini CLI 등 원고 저장소를 읽을 수 있는 AI 에이전트를 이미 쓰고 있다면 가장 빠른 방법이다.

`SKILL.md` 또는 한국어 설명판인 [`SKILL_KO.md`](SKILL_KO.md)의 원칙을 에이전트가 따르게 하고, 책 저장소에 아래 세 규칙 파일을 준비한 뒤 Manuscript CI 방식으로 리뷰해달라고 요청한다.

```text
WRITING_BRIEF.md
DEDUP_DECISIONS.md
REVIEW_RUBRIC.md
```

예:

```text
이 책을 Manuscript CI 방식으로 검토해줘.
원문보다 확실히 나은 수정만 남기고 저자 목소리는 보존해줘.
WRITING_BRIEF.md, DEDUP_DECISIONS.md, REVIEW_RUBRIC.md를 우선 규칙으로 사용해줘.
```

### 방법 B — CLI 설치

GitHub에서 바로 설치할 수 있다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/ksangki/manuscript-ci.git"
manuscript-ci init .
```

개발하려면 저장소를 clone한 뒤 `pip install -e .`을 사용한다.

초기화하면 다음 파일이 만들어진다.

```text
manuscript-ci.toml
WRITING_BRIEF.md
DEDUP_DECISIONS.md
REVIEW_RUBRIC.md
```

`manuscript-ci.toml`에서 사용할 LLM을 wrapper 명령으로 연결한다.

```toml
[models]
mutator_command = ["./scripts/my-mutator"]
evaluator_command = ["./scripts/my-evaluator"]
timeout_seconds = 180
```

각 wrapper는 **stdin**으로 prompt를 받고 **stdout**으로 JSON을 출력하면 된다. 그래서 코어는 특정 모델 회사에 종속되지 않는다. Claude, Codex, Gemini, Ollama, 사내 LLM Gateway 등 무엇이든 wrapper 뒤에 연결할 수 있다.

한 장 리뷰:

```bash
manuscript-ci review chapters/04.md
```

기본값은 원고를 수정하지 않는다. 검증된 수정을 실제 반영하려면:

```bash
manuscript-ci review chapters/04.md --apply
```

책 전체를 수정 없이 감사하려면:

```bash
manuscript-ci audit-book chapters/*.md
```

LLM 없이 정적 검사만 하려면:

```bash
manuscript-ci check chapters/*.md
```

## 가장 중요한 세 파일

### `WRITING_BRIEF.md`

저자의 목소리와 편집 제약을 정의한다. 독자, 문체, 용어, 근거 사용 규칙, 피해야 할 패턴, 반드시 보존해야 할 표현 등을 적는다.

예:

```markdown
- 독자: AI 전환을 실제로 추진하는 중간 리더
- 문체: 한국어 평서체 -다/-한다
- 경험담은 실제 경험만 쓴다.
- 외부 수치에서 원인을 임의로 추론하지 않는다.
- 컨설팅 보고서처럼 매끈한 문장보다 실무자 목소리를 우선한다.
- 이미 좋은 문장은 더 매끈하게 만들기 위한 이유만으로 고치지 않는다.
```

### `DEDUP_DECISIONS.md`

어느 장이 어떤 개념을 ‘소유’하는지 정한다. 책이 길어지면서 같은 개념을 여러 장에서 다시 처음처럼 설명하는 일을 막는다.

예:

```markdown
- 2장: 기존 모델과의 차이를 처음 발견하는 장
- 5장: 단계 설계 이유를 설명하는 장
- 10장: 인계 문제의 본 진단을 담당하는 장
```

### `REVIEW_RUBRIC.md`

무엇을 ‘더 좋은 원고’라고 볼지 정의한다. 보통 다음 항목을 평가한다.

- 사실·근거 규율
- 논리 일관성
- 장간 일관성
- 저자 목소리
- 중복 억제
- 독자 효용
- 지나친 매끈함 없이 명료한 문장

## 안전 기본값

Manuscript CI는 의도적으로 보수적이다.

- **기본은 읽기 전용.** 실제 수정에는 `--apply`가 필요하다.
- **정확히 일치하는 교체만 허용.** FIND 텍스트가 원고에 정확히 한 번 존재하지 않으면 mutation을 거부한다.
- **동점이면 원문 유지.** evaluator가 확신하지 못하면 원고를 바꾸지 않는다.
- **순서 편향 검사.** A/B 순서를 뒤집어 pairwise 평가를 두 번 한다.
- **Hard gate.** 사실 날조, 저자 경험 창작, 출처보다 강한 주장, 저자 목소리 훼손은 숫자 점수가 올라도 거부할 수 있다.
- **작은 수정 우선.** 한 장 전체 재작성보다 한 문장, 한 단락, 한 용어 수준의 surgical edit를 선호한다.

## 명령어

```text
manuscript-ci init [DIR]
manuscript-ci check FILE [FILE ...]
manuscript-ci review FILE [--apply] [--max-iterations N]
manuscript-ci audit-book FILE [FILE ...]
manuscript-ci prompt FILE --kind mutate|score|pairwise
```

자세한 실전 사용법은 [`GUIDE_KO.md`](GUIDE_KO.md)를 참고하면 된다.

## AI 에이전트 스킬로 쓰기

`SKILL.md`에는 모델에 종속되지 않는 리뷰 규칙이 들어 있다. 에이전트가 이 파일과 프로젝트 규칙을 먼저 읽게 한 뒤 다음처럼 요청할 수 있다.

```text
이 책을 Manuscript CI 방식으로 검토해줘.
원문보다 확실히 나은 수정만 남기고, 저자 목소리는 보존해줘.
```

스킬은 에이전트가 원고를 통째로 다시 쓰지 않고, 작은 mutation과 pairwise 판단으로 수정 여부를 결정하도록 유도한다.

한국어로 읽기 쉬운 설명판은 [`SKILL_KO.md`](SKILL_KO.md)에 있다.

## GitHub Actions

예제 workflow:

```text
examples/github-actions/manuscript-ci.yml
```

CI에서는 **자동 수정보다 report-only 모드**를 권장한다. 회귀 문제는 자동으로 찾아도 실제 원고 반영은 저자가 diff를 보고 결정하는 편이 안전하다.

## 실제 책 리뷰에서 시작됐다

Manuscript CI는 실제 한 권의 장문 원고를 전권 검토하면서 일반화됐다. 작은 수정, 명시적인 품질 기준, pairwise 판단, 장간 일관성 검사와 최종 사람 검토를 반복했다.

그 과정에서 가장 효과가 컸던 것은 문장을 ‘예쁘게’ 만드는 일이 아니었다.

- 외부 자료보다 강해진 인과 주장
- 장마다 달라진 정의
- 같은 개념을 여러 장이 소유하는 문제
- 서로 다른 장의 운영 주기 충돌
- AI가 다듬으면서 저자 목소리를 약하게 만드는 수정

같은 문제를 잡는 일이었다.

## 기존 책을 다시 리뷰할 때

오래전에 쓴 책에도 사용할 수 있다. 다만 지금의 문체로 과거 원고를 덮어쓰지 않도록 **책마다 별도의 `WRITING_BRIEF.md`를 만드는 것**을 권장한다.

추천 순서는 다음과 같다.

```text
1. WRITING_BRIEF 작성
2. DEDUP_DECISIONS 작성
3. manuscript-ci check
4. manuscript-ci audit-book
5. 문제가 큰 장부터 review
6. git diff 확인
7. 저자가 최종 전권 재독
```

## 감사의 말

Manuscript CI는 MIT 라이선스인 [`crimeacs/auto-improve`](https://github.com/crimeacs/auto-improve)의 **mutate → evaluate → pairwise keep/revert** 아이디어에서 영감을 받았다. Manuscript CI는 해당 소스를 내장하지 않고, 장문 원고 리뷰를 위해 독립적으로 구현했다.

## 기여하기

기여 방법은 [`CONTRIBUTING.md`](CONTRIBUTING.md) 또는 [`CONTRIBUTING_KO.md`](CONTRIBUTING_KO.md)를 참고하면 된다.

## 라이선스

MIT. 자세한 내용은 [LICENSE](LICENSE)를 참고한다.
