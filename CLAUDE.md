# Threads運用プロジェクト

## 概要
シンスレッズ教材をベースにしたThreadsアカウント運用プロジェクト。
2アカウント体制で運用し、ポンタアカウントで成果を報告するドキュメンタリー戦略。

## ディレクトリ構成

```
Threads運用/
├── CLAUDE.md                          ← このファイル
├── .claude/skills/                    ← スキル（6エージェント + ツール）
│   ├── threads-researcher/            ← バズ投稿リサーチ
│   ├── threads-analyst/               ← 過去投稿分析・改善提案
│   ├── threads-writer/                ← 投稿生成（ライティング）
│   ├── threads-poster/                ← Threads API投稿実行
│   ├── threads-fetcher/               ← 投稿後データ自動取得
│   ├── threads-supervisor/            ← 5エージェント監視・凍結時停止
│   └── skill-creator/                 ← スキル作成・改善ツール
├── 共通/ナレッジ/                      ← 全アカウント共通のナレッジ
│   ├── 05_writing.md                  ← 書き方の共通ルール・テクニック・ファン化
│   ├── 07_ng-rules.md                 ← シャドウバン・凍結ルール
│   ├── algorithm.md                   ← アルゴリズム・CTA・PDCA・Threads仕様
│   ├── buzzwords.md                   ← バズワード50選（フック集）
│   ├── education.md                   ← 教育の6種類（商品販売準備）
│   ├── affiliate.md                   ← アフィリエイト攻略・ASP一覧
│   ├── launch.md                      ← プロダクトローンチ戦略
│   └── product_ideas.md              ← 商品アイデア20選
├── ポンタ/
│   ├── ナレッジ/                       ← ポンタ固有のナレッジ
│   │   ├── 01_profile.md              ← このアカウントは誰か
│   │   ├── 02_target.md               ← 誰に向けて書くか
│   │   ├── 03_genre.md                ← どんなジャンルか
│   │   ├── 04_domain/                 ← 専門知識
│   │   │   ├── AI活用術.md
│   │   │   └── 借金返済ドキュメンタリー.md
│   │   ├── 05_writing.md              ← ポンタ固有の口調・キャラ
│   │   ├── 06_references.md           ← 参考にする投稿
│   │   └── 08_strategy.md             ← 戦略
│   └── threads_post_generator.py
├── ルナ/
│   ├── ナレッジ/                       ← ルナ固有のナレッジ
│   │   ├── 01_profile.md              ← このアカウントは誰か
│   │   ├── 02_target.md               ← 誰に向けて書くか
│   │   ├── 03_genre.md                ← どんなジャンルか
│   │   ├── 04_domain/                 ← 専門知識
│   │   │   ├── 星座占い.md
│   │   │   └── 恋愛心理学.md
│   │   ├── 05_writing.md              ← ルナ固有の口調・キャラ
│   │   ├── 06_references.md           ← 参考にする投稿
│   │   └── 08_strategy.md             ← 戦略
│   └── luna_post_generator.py
├── threads_api.py                     ← Threads API自動化
├── discord_bot.py                     ← Discord Bot（承認→自動投稿）
├── discord_notify.py                  ← Discord Webhook通知
└── 画像/                              ← 投稿用画像
```

## ナレッジの読み方

投稿生成・分析時は以下の順で読む：
1. `共通/ナレッジ/` → 共通テクニック・ルール
2. `{アカウント名}/ナレッジ/` → アカウント固有の設定

## アカウント構成

### ポンタ（@ponta_ai_life）
- コンセプト：副業初心者が物販にたどり着くドキュメンタリー（理想の副業探す→停滞→物販の商材に出会う→少しずつ稼ぐ）。借金100万は"始めたきっかけ"の背景
- 1日3投稿：1本目=副業日報（冒頭「副業〇日目」固定）/ 2本目=過程の深掘り / 3本目=本音・横のつながり
- ストーリー進行は ポンタ/ナレッジ/09_story-arc.md と scripts/daily_routine.py の PONTA_TURNING_POINT_DAY / PONTA_PRODUCT で管理（物販商材が決まったら転機日をセット）
- 設計の型の元ネタ：X「たろう @XS1bR7pLDg65025」（→ ポンタ/ナレッジ/06_references.md）
- 運用：手動＋AI生成

### ルナ（@runa29677）
- コンセプト：星が導く恋の処方箋（恋愛×星座占い）
- 役割：自動運用アカウント。マネタイズの実験台
- 投稿：毎日5投稿（7:00/10:00/13:00/18:00/21:00）
- 運用：AI全自動生成
- 注意：ポンタとは別端末でログイン（連鎖凍結防止）

## 投稿生成スクリプト

### ポンタ
```bash
python3 ポンタ/threads_post_generator.py -n 10 --debt 1200000 --earnings 0
python3 ポンタ/threads_post_generator.py -n 5 -t "AIツール紹介"
python3 ポンタ/threads_post_generator.py -n 5 --technique 常識破壊
```

### ルナ
```bash
python3 ルナ/luna_post_generator.py --daily
python3 ルナ/luna_post_generator.py --weekly
python3 ルナ/luna_post_generator.py --reply 蠍座
python3 ルナ/luna_post_generator.py --daily --date 2026-03-27
```

## API設定
- Anthropic API Key: 環境変数 ANTHROPIC_API_KEY（~/.zshrc）
- Discord Bot Token: 環境変数 DISCORD_BOT_TOKEN（~/.zshrc）
- Threads API Token: 環境変数 THREADS_PONTA_TOKEN / THREADS_LUNA_TOKEN（~/.zshrc）

## 3周年イベント（8/22(土) 東京・高田馬場・2,000人規模）

**フル議事録・ネクストアクション → `共通/ミーティング/2026-07-02_3周年定例MTG.md`**
（3周年・イベント・集客・特典・ウェビナー連携について聞かれたら、まずこのファイルを読むこと）

- **告知スライド（HTML 3パターン）→ `slides/shift-ai-3rd-anniversary/`**（index.htmlから比較。要差替：◯次募集/締切/特典/申込QR）
- 集客の基本方針（西田さん指摘）：①集客はファネルで設計（ターゲット×タイミング×施策）②数値で仮説検証（LP/開封/登録率/参加率）③施策連携（ウェビナー/フロント/特典/月刊/YouTubeライブ）
- 直近の勝負は7月頭〜中旬。お盆前に決着、地方の人から先に確保。
- 主要期限：7/3フロント連携MTG（具体案持参）／7/4月刊ウィーク2／7/8 YouTubeライブ1回目／8/1ごろ2回目（前倒し検討）／8/22本番。
