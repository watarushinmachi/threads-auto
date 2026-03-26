#!/usr/bin/env python3
"""
毎朝ルーティン - 6エージェント連携
GitHub Actionsから呼び出される統合スクリプト
"""

import argparse
import json
import os
import sys
import time

# プロジェクトルートをパスに追加（scripts/ から実行されても threads_api をインポートできるように）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

def run_fetcher(account):
    """Agent 1: FETCHER - 前日の投稿データ取得"""
    print(f"\n{'='*50}")
    print(f"  Agent 1: FETCHER（データ取得）- {account}")
    print(f"{'='*50}")

    from threads_api import get_user_profile, analyze_posts
    try:
        get_user_profile(account)
        result = analyze_posts(account, days=1)
        return result
    except Exception as e:
        print(f"FETCHER エラー: {e}")
        return {"posts": [], "summary": {"post_count": 0, "total_views": 0, "avg_views": 0, "total_likes": 0, "total_replies": 0, "total_reposts": 0}}


def run_analyst(account, fetcher_result):
    """Agent 2: ANALYST - 前日の投稿分析"""
    print(f"\n{'='*50}")
    print(f"  Agent 2: ANALYST（分析）- {account}")
    print(f"{'='*50}")

    import anthropic

    # ナレッジ読み込み
    writing_knowledge = ""
    try:
        with open("共通/ナレッジ/05_writing.md", "r") as f:
            writing_knowledge = f.read()
    except:
        pass

    summary = fetcher_result.get("summary", {})
    posts = fetcher_result.get("posts", [])

    posts_text = json.dumps(
        [{"text": p.get("text", "")[:200], "views": p.get("views", 0), "likes": p.get("like_count", 0)} for p in posts],
        ensure_ascii=False, indent=2
    )

    prompt = f"""あなたはThreads投稿のアナリストです。

【前日の投稿データ】
{json.dumps(summary, ensure_ascii=False, indent=2)}

【各投稿】
{posts_text}

【分析基準（6つのバズテクニック）】
{writing_knowledge[:2000]}

以下を簡潔にまとめてください：
1. 各投稿のS/A/B/C/Dランク評価
2. 伸びた投稿の要因
3. 伸びなかった投稿の改善点
4. 今日の投稿で意識すべきこと3点

日本語で箇条書きで簡潔に。"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    analysis = response.content[0].text
    print(analysis)
    return analysis


def run_researcher(account):
    """Agent 3: RESEARCHER - 競合バズ投稿リサーチ"""
    print(f"\n{'='*50}")
    print(f"  Agent 3: RESEARCHER（競合リサーチ）- {account}")
    print(f"{'='*50}")

    from threads_api import get_user_profile, search_threads

    keywords = {
        "ponta": ["AI 活用", "借金返済", "Claude Code"],
        "luna": ["星座占い", "恋愛運", "タロット 恋愛"],
    }

    try:
        get_user_profile(account)
        all_results = []
        for kw in keywords.get(account, []):
            try:
                results = search_threads(account, kw, limit=5)
                all_results.extend(results)
            except Exception as e:
                print(f"検索エラー ({kw}): {e}")
            time.sleep(1)

        all_results.sort(key=lambda p: p.get("views", 0), reverse=True)
        top3 = all_results[:3]

        print(f"\nバズ投稿TOP3:")
        for i, p in enumerate(top3):
            print(f"  {i+1}. {p.get('views', '?')}表示 | @{p.get('username', '?')}")
            print(f"     {p.get('text', '')[:100]}")

        return top3
    except Exception as e:
        print(f"RESEARCHER エラー: {e}")
        return []


def run_writer(account, analyst_result, researcher_result):
    """Agent 4: WRITER - 投稿5本生成"""
    print(f"\n{'='*50}")
    print(f"  Agent 4: WRITER（投稿生成）- {account}")
    print(f"{'='*50}")

    import anthropic

    # ナレッジ読み込み
    knowledge_files = {
        "ponta": [
            "共通/ナレッジ/05_writing.md", "共通/ナレッジ/07_ng-rules.md", "共通/ナレッジ/buzzwords.md",
            "ポンタ/ナレッジ/01_profile.md", "ポンタ/ナレッジ/02_target.md", "ポンタ/ナレッジ/03_genre.md",
            "ポンタ/ナレッジ/05_writing.md", "ポンタ/ナレッジ/04_domain/AI活用術.md",
            "ポンタ/ナレッジ/04_domain/借金返済ドキュメンタリー.md",
        ],
        "luna": [
            "共通/ナレッジ/05_writing.md", "共通/ナレッジ/07_ng-rules.md", "共通/ナレッジ/buzzwords.md",
            "ルナ/ナレッジ/01_profile.md", "ルナ/ナレッジ/02_target.md", "ルナ/ナレッジ/03_genre.md",
            "ルナ/ナレッジ/05_writing.md", "ルナ/ナレッジ/04_domain/星座占い.md",
            "ルナ/ナレッジ/04_domain/恋愛心理学.md",
        ],
    }

    knowledge = {}
    for fp in knowledge_files.get(account, []):
        try:
            with open(fp, "r") as f:
                knowledge[fp] = f.read()
        except:
            pass

    all_knowledge = "\n\n---\n\n".join([f"## {k}\n{v}" for k, v in knowledge.items()])

    researcher_text = json.dumps(
        [{"username": p.get("username", ""), "text": p.get("text", "")[:200], "views": p.get("views", 0)} for p in researcher_result],
        ensure_ascii=False, indent=2
    )

    if account == "ponta":
        char_prompt = """【キャラクター】借金120万のFランインキャがAIで人生逆転する男。口調はカジュアルで熱量がある。「〜なんよ」「マジで」。絵文字は最小限（0〜2個）。
