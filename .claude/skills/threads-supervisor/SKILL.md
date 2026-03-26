---
name: threads-supervisor
description: 5つのThreadsエージェント（researcher, analyst, writer, poster, fetcher）を監視・統括するスーパーバイザー。「全体の状態を確認して」「問題ないかチェックして」「自動運用を開始して」「ルナの1日ルーティンを回して」「システムの状態は？」「安全確認して」など、エージェント全体の監視・統括・自動運用フロー実行で使用する。凍結の可能性がある場合はシステムを停止する。
---

# Threads Supervisor

5つのエージェントスキル（researcher, analyst, writer, poster, fetcher）が正常に動作しているかを監視し、問題発生時は原因特定・改善を行うスーパーバイザーエージェント。

## いつ使うか

- 自動運用フローを一括実行するとき
- エージェントの動作状態を確認したいとき
- 問題が発生して原因特定が必要なとき
- 凍結リスクの判断が必要なとき

## 監視対象

| エージェント | 役割 | チェック項目 |
|------------|------|------------|
| researcher | バズ投稿リサーチ | API接続、検索結果の件数 |
| analyst | 過去投稿分析 | データ取得、分析精度 |
| writer | 投稿生成 | NGワード、文字数、品質 |
| poster | 投稿実行 | API認証、投稿成功率 |
| fetcher | データ取得 | API接続、データ整合性 |

## ワークフロー

### 1. ヘルスチェック

全エージェントの動作状態を確認:

```bash
cd "合同会社Harbor/Threads運用"
source ~/.zshrc

# APIトークン確認
python3 -c "
import os
tokens = {
    'THREADS_PONTA_TOKEN': bool(os.environ.get('THREADS_PONTA_TOKEN')),
    'THREADS_LUNA_TOKEN': bool(os.environ.get('THREADS_LUNA_TOKEN')),
    'ANTHROPIC_API_KEY': bool(os.environ.get('ANTHROPIC_API_KEY')),
    'DISCORD_BOT_TOKEN': bool(os.environ.get('DISCORD_BOT_TOKEN')),
}
for k, v in tokens.items():
    status = '✅' if v else '❌'
    print(f'{status} {k}')
"

# Threads API疎通確認
python3 -c "
from threads_api import get_user_profile
try:
    result = get_user_profile('ponta')
    print('✅ ポンタ API接続OK' if 'id' in result else '❌ ポンタ API接続NG')
except Exception as e:
    print(f'❌ ポンタ API接続エラー: {e}')
try:
    result = get_user_profile('luna')
    print('✅ ルナ API接続OK' if 'id' in result else '❌ ルナ API接続NG')
except Exception as e:
    print(f'❌ ルナ API接続エラー: {e}')
"
```

### 2. 凍結リスク判定

以下の指標で凍結リスクを判定:

| 指標 | 正常 | 警告 | 危険（即停止） |
|------|------|------|-------------|
| 投稿の表示回数 | 平常通り | 前日比50%以下 | ほぼ0 |
| APIエラー率 | 0% | 10%以上 | 50%以上 |
| 連続エラー | 0回 | 2回 | 3回以上 |
| スパム判定 | なし | 1回 | 2回以上 |

**危険判定時のアクション:**
1. 即座に全投稿を停止
2. Discordに緊急通知を送信
3. ユーザーに手動確認を依頼
4. 最後の投稿内容を確認し、原因を推定

```python
from discord_notify import send_to_discord, MENTION
send_to_discord("ponta_analysis",
    f"🚨 {MENTION} **緊急: 凍結リスク検知**\n\n"
    f"アカウント: ポンタ\n"
    f"原因: {原因}\n"
    f"対応: 全投稿を停止しました。手動で確認してください。"
)
```

### 3. 自動運用フロー（ルナ1日ルーティン）

ルナの1日の自動運用を統括する:

```
07:00 - [fetcher] 前日のデータ取得
      ↓
07:05 - [analyst] 前日の投稿分析
      ↓
07:10 - [researcher] 競合バズ投稿リサーチ
      ↓
07:15 - [writer] 本日の投稿5本生成（分析結果を反映）
      ↓
07:20 - [poster] Discord にプレビュー送信
      ↓
(ユーザー承認待ち or 自動承認)
      ↓
指定時刻 - [poster] 投稿実行（7:00/10:00/13:00/18:00/21:00）
      ↓
各投稿後3h - [fetcher] 初速データ取得
      ↓
翌朝 - ループ
```

### 4. 問題発生時の対処フロー

```
問題検知
  ↓
原因の切り分け
  ├── APIエラー → トークン確認 → 期限切れならユーザーに通知
  ├── スパム判定 → 投稿内容のNGワードチェック → 修正して再投稿
  ├── 表示激減 → シャドウバン疑い → 投稿停止 → 24h待機
  ├── 投稿失敗 → ネットワーク/API障害 → リトライ（最大3回）
  └── 生成品質低下 → ナレッジ更新が必要 → analyst にフィードバック
  ↓
対処実行
  ↓
結果をDiscordに報告
```

### 5. ステータスレポート

```markdown
# システムステータス - {日付時刻}

## エージェント状態
| エージェント | 状態 | 最終実行 | 備考 |
|------------|------|---------|------|
| researcher | ✅ 正常 | 03/27 07:10 | 検索15件取得 |
| analyst    | ✅ 正常 | 03/27 07:05 | 5投稿分析済 |
| writer     | ✅ 正常 | 03/27 07:15 | 5投稿生成済 |
| poster     | ✅ 正常 | 03/27 10:00 | 2/5投稿公開済 |
| fetcher    | ✅ 正常 | 03/27 07:00 | 前日データ取得済 |

## アカウント状態
| アカウント | 凍結リスク | 今日の投稿 | 平均表示 |
|----------|----------|----------|---------|
| ポンタ    | 🟢 低    | 2/5完了   | 500     |
| ルナ      | 🟢 低    | 3/5完了   | 300     |

## アラート
- なし
```

## 緊急停止コマンド

ユーザーが「停止」「止めて」「ストップ」と言った場合、全エージェントの実行を即座に停止する。
