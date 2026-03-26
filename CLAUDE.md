# Threads運用プロジェクト

## 概要
シンスレッズ教材をベースにしたThreadsアカウント運用プロジェクト。
2アカウント体制で運用し、ポンタアカウントで成果を報告するドキュメンタリー戦略。

## アカウント構成

### ポンタ（@ponta_ai_life）
- コンセプト：借金120万のFランインキャがAIだけで人生逆転する全記録
- 役割：メインアカウント。リアルドキュメンタリー＋成果報告
- 投稿配分：AI活用術5割 / 借金返済リアル報告3割 / 実績報告2割
- 運用：手動＋AI生成
- スクリプト：`ポンタ/threads_post_generator.py`

### ルナ（@runa29677）
- コンセプト：星が導く恋の処方箋（恋愛×星座占い）
- 役割：自動運用アカウント。マネタイズの実験台
- 投稿：毎日5投稿（7:00/10:00/13:00/18:00/21:00）
- 運用：AI全自動生成
- スクリプト：`ルナ/luna_post_generator.py`
- 注意：ポンタとは別端末でログイン（連鎖凍結防止）

## ナレッジベース
`ナレッジ/` ディレクトリに教材のエッセンスを格納：
- `01_アカウント設計.md` - ジャンル選定、コンセプト設計、プロフィール設計
- `02_投稿テクニック.md` - 6つのバズテクニック、王道の型、アルゴリズムハック
- `03_ファン化術.md` - 7つのファン化フォーマット
- `04_マネタイズ.md` - 商品販売、アフィリエイト、導線設計
- `05_アルゴリズム対策.md` - アルゴリズム、シャドウバン対策、CTA

## スラッシュコマンド
- `/threads-profile` - プロフィール設計（ジャンル選定〜プロフ文まで）
- `/threads-post` - バズ投稿作成（テクニック全実装）
- `/threads-strategy` - 戦略・マネタイズ相談

## 投稿生成スクリプト

### ポンタ
```bash
# 10本生成
python3 ポンタ/threads_post_generator.py -n 10 --debt 1200000 --earnings 0
# テーマ指定
python3 ポンタ/threads_post_generator.py -n 5 -t "AIツール紹介"
# テクニック指定
python3 ポンタ/threads_post_generator.py -n 5 --technique 常識破壊
```

### ルナ
```bash
# 1日分のバズ投稿5本
python3 ルナ/luna_post_generator.py --daily
# 週間特別投稿
python3 ルナ/luna_post_generator.py --weekly
# コメント返信生成
python3 ルナ/luna_post_generator.py --reply 蠍座
# 日付指定
python3 ルナ/luna_post_generator.py --daily --date 2026-03-27
```

## API設定
- Anthropic API Key: 環境変数 ANTHROPIC_API_KEY に設定済み（~/.zshrc）

## シャドウバン対策（全アカウント共通）
- 本文にリンク貼らない（コメント欄に）
- 「稼げる」「副業」「#副業」は使わない
- 「X」「Twitter」という単語は使わない
- アダルト系・政治系の投稿は避ける
- 同一端末で複数アカウントにログインしない
