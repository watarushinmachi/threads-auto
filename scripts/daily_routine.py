#!/usr/bin/env python3
"""
毎朝ルーティン - 6エージェント連携
GitHub Actionsから呼び出される統合スクリプト
"""

import argparse
import datetime
import json
import os
import re
import sys
import time

# プロジェクトルートをパスに追加（scripts/ から実行されても threads_api をインポートできるように）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# --- アカウント別の投稿設定 ---
JST = datetime.timezone(datetime.timedelta(hours=9))
PONTA_START_DATE = datetime.date(2026, 6, 17)  # 「副業〇日目」カウントの起点（この日が1日目）
POSTS_PER_DAY = {"ponta": 3, "luna": 5}


def ponta_day_number():
    """ポンタの「副業〇日目」の日数を返す（JST基準、起点日=1日目）"""
    today_jst = datetime.datetime.now(JST).date()
    return max(1, (today_jst - PONTA_START_DATE).days + 1)


# --- ポンタ 物販ドキュメンタリーのストーリー進行 ---
# 物販商材（アフィリ）が確定したら、転機の「副業〇日目」をセットする。
# それまでは None のままで、フェーズ1(探索)〜2(停滞)を進める。
PONTA_TURNING_POINT_DAY = None   # 例: 21（副業21日目に物販商材へ出会う）
PONTA_PRODUCT = ""               # 物販アフィリ商材名（確定後に記入）


def ponta_story_stage(day):
    """副業〇日目から現在のストーリー段階を返す → (フェーズ名, 指示文)"""
    if PONTA_TURNING_POINT_DAY and day >= PONTA_TURNING_POINT_DAY:
        if day == PONTA_TURNING_POINT_DAY:
            return ("転機", f"物販系のいい商材『{PONTA_PRODUCT}』に出会った日。半信半疑だけど希望が見えた興奮を、なぜそれを選んだかの理由とともに誠実に。")
        return ("実践", f"物販（{PONTA_PRODUCT}）を実際にやってみる過程。リサーチ→仕入れ→出品→初売上…小さな成果・失敗・学びを一次情報で実況。")
    if day <= 10:
        return ("探索", "理想の副業を探して色々リサーチ・試す段階。期待と、現実とのギャップ。物販以外も含め『何が正解か分からない』迷いをリアルに。")
    return ("停滞", "良い副業がなかなか見つからず空回りする段階。挫折・葛藤・本音。でも諦めない。共感の最大の山場。まだ物販商材には出会っていない。")

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
        model="claude-sonnet-4-6",
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
        "ponta": ["AI 副業", "副業 月1万", "AI 0から", "Claude Code"],
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


