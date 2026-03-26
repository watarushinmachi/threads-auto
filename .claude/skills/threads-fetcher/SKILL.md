---
name: threads-fetcher
description: 投稿後のパフォーマンスデータを自動取得・分析するエージェント。「データ取って」「投稿のパフォーマンスは？」「インサイト見せて」「数字を確認して」「フェッチして」など、投稿後のデータ取得・追跡に関するリクエストで使用する。
---

# Threads Fetcher

投稿後のパフォーマンスデータ（表示回数、いいね、コメント等）を定期的に取得し、蓄積するデータ収集エージェント。

## いつ使うか

- 投稿後のパフォーマンスデータを確認したいとき
- 定期的なデータ収集ルーティンとして
- threads-analyst に渡すデータを準備するとき

## ワークフロー

### Step 1: データ取得対象の特定

取得対象を決定:
- **最新の投稿**: 直近X件の投稿データ
- **特定の投稿**: 投稿IDを指定
- **期間指定**: 直近X日間の全投稿

### Step 2: Threads APIでデータ取得

`threads_api.py` の関数を使用:

**投稿一覧の取得:**
```bash
cd "合同会社Harbor/Threads運用"
source ~/.zshrc
python3 -c "
from threads_api import *
get_user_profile('アカウントキー')
posts = get_user_posts('アカウントキー', limit=25)
import json
print(json.dumps(posts, ensure_ascii=False, indent=2))
"
```

**特定の投稿のインサイト:**
```bash
python3 -c "
from threads_api import *
insight = get_post_insights('アカウントキー', '投稿ID')
import json
print(json.dumps(insight, ensure_ascii=False, indent=2))
"
```

**返信の取得:**
```bash
python3 -c "
from threads_api import *
replies = get_replies('アカウントキー', '投稿ID')
import json
print(json.dumps(replies, ensure_ascii=False, indent=2))
"
```

### Step 3: データの整形と保存

取得したデータを整形して保存:

**保存先:** `{アカウント名}/データ/fetch_{日付時刻}.json`

```json
{
  "account": "ponta",
  "fetched_at": "2026-03-27T10:00:00",
  "period": "2026-03-26 ~ 2026-03-27",
  "posts": [
    {
      "id": "投稿ID",
      "text": "投稿テキスト",
      "timestamp": "2026-03-26T10:00:00",
      "views": 1500,
      "like_count": 25,
      "reply_count": 3,
      "repost_count": 2,
      "quote_count": 1,
      "like_rate": 0.0167,
      "reply_rate": 0.002,
      "engagement_rate": 0.0207
    }
  ],
  "summary": {
    "total_posts": 5,
    "total_views": 5000,
    "avg_views": 1000,
    "total_likes": 80,
    "avg_like_rate": 0.016,
    "best_post_id": "XXX",
    "worst_post_id": "YYY"
  }
}
```

### Step 4: 前回データとの比較（差分検知）

前回のフェッチデータが存在する場合、変化を検知:

- 表示回数の増加率
- エンゲージメント率の変動
- 急激に伸びている投稿の検知（バズ兆候）
- 急激にパフォーマンスが落ちた投稿の検知（シャドウバン兆候）

### Step 5: アラート判定

以下の場合はアラートを発行:

| 状況 | アラートレベル | アクション |
|------|-------------|-----------|
| 投稿が急にバズり始めた | INFO | Discordに通知、threads-analyst に分析依頼 |
| 平均表示が前日比50%以下 | WARNING | シャドウバン可能性を threads-supervisor に報告 |
| 全投稿の表示が0に近い | CRITICAL | threads-supervisor に即座に報告、投稿停止を推奨 |
| コメントが急増 | INFO | 返信対応の必要性を通知 |

### Step 6: Discord通知

取得結果のサマリーをDiscordに送信:

```python
from discord_notify import send_to_discord
send_to_discord("アカウント_analysis", f"📊 フェッチ完了: {summary}")
```

## 定期実行

cronやスケジューラから呼び出す場合:
- 投稿後3時間: 初速データ取得
- 投稿後24時間: 最終パフォーマンス取得
- 毎朝7:00: 前日の全データ取得