配分: AI活用術×Claude Code 3本 + 借金返済リアル 1本 + 自己開示/信念 1本
機能的価値（具体的ノウハウ・手順）を必ず含める"""
    else:
        char_prompt = """【キャラクター】恋愛×星座占い。口調は優しく柔らかい。「〜だよ」「〜かも」。絵文字は🌙⭐💫✨💕を1〜3個。
具体的なアクション入り（「午後3時に彼にLINE送って」等）
必ずポジティブで締める"""

    prompt = f"""あなたはThreadsアカウントの投稿ライターです。

{char_prompt}

【ナレッジベース】
{all_knowledge[:8000]}

【前日の分析結果】
{analyst_result[:1500]}

【競合バズ投稿TOP3】
{researcher_text[:1500]}

以下のルールで投稿を5本生成してください：

絶対ルール:
- 500文字以内
- フック→本編→CTAの3部構成
- 具体性を最大化（数字、固有名詞、手順）
- 一文の濃度を凝縮
- NGワード禁止:「稼げる」「副業」「#副業」「X」「Twitter」、本文にリンク禁止
- CTAにはベネフィットを必ず含める
- 各投稿に異なるバズテクニックを使う
- バズワード50選から冒頭フックを選んで使う

出力形式（JSON配列のみ。説明不要）:
[{{"content": "投稿本文", "technique": "テクニック名"}}]"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.content[0].text

    import re
    match = re.search(r'\[[\s\S]*\]', result)
    if match:
        posts = json.loads(match.group())
    else:
        posts = [{"content": result, "technique": "不明"}]

    for i, p in enumerate(posts):
        print(f"\n--- 投稿 {i+1} 【{p.get('technique', '')}】---")
        print(p.get("content", ""))
        print(f"文字数: {len(p.get('content', ''))}")

    return posts


def run_poster(account, summary, analyst_result, researcher_result, posts):
    """Agent 5: POSTER - Discord送信"""
    print(f"\n{'='*50}")
    print(f"  Agent 5: POSTER（Discord送信）- {account}")
    print(f"{'='*50}")

    from discord_notify import send_analysis_report, send_post_preview

    send_analysis_report(account, summary, analyst_result, researcher_result)
    send_post_preview(account, posts)
    print(f"Discord送信完了: 分析レポート + 投稿{len(posts)}本")


def run_supervisor(account, posts):
    """Agent 6: SUPERVISOR - 最終チェック"""
    print(f"\n{'='*50}")
    print(f"  Agent 6: SUPERVISOR（最終チェック）- {account}")
    print(f"{'='*50}")

    from discord_notify import send_to_discord

    ng_words = ["稼げる", "副業", "#副業", "Twitter"]
    thread_key = f"{account}_analysis"

    issues = []
    for i, p in enumerate(posts):
        text = p.get("content", "")
        if len(text) > 500:
            issues.append(f"投稿{i+1}: {len(text)}文字（500文字超過）")
        for ng in ng_words:
            if ng in text:
                issues.append(f"投稿{i+1}: NGワード「{ng}」を検知")

    if issues:
        msg = "⚠️ [SUPERVISOR] 問題を検知:\n" + "\n".join(issues)
        send_to_discord(thread_key, msg)
        print(msg)
    else:
        name = "ポンタ" if account == "ponta" else "ルナ"
        msg = f"✅ [SUPERVISOR] {name}の全エージェント正常完了。投稿{len(posts)}本がDiscordで承認待ちです。"
        send_to_discord(thread_key, msg)
        print(msg)


def main():
    parser = argparse.ArgumentParser(description="毎朝ルーティン（6エージェント連携）")
    parser.add_argument("account", choices=["ponta", "luna"], help="対象アカウント")
    args = parser.parse_args()

    account = args.account

    print(f"\n{'#'*60}")
    print(f"  毎朝ルーティン開始 - {account}")
    print(f"  {time.strftime('%Y/%m/%d %H:%M')}")
    print(f"{'#'*60}")

    # Agent 1: FETCHER
    fetcher_result = run_fetcher(account)
    if isinstance(fetcher_result, dict):
        summary = fetcher_result.get("summary", {})
    else:
        summary = {}
    # summaryがdictでない場合のフォールバック
    if not isinstance(summary, dict):
        summary = {"post_count": 0, "total_views": 0, "avg_views": 0, "total_likes": 0, "total_replies": 0, "total_reposts": 0}

    # Agent 2: ANALYST
    analyst_result = run_analyst(account, fetcher_result)

    # Agent 3: RESEARCHER
    researcher_result = run_researcher(account)

    # Agent 4: WRITER
    posts = run_writer(account, analyst_result, researcher_result)

    # Agent 5: POSTER
    run_poster(account, summary, analyst_result, researcher_result, posts)

    # Agent 6: SUPERVISOR
    run_supervisor(account, posts)

    print(f"\n{'#'*60}")
    print(f"  完了!")
    print(f"{'#'*60}")


if __name__ == "__main__":
    main()