def run_writer(account, analyst_result, researcher_result, fetcher_result=None):
    """Agent 4: WRITER - 投稿生成（ポンタは物販ドキュメンタリーを日々進める）"""
    print(f"\n{'='*50}")
    print(f"  Agent 4: WRITER（投稿生成）- {account}")
    print(f"{'='*50}")

    import anthropic

    # ナレッジ読み込み（ポンタ固有を先に置き、トランケートで切れないように）
    knowledge_files = {
        "ponta": [
            "ポンタ/ナレッジ/01_profile.md", "ポンタ/ナレッジ/09_story-arc.md",
            "ポンタ/ナレッジ/03_genre.md", "ポンタ/ナレッジ/05_writing.md",
            "ポンタ/ナレッジ/02_target.md", "ポンタ/ナレッジ/04_domain/物販.md",
            "共通/ナレッジ/05_writing.md", "共通/ナレッジ/07_ng-rules.md", "共通/ナレッジ/buzzwords.md",
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

    num_posts = POSTS_PER_DAY.get(account, 5)
    story_context = ""

    if account == "ponta":
        day_num = ponta_day_number()
        stage, stage_dir = ponta_story_stage(day_num)

        # 前日の投稿を引き継いで「続き」を自然につなげる（同じ話の繰り返しを防ぐ）
        prev_text = ""
        if isinstance(fetcher_result, dict):
            prev = fetcher_result.get("posts", []) or []
            prev_lines = [p.get("text", "")[:200] for p in prev if p.get("text")]
            if prev_lines:
                prev_text = "\n".join(f"- {t}" for t in prev_lines[:5])
        story_context = f"""
【ストーリー進行（最重要）】
- 今日は「副業{day_num}日目」。現在のフェーズ＝『{stage}』
- 今日の方向性：{stage_dir}
- ルール：昨日までの話と矛盾させない／同じ内容を繰り返さない／1日1歩だけ進める／段階を飛ばさない（まだ出会っていない物販商材を語らない）

【昨日の投稿（この続きとして自然につなげる。無ければ気にしない）】
{prev_text or "（データなし）"}
"""

        char_prompt = f"""【キャラクター】20代後半。借金120万をきっかけに副業を始めた"普通の初心者"。今まさに理想の副業を探して試行錯誤している最中で、まだ大きく稼げていない（成功者ぶらない）。口調は等身大・仲間目線で親しみやすい。「〜なんよ」「〜してみた」に柔らかい語尾も混ぜる。煽らない・威圧しない（インフルエンサー臭NG）。絵文字は0〜2個。
旗印は「人生逆転」ではなく『まず月1万円』。小さい目標・現在進行形・失敗や停滞の開示で共感を取る。
※これは「副業初心者が物販にたどり着くドキュメンタリー」。AIやClaude Codeの話はしない。
【1日3投稿の配分（この順番で出す）】
- 1本目＝副業日報。今日「副業{day_num}日目」のストーリーを1歩だけ進める。※冒頭の「副業{day_num}日目」という行はシステムが自動付与するので本文には書かず、その続きから書く
- 2本目＝1本目で触れた今日の出来事の深掘り（調べたこと・試した手順・数字・気づきを具体的に）
- 3本目＝本音/自己開示/横のつながり（葛藤や決意を正直に＋「一緒にやろう」）
CTAには『同じく副業0→1で踏ん張ってる人フォローして一緒にやろう』系の横のつながり訴求を混ぜる"""
    else:
        char_prompt = """【キャラクター】恋愛×星座占い。口調は優しく柔らかい。「〜だよ」「〜かも」。絵文字は🌙⭐💫✨💕を1〜3個。
具体的なアクション入り（「午後3時に彼にLINE送って」等）
必ずポジティブで締める"""

    prompt = f"""あなたはThreadsアカウントの投稿ライターです。

{char_prompt}
{story_context}
【ナレッジベース】
{all_knowledge[:12000]}

【前日の分析結果】
{analyst_result[:1500]}

【競合バズ投稿TOP3】
{researcher_text[:1500]}

以下のルールで投稿を{num_posts}本生成してください：

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
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.content[0].text

    match = re.search(r'\[[\s\S]*\]', result)
    if match:
        posts = json.loads(match.group())
    else:
        posts = [{"content": result, "technique": "不明"}]

    # ポンタは1本目の冒頭に「副業〇日目」を固定で付与（モデル任せにせず確実に）
    if account == "ponta" and posts:
        prefix = f"副業{ponta_day_number()}日目"
        body = posts[0].get("content", "")
        if not body.lstrip().startswith(prefix):
            posts[0]["content"] = f"{prefix}\n\n{body.lstrip()}"

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
        # ポンタ1本目の固定冒頭「副業〇日目」は仕様なのでNGチェックから除外
        scan_text = re.sub(r'^副業\d+日目', '', text.lstrip())
        for ng in ng_words:
            if ng in scan_text:
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
    posts = run_writer(account, analyst_result, researcher_result, fetcher_result)

    # Agent 5: POSTER
    run_poster(account, summary, analyst_result, researcher_result, posts)

    # Agent 6: SUPERVISOR
    run_supervisor(account, posts)

    print(f"\n{'#'*60}")
    print(f"  完了!")
    print(f"{'#'*60}")


if __name__ == "__main__":
    main()
