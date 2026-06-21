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
PONTA_START_DATE = datetime.date(2026, 6, 21)  # 「副業〇日目」カウントの起点（この日が1日目）
POSTS_PER_DAY = {"ponta": 3, "luna": 5}


def ponta_day_number():
    """ポンタの「副業〇日目」の日数を返す（JST基準、起点日=1日目）"""
    today_jst = datetime.datetime.now(JST).date()
    return max(1, (today_jst - PONTA_START_DATE).days + 1)


# --- ポンタ 物販ドキュメンタリーのストーリー進行 ---
# 物販商材（アフィリ）が確定したら、転機の「副業〇日目」をセットする。
# それまでは None のままで、フェーズ1(探索)〜2(停滞)を進める。
PONTA_TURNING_POINT_DAY = 14     # 副業14日目（≈2026/6/30）に物販商材『楽得物販』へ出会う転機
PONTA_PRODUCT = "楽得物販"        # 物販アフィリ商材名（利益情報配信オンラインサロン）


def ponta_story_stage(day):
    """副業〇日目から現在のストーリー段階を返す → (フェーズ名, 指示文)
    全体: AI副業に挑戦→稼げない(逆張りの芽)→情報に自己投資(楽得物販)→物販で稼ぐ→『AI副業より物販＋情報』の逆張りが実感に。"""
    if PONTA_TURNING_POINT_DAY and day >= PONTA_TURNING_POINT_DAY:
        if day == PONTA_TURNING_POINT_DAY:
            return ("転機", f"AI副業で稼げず『結局は情報を持ってる人が勝つんだ』と痛感し、物販の情報配信サロン『{PONTA_PRODUCT}』に思い切って自己投資（課金）した日。AIで遠回りしたからこその決断。半信半疑だけど期待。金額(月2万)を払う緊張も正直に。")
        return ("実践", f"『{PONTA_PRODUCT}』で配信される情報をもとに物販を実際にやる過程。リサーチ→仕入れ→出品→初売上…小さな成果や金額を正直に公開。『AI副業に振り回されたけど、ちゃんとした情報＋物販の方が自分には合ってた』という逆張りの実感がだんだん育つ。")
    if day <= 10:
        return ("探索", "みんなが『簡単に稼げる』と言うAI副業（AIツール・楽天アフィリ・note等）に、楽したい気持ちでまず挑戦してみる段階。触ってはみるが、思ったほどうまくいかない予感が出てくる。")
    return ("停滞", "AI副業をやってみたけど全然稼げない段階。『AI副業って言うほど簡単じゃない。これ結局、頭いい人とか、いい情報を持ってる人が勝つやつだ』と痛感し始める（逆張りの芽）。でもまだ答えは見つかってない。")

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


