# Paper Indexer

OpenAlex, arXiv, Semantic Scholar(선택), IEEE Xplore(선택)을 모아 SQLite에 저장하고, 정적 HTML로 보여주는 로컬 우선 paper indexer입니다.

## 빠른 시작

1. Docker 설치
   - macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - 확인:

```bash
docker --version
docker compose version
```

2. 저장소 받기

```bash
git clone git@github.com:Merlinkim/whale-swim.git
cd whale-swim
```

3. `config/paper_targets.yaml` 수정
   - `global.port`: 접속 포트
   - `global.daily_schedule`: 자동 갱신 시간 (`HH:MM`)
   - `topics[*].keywords`: 검색 키워드
   - `sources.ieee_xplore.enabled`: IEEE Xplore 사용 여부

4. Docker Compose용 포트 동기화

```bash
python3 scripts/sync_compose_env.py
```

5. 실행

```bash
docker compose up -d --build
```

6. 접속

```text
http://localhost:8089
```

첫 실행은 데이터 갱신이 백그라운드로 돌아가고, 화면은 바로 열립니다.

## 설정 파일

`config/paper_targets.yaml`만 수정하면 됩니다.

예시:

```yaml
global:
  port: 8089
  daily_schedule: "06:00"

sources:
  ieee_xplore:
    enabled: false

topics:
  - name: "slam"
    keywords:
      - "SLAM"
      - "Visual SLAM"
      - "LiDAR SLAM"
```

## 자주 쓰는 명령

```bash
docker compose up -d --build
docker compose logs -f paper-indexer
docker compose run --rm paper-indexer python -m src.main --config config/paper_targets.yaml --once
python -m src.main --config config/paper_targets.yaml --once
python -m src.main --config config/paper_targets.yaml --topic slam --once
python -m src.scheduler --config config/paper_targets.yaml
```

## 포트 변경

1. `config/paper_targets.yaml`의 `global.port` 수정
2. `python3 scripts/sync_compose_env.py` 실행
3. `docker compose up -d --build` 실행

## 자동 갱신

`global.daily_schedule`에 `HH:MM` 형식으로 적으면 매일 그 시간에 자동 갱신합니다.

예:

- `"06:00"`: 매일 오전 6시
- `"13:30"`: 매일 오후 1시 30분

## 출력물

- `data/papers.db`
- `outputs/index.html`
- `outputs/latest_results.json`
- `outputs/latest_results.csv`

## 주의

- Google Scholar는 기본 비활성화입니다.
- IEEE Xplore는 기본 비활성화입니다.
- CAPTCHA, rate limit, unusual traffic가 나오면 즉시 중단합니다.
- 포트를 바꾸면 `config/paper_targets.yaml`과 `.env`를 다시 맞춰야 합니다.
