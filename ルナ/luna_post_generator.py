"""
Threads投稿自動生成システム - るな｜星が導く恋の処方箋
恋愛×星座占い特化アカウント - バズテクニック全実装版
"""

import anthropic
import json
import random
import datetime
import os

# ============================================================
# キャラクター設定
# ============================================================
CHARACTER_PROFILE = """
【キャラクター：るな】
- 恋愛×星座占いに特化したThreadsアカウント
- 毎朝12星座の恋愛運を届ける占い師キャラ
- 口調：優しく柔らかい。「〜だよ」「〜かも」「〜してみてね」
- 女性的で親しみやすいトーン
- 絵文字は星・月・ハート系を1〜3個使用OK（🌙⭐💫✨💕）
- スピリチュアルすぎず、でも神秘的な雰囲気
- 「当たる！」とは言わない。「星はこう言ってるよ」的なスタンス
- 恋愛の悩みに寄り添う姿勢
- 押しつけがましくない。あくまで「ヒント」を届ける
"""

# ============================================================
# 星座データ
# ============================================================
ZODIAC_SIGNS = [
    {"name": "牡羊座", "period": "3/21-4/19", "element": "火", "emoji": "♈"},
    {"name": "牡牛座", "period": "4/20-5/20", "element": "地", "emoji": "♉"},
    {"name": "双子座", "period": "5/21-6/21", "element": "風", "emoji": "♊"},
    {"name": "蟹座", "period": "6/22-7/22", "element": "水", "emoji": "♋"},
    {"name": "獅子座", "period": "7/23-8/22", "element": "火", "emoji": "♌"},
    {"name": "乙女座", "period": "8/23-9/22", "element": "地", "emoji": "♍"},
    {"name": "天秤座", "period": "9/23-10/23", "element": "風", "emoji": "♎"},
    {"name": "蠍座", "period": "10/24-11/22", "element": "水", "emoji": "♏"},
    {"name": "射手座", "period": "11/23-12/21", "element": "火", "emoji": "♐"},
    {"name": "山羊座", "period": "12/22-1/19", "element": "地", "emoji": "♑"},
    {"name": "水瓶座", "period": "1/20-2/18", "element": "風", "emoji": "♒"},
    {"name": "魚座", "period": "2/19-3/20", "element": "水", "emoji": "♓"},
]

# ============================================================
# バズテクニック（シンスレッズ教材ベース × 占い最適化）
# ============================================================
BUZZ_TECHNIQUES = """
━━━━━━━━━━━━━━━━━━━━
【必須バズテクニック - 全投稿に適用】
━━━━━━━━━━━━━━━━━━━━

■ アルゴリズムで最重要な3指標
→「投稿詳細のタップ」「プロフィールアクセス」「フォロー獲得」
この3つを引き起こす投稿設計にすること。

■ タップ投稿（アルゴリズムハック）
→ タイムラインでは途中で切れて「...」になる長さにし、続きを読むためにタップさせる
→ 途中で「↓」や「...」を使って続きがあることを示唆
→ 型1 途中で強制終了型：続きはコメント欄
→ 型2 問題解決提案型：具体的な課題と解決法をセットで提案
→ 型3 友人アドバイス型：会話形式で悩みと解決策を提示
→ ただし毎回使うと飽きられるので、5投稿中2〜3投稿で使用

■ プロフィールアクセスを促す
→ 「他の星座の運勢はプロフィールから見てね🌙」のように誘導
→ 「この人の他の投稿も見たい」と思わせる情報の出し惜しみ

■ フック→本編→CTA の3部構成（王道の型）
→ フック：冒頭1〜3行で手を止めさせる。具体的な数字、ターゲット限定が有効
→ 本編：一文の濃度を最大化。余計な言葉は全て削る。具体性MAX
→ CTA：フォロー促進、コメント誘発、保存促進をベネフィット付きで

■ 6つのバズ投稿テクニック（占い版に変換して使用）
1. 一次情報：「実際に占って出た結果」「統計的に当たりやすい時期」など占い師視点の独自情報
2. 常識破壊：「占いを信じるな」「相性が悪い方がうまくいく」など逆張り
3. 権威性：「15年占いしてきて確信したこと」「1万人鑑定してわかったこと」
4. ターゲット限定：星座名で冒頭限定「蠍座の片思い中の人だけ見て」
5. 大量：12星座ランキング、恋愛運アップ術10選、相性TOP12など箇条書き大量
6. 再現性：「今夜やるだけで恋愛運UP」「この色の服を着るだけ」など誰でもできるアクション

■ コメント誘発の仕掛け（エンゲージメント最大化）
→ 「あなたの星座をコメントで教えて。個別に占うよ🌙」
→ 「当たってたらいいね、外れてたらコメントで教えて」
→ 「気になる相手の星座をコメントしたら相性占うよ💕」

■ 占い特有の具体性ルール
→ ❌「いいことがあるかも」（抽象的すぎる）
→ ⭕「午後3時頃に意外な連絡が来るかも」（具体的）
→ ⭕「赤いリップで出かけると恋愛運UP」（行動に落とせる）
→ ⭕「夜9時以降にLINE返すと好印象」（時間が具体的）
"""