def run_learnings(account, summary, analyst_result, fetcher_result):
    """前日の実績＋分析から「学び」を抽出し、ナレッジ(10_learnings.md)に蓄積・整理する（PDCA）"""
    if account != "ponta":
        return  # 当面はポンタのみ
    print(f"\n{'='*50}")
    print(f"  LEARNINGS（学びの蓄積）- {account}")
    print(f"{'='*50}")

    path = "ポンタ/ナレッジ/10_learnings.md"
    try:
        existing = open(path, "r", encoding="utf-8").read()
    except Exception:
        existing = ""

    posts = (fetcher_result or {}).get("posts", []) if isinstance(fetcher_result, dict) else []
    post_count = (summary or {}).get("post_count", 0) if isinstance(summary, dict) else 0
    if not posts or post_count == 0:
        print("実績データがまだ無いのでスキップ（投稿が公開され数字が付いてから蓄積されます）")
        return

    import anthropic
    today = datetime.datetime.now(JST).date().isoformat()
    posts_brief = json.dumps(
        [{"text": p.get("text", "")[:120], "views": p.get("views", 0), "likes": p.get("like_count", 0),
          "replies": p.get("reply_count", 0)} for p in posts],
        ensure_ascii=False, indent=2
    )

    prompt = f"""あなたはThreads運用の学習担当です。ポンタ（副業→物販ドキュメンタリー、偏差値低め・ぼやき文体）の
「学びの蓄積ファイル」を、今日の実績をもとに更新します。

【今の蓄積ファイル（これを土台に更新）】
{existing}

【昨日の実績サマリー】
{json.dumps(summary, ensure_ascii=False)}

【昨日の各投稿（数字つき）】
{posts_brief}

【昨日のAI分析】
{(analyst_result or '')[:1500]}

ルール：
- ファイル全体を「更新後の完全版」として出力（マークダウン）。見出し構成は維持
- 各セクションは**簡潔・厳選**（「効いてること」「効かなかった/避けること」「ベスト投稿の傾向メモ」は各最大8項目まで。古い/弱い学びは削ってよい）
- 実績（表示・いいね・返信の数字）に裏打ちされた"効いた/効かない"だけを残す。憶測の水増し禁止
- 「日次ログ」セクションに「- {today}：<その日の要点1行>」を末尾に追記
- 文体や禁止事項そのものは変えない（学び＝何が伸びたかの知見だけ）
- 説明や前置きは不要。ファイルの中身だけを出力"""

    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        updated = resp.content[0].text.strip()
        # コードフェンスで囲まれていたら剥がす
        if updated.startswith("```"):
            updated = updated.split("```", 2)[1]
            if updated.startswith("markdown"):
                updated = updated[len("markdown"):]
        updated = updated.strip()
        if updated and "学びの蓄積" in updated:
            open(path, "w", encoding="utf-8").write(updated + "\n")
            print(f"✅ 学びを更新（{today}）")
        else:
            print("更新内容が不正だったのでスキップ")
    except Exception as e:
        print(f"LEARNINGS エラー: {e}")


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
            "ポンタ/ナレッジ/10_learnings.md",
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

        char_prompt = f"""【キャラクター】20代後半。借金100万をきっかけに副業を始めた"普通の初心者"。今まさに理想の副業を探して試行錯誤している最中で、まだ大きく稼げていない（成功者ぶらない）。
【知能・性格（最重要・偏差値低めに）】
- 頭が良い人・分析できる人にしない。**「楽して稼ぎたい」が本音**の、深く考えてない普通の人
- 難しそうなこと（計算・分析・専門用語）はすぐ「めんどくさい」「無理そう」「ようわからん」で避ける。きっちり数字を計算したり「順番がある」と気づいたりする賢さは出さない
- 集中力なくてすぐ脱線する。気分で動く。ちょっとだらしない、詰めが甘い
- 本音がチープでいい（「ラクして稼ぎたい」「寝てても入ってくるお金ほしい」「怪しいけど気になる」）。でも憎めない
【口調・文体（最重要）】
- 標準語。方言（「〜なんよ」等）は使わない
- SNSに慣れてない普通の人がスマホでテキトーに打った感じ。**簡単な言葉・短文・ひらがな多め**。漢字や言い回しを難しくしない。整えない、雑でいい
- 上手く書こうとしない。分析・まとめ・きれいな箇条書きにしない（賢く見える）
- 絵文字は0〜1個。煽らない。旗印は『まず月1万円』。失敗や停滞・サボった日もそのまま出す
- ※全体は「AI副業に挑戦→稼げない→物販で稼ぐ」の逆張りドキュメンタリー。AI副業を"使う側"として試す話はOK（ChatGPT触ってみた等、流行りに乗る）。ただしClaude Codeで自動化を組む等のエンジニア的なAIの話はしない（前コンセプトの名残）
【CTA】
- 「フォローして」「一緒にやろう」等の呼びかけ・勧誘は入れない。独り言・ぼやきで自然に終わる
【"読む意味"は軽くでいい】
- 各投稿に「今日やったこと・調べたこと・名前」を1つは入れる。ただし分析っぽく深掘りせず、**ざっくり・浅め**でいい（「メルカリってやつが簡単らしい」程度でOK。報酬率を計算したりしない）
【1日3投稿の配分（この順番で出す）】
- 1本目＝副業日報。今日「副業{day_num}日目」のストーリーを1歩だけ進める。※冒頭の「副業{day_num}日目」という行はシステムが自動付与するので本文には書かず、その続きから書く
- 2本目＝1本目で触れた今日の出来事の深掘り（調べたこと・試した手順・数字・気づきを具体的に）
- 3本目＝その日の本音・ぼやき（葛藤や気づきを正直に。呼びかけはしない）"""
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

"""

    if account == "ponta":
        rules = """絶対ルール:
- 200〜400文字くらい。短くて雑でいい。ぼやき
- 偏差値低め。楽して稼ぎたいのが本音。深く考えない・難しいことは避ける普通の人。分析・計算・きれいな箇条書きで賢く見せない
- 簡単な言葉、短文、ひらがな多め。上手く書こうとしない
- フォロー誘導・「一緒にやろう」等の呼びかけ/勧誘は入れない。独り言で自然に終わる
- 各投稿に「今日やったこと・調べたこと・名前」を1つは入れる（ただし浅く・ざっくりでいい。報酬率の計算とかはしない）
- 嘘や誇張はしない。まだ稼げてないものは「稼げてない」と正直に
- NGワード禁止:「稼げる」「副業」「#副業」「X」「Twitter」、本文にリンク禁止
- 3本それぞれ内容が被らないようにする"""
    else:
        rules = """絶対ルール:
- 500文字以内
- フック→本編→CTAの3部構成
- 具体性を最大化（数字、固有名詞、手順）
- 一文の濃度を凝縮
- NGワード禁止:「稼げる」「副業」「#副業」「X」「Twitter」、本文にリンク禁止
- CTAにはベネフィットを必ず含める
- 各投稿に異なるバズテクニックを使う
- バズワード50選から冒頭フックを選んで使う"""

    prompt += f"""以下のルールで投稿を{num_posts}本生成してください：

{rules}

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

    # LEARNINGS: 学びを蓄積（PDCA）→ この更新をWRITERが読む
    run_learnings(account, summary, analyst_result, fetcher_result)

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