# ============================================================
# 投稿構成ルール
# ============================================================
POST_STRUCTURE = """
【投稿の構成ルール】

■ フック（冒頭1〜3行）- 手を止めさせる
→ 「片思い中の水の星座だけ見て🌙」（ターゲット限定）
→ 「今日、恋が動く星座が3つある✨」（気になる構造）
→ 「占いを信じるな。でもこれだけはやって」（常識破壊）
→ 「1万人占ってわかった。モテる星座の共通点」（権威性）

■ 本編 - 一文の濃度を最大化
→ 余計な言葉は全て削る（引き算の意識）
→ 占い結果は具体的に（時間・場所・行動を指定する）
→ 箇条書きを活用して視認性を高める
→ タップさせるために途中で切る構造を作る

■ CTA（締め）- 必ずベネフィット付き
→ 「毎朝の恋愛運を逃したくない人はフォロー🌙」
→ 「当たってたらいいねで教えてね💕」
→ 「コメントで星座教えてくれたら個別に占うよ✨」
→ 「他の星座の運勢はプロフィールから見てね🌙」

【絶対ルール】
- 500文字以内（Threads制限）
- 「100%当たる」「絶対」などの断定は避ける
- ネガティブすぎる占い結果は出さない（ポジティブ転換する）
- リンクは本文に貼らない（シャドウバン対策）
- 宗教的・カルト的な表現は絶対にNG
- 同じ語尾を3回以上連続させない
"""

# ============================================================
# 投稿生成関数
# ============================================================

def generate_daily_batch(target_date=None):
    """1日分のバズ最適化投稿をまとめて生成"""

    client = anthropic.Anthropic()

    if target_date:
        today = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        today = datetime.date.today()

    date_str = today.strftime('%Y年%m月%d日')
    weekday = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]

    zodiac_info = "【12星座データ】\n"
    for z in ZODIAC_SIGNS:
        zodiac_info += f"{z['emoji']} {z['name']}（{z['period']}）- {z['element']}のエレメント\n"

    prompt = f"""あなたはThreadsで恋愛×星座占いアカウント「るな」のバズる投稿を作成するプロです。

{CHARACTER_PROFILE}

{BUZZ_TECHNIQUES}

{POST_STRUCTURE}

今日は{date_str}（{weekday}曜日）です。

{zodiac_info}

今日1日分の投稿を5本作成してください。
各投稿で異なるバズテクニックを使い、エンゲージメントを最大化してください。

━━━━━━━━━━━━━━━━━━━━
【5本の投稿設計】
━━━━━━━━━━━━━━━━━━━━

投稿1（7:00）: 12星座の恋愛運まとめ【タップ投稿×ターゲット限定×大量】
→ 最初の6星座だけ表示、残り6星座は「↓」の先に配置してタップさせる
→ 各星座に具体的なアクション1つ必ず付ける（「午後2時にLINE」「白い服が吉」など）
→ CTAでフォロー促進

投稿2（10:00）: タロット×ターゲット限定【タップ投稿×一次情報】
→ 「片思い中の○○座だけ見て」で冒頭限定
→ タロットカードの結果を提示、途中で「...」で切ってタップさせる
→ 具体的な行動アドバイス付き

投稿3（13:00）: 常識破壊×恋愛占い【常識破壊×権威性】
→ 「占いを信じるな」「相性悪い方がうまくいく」など意外な切り口
→ でも論理的な根拠を示して納得させる
→ プロフィールアクセスを促す締め

投稿4（18:00）: 相性ランキング【大量×プロフアクセス誘導】
→ 「今夜の相性ランキングTOP12」を箇条書きで一気に
→ 視認性高く、タイムラインで目を引く構成
→ 「あなたの組み合わせは？」でコメント誘発

投稿5（21:00）: コメント誘発特化【再現性×コメント最大化】
→ 「コメントで星座教えて。明日の恋愛運を個別に占うよ🌙」
→ コメントしたくなる仕掛け（個別対応の約束）
→ 明日の投稿への期待感を作る

【重要】
- 5投稿全てのテーマ・切り口が被らないこと
- 毎回異なるバズテクニックを使うこと
- 占いの具体性を最大化すること（抽象的な占いは絶対NG）
- 各投稿500文字以内

【出力形式】JSONのみ出力してください。
{{
  "date": "{date_str}",
  "weekday": "{weekday}",
  "posts": [
    {{
      "id": 1,
      "scheduled_time": "7:00",
      "technique": "使用したバズテクニック",
      "content": "投稿本文（500文字以内）",
      "cta_comment": "コメント欄に投稿する内容（あれば、なければnull）"
    }}
  ]
}}
"""

    print(f"{date_str}（{weekday}）のバズ投稿を生成中...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)
    except json.JSONDecodeError:
        result = {"raw_response": response_text}

    return result


def generate_comment_reply(commenter_sign: str, question: str = "明日の恋愛運"):
    """コメントへの個別占い返信を生成"""

    client = anthropic.Anthropic()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y年%m月%d日')

    prompt = f"""あなたは恋愛占いアカウント「るな」です。

{CHARACTER_PROFILE}

コメントで「{commenter_sign}」と教えてくれた人に、{question}を個別に占って返信してください。

【ルール】
- 150文字以内（返信は短く）
- 具体的なアドバイス1つ必ず入れる
- 温かく親しみやすいトーン
- 絵文字は1〜2個
- 「また明日の朝もチェックしてね🌙」で締める

返信テキストのみ出力してください。
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def generate_weekly_special():
    """週1回の特別投稿（バズ狙い大型投稿）"""

    client = anthropic.Anthropic()
    today = datetime.date.today()
    date_str = today.strftime('%Y年%m月%d日')

    prompt = f"""あなたはThreadsで恋愛×星座占いアカウント「るな」のバズる投稿を作成するプロです。

{CHARACTER_PROFILE}

{BUZZ_TECHNIQUES}

{POST_STRUCTURE}

今日は{date_str}です。

週1回の特別バズ投稿を2本作成してください。
通常投稿よりも拡散力が高い投稿を狙います。

【特別投稿1：保存されやすい大量情報投稿】
テーマ例：
- 「12星座別・モテるLINEの返し方」
- 「星座別・好きな人にとる態度まとめ」
- 「星座別・告白が成功しやすい場所」
→ 12星座全部を網羅した、保存したくなる情報を大量に
→ 視認性重視、箇条書き

【特別投稿2：ストーリー性のあるファン化投稿】
テーマ例：
- 「占いを始めたきっかけ」
- 「一番印象に残った鑑定の話」
- 「星座占いで恋愛が変わった人の実話」
→ 物語形式で感情を動かす
→ 自己開示、共感を誘う

【出力形式】JSONのみ
{{
  "posts": [
    {{
      "id": 1,
      "technique": "使用テクニック",
      "content": "投稿本文（500文字以内）",
      "cta_comment": "コメント欄テキスト"
    }}
  ]
}}
"""

    print("週間特別バズ投稿を生成中...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        result = json.loads(json_str)
    except json.JSONDecodeError:
        result = {"raw_response": response_text}

    return result


def save_posts(posts_data: dict, output_dir: str = None):
    """生成した投稿をファイルに保存"""
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"luna_posts_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {filepath}")

    # テキスト版
    txt_filename = f"luna_posts_{timestamp}.txt"
    txt_filepath = os.path.join(output_dir, txt_filename)

    with open(txt_filepath, "w", encoding="utf-8") as f:
        f.write(f"=== るな バズ投稿 生成日時: {timestamp} ===\n\n")

        if "posts" in posts_data:
            for post in posts_data["posts"]:
                f.write(f"--- 投稿 {post['id']} ---\n")
                if 'scheduled_time' in post:
                    f.write(f"投稿時間: {post['scheduled_time']}\n")
                if 'technique' in post:
                    f.write(f"テクニック: {post['technique']}\n")
                f.write(f"文字数: {len(post['content'])}文字\n\n")
                f.write(f"{post['content']}\n\n")
                if post.get("cta_comment"):
                    f.write(f"[コメント欄] {post['cta_comment']}\n")
                f.write(f"\n{'=' * 50}\n\n")
        else:
            f.write(posts_data.get("raw_response", "エラー"))

    print(f"テキスト版保存: {txt_filepath}")
    return filepath, txt_filepath


# ============================================================
# メイン実行
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="るなの恋愛占いバズ投稿自動生成")
    parser.add_argument("--daily", action="store_true", help="1日分のバズ投稿を生成")
    parser.add_argument("--weekly", action="store_true", help="週間特別バズ投稿を生成")
    parser.add_argument("--reply", type=str, default=None,
                       help="コメント返信を生成（星座名を指定。例: 蠍座）")
    parser.add_argument("--date", type=str, default=None, help="対象日（YYYY-MM-DD）")

    args = parser.parse_args()

    if args.reply:
        reply = generate_comment_reply(args.reply)
        print(f"\n返信文：\n{reply}")
    elif args.weekly:
        result = generate_weekly_special()
        save_posts(result)
    else:
        result = generate_daily_batch(target_date=args.date)
        save_posts(result)

    if not args.reply and "posts" in result:
        print(f"\n{'=' * 50}")
        print(f"  {len(result['posts'])}件のバズ投稿を生成しました")
        print(f"{'=' * 50}\n")

        for post in result["posts"]:
            time_str = f"[{post.get('scheduled_time', '')}] " if 'scheduled_time' in post else ""
            tech_str = f"【{post.get('technique', '')}】" if 'technique' in post else ""
            print(f"{time_str}{tech_str}")
            print(f"{post['content'][:80]}...")
            print()
