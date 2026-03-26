"""
Threads投稿自動生成システム - ポンタ｜借金120万をAIで返す男
シンスレッズ教材のバズテクニックを全て組み込んだ投稿生成スクリプト
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
【キャラクター：ポンタ】
- 借金120万円（アコム・プロミス・アイフル3社）を抱えるアラサー男
- Fラン大学卒（偏差値40）
- インキャ、彼女なし
- AIアフィリエイトで借金返済を目指している
- 毎月の返済状況をリアルに公開中
- 口調：カジュアルだけど熱量がある。「〜だよね」「〜なんよ」「マジで」などを自然に使う
- 絵文字は最小限（1投稿に0〜1個まで）
- 弱みを隠さず、でも前向き
- 同じ境遇の人に寄り添う姿勢
"""

# ============================================================
# バズテクニック定義（シンスレッズ教材ベース）
# ============================================================
BUZZ_TECHNIQUES = {
    "一次情報": {
        "description": "自分が実際に経験・発見したことを共有する",
        "instruction": "ポンタが実際にAIツールを試した結果、借金返済の進捗、アフィリエイトの成果など、自分だけのリアルな体験を投稿にする。「やってみた」「使ってみた」「結果こうだった」という形式。",
        "examples": [
            "先月AIアフィで稼いだ額を公開する",
            "実際に使って稼げたAIツールの具体名と方法",
            "借金返済の進捗報告（実額公開）"
        ]
    },
    "常識破壊": {
        "description": "一般的な常識と異なる主張をして興味を引く",
        "instruction": "「普通はこう思われてるけど、実は違う」という切り口。借金持ちだからこそ見える視点、Fランだからこその気づきなど、逆張り的な主張を論理的に展開する。",
        "examples": [
            "借金があるからこそ副業に本気になれる理由",
            "高学歴より低学歴の方がAI副業に向いてる理由",
            "貯金ゼロの方がAIで稼ぎやすい理由"
        ]
    },
    "権威性": {
        "description": "実績や経験から信頼性を示す",
        "instruction": "ポンタの権威性は「逆権威性」。借金のリアルな数字、実際の返済額、AIで稼いだ具体的な金額など、生々しい数字で信頼性を出す。",
        "examples": [
            "借金120万から○ヶ月でAIアフィ収益○万達成",
            "アコムの返済画面スクショ付きで報告",
            "3社から借りてる僕が言うから間違いない"
        ]
    },
    "ターゲット限定": {
        "description": "特定の読者に「自分のことだ」と思わせる",
        "instruction": "冒頭でターゲットを明確に限定する。「借金ある人」「Fランの人」「副業始めたいけど金がない人」「インキャで営業とか無理な人」など、ポンタと同じ境遇の人を狙い撃ち。",
        "examples": [
            "消費者金融に手を出したことある人だけ見て",
            "副業始めたいけど初期費用0円じゃないと無理な人へ",
            "コミュ障で営業系の副業が無理な人、AIがある"
        ]
    },
    "大量": {
        "description": "情報を大量に箇条書きで詰め込む",
        "instruction": "AIツールのリスト、稼ぎ方のステップ、節約術など、情報を箇条書きで大量に並べる。視認性重視、一行一情報。タイムラインで目を引く構成にする。",
        "examples": [
            "借金持ちが今すぐやるべきこと10選",
            "無料で使えるAI副業ツール7選",
            "AIアフィで月5万稼ぐまでにやったこと全部"
        ]
    },
    "再現性": {
        "description": "「自分にもできそう」と思わせる",
        "instruction": "手順を明確にし、「コピペでOK」「マネするだけ」「スマホだけ」など再現性が高いことを強調。Fランでもできた、借金持ちでもできた、という事実が最強の再現性の証明。",
        "examples": [
            "偏差値40の僕でもできたAIアフィの始め方",
            "このプロンプトコピペするだけで副業記事が書ける",
            "スマホ1台、初期費用0円で始めたAI副業の全手順"
        ]
    }
}

# ============================================================
# ファン化フォーマット（シンスレッズ教材ベース）
# ============================================================
FANIFICATION_FORMATS = {
    "信念を語る": "借金を絶対AIで返すという決意、低学歴でも人生変えられるという信念を熱く語る",
    "自己開示": "借金の具体額、Fランの苦労、インキャエピソード、彼女いない歴など弱みをさらけ出す",
    "認知的共感": "お金がない不安、学歴コンプ、将来への焦りなど、同じ境遇の人の気持ちに寄り添う",
    "仮想敵・共通の敵": "「簡単に稼げる」と煽る情報商材屋、学歴マウント取る人、借金を馬鹿にする人を敵に設定",
    "失敗の開示": "AIで失敗した経験、アフィリが全然成果出なかった時期、借金が増えた時の絶望を共有",
    "自信": "「Fランの借金持ちでも絶対できる」と断言する。迷いなく言い切る",
    "代弁": "借金ある人が言えない本音、低学歴の悔しさ、副業したいけど踏み出せない葛藤を代弁"
}

# ============================================================
# 投稿構成テンプレート
# ============================================================
POST_STRUCTURE = """
【投稿の構成ルール（フック→本編→CTA）】

■ フック（冒頭1〜3行）
- 読者の手を止めさせる
- 具体的な数字を入れる
- ターゲットを限定する場合は冒頭で

■ 本編
- 一文の濃度を最大化（余計な言葉は全て削る）
- 具体性を最大にする（抽象的な表現禁止）
- 箇条書きを活用して視認性を高める

■ CTA（締め）
- フォロー促進、いいね依頼、保存促進など
- ベネフィットを添える
- 「借金返済の過程を見届けたい人はフォロー」のような形

【絶対ルール】
- 500文字以内（Threads制限）
- 文末表現は「です・ます」禁止。体言止め、「〜だ」「〜なんよ」「〜だよね」
- 絵文字は0〜1個
- 区切り線（───）、コロン（：）は使用禁止
- 同じ語尾を3回以上連続させない
- 漢字とひらがなのバランスを意識（漢字7割ひらがな3割ではなく自然に）
- リンクは本文に貼らない（シャドウバン対策）
- 「稼げる」「副業」「#副業」は使わない（シャドウバン対策）
- 比喩表現は1投稿に1回まで
- AIっぽい堅い文章は絶対NG
"""

# ============================================================
# 投稿生成関数
# ============================================================

def generate_posts(
    num_posts: int = 10,
    topic: str = None,
    technique: str = None,
    include_fan_post: bool = True,
    debt_amount: int = 1200000,
    monthly_earnings: int = 0,
):
    """
    Threads投稿を一括生成する

    Args:
        num_posts: 生成する投稿数
        topic: 投稿のテーマ（指定しない場合はAIが選定）
        technique: 使用するバズテクニック（指定しない場合はランダム）
        include_fan_post: ファン化投稿を含めるか
        debt_amount: 現在の借金残高
        monthly_earnings: 今月のアフィ収益
    """

    client = anthropic.Anthropic()

    # テクニックの割り振り
    if technique:
        techniques_to_use = [technique] * num_posts
    else:
        buzz_keys = list(BUZZ_TECHNIQUES.keys())
        fan_keys = list(FANIFICATION_FORMATS.keys())

        techniques_to_use = []
        for i in range(num_posts):
            if include_fan_post and i % 3 == 2:
                # 3投稿に1回はファン化投稿
                techniques_to_use.append(("fan", random.choice(fan_keys)))
            else:
                techniques_to_use.append(("buzz", random.choice(buzz_keys)))

    # プロンプト構築
    technique_details = ""
    for i, tech in enumerate(techniques_to_use):
        if isinstance(tech, tuple):
            tech_type, tech_name = tech
            if tech_type == "buzz":
                info = BUZZ_TECHNIQUES[tech_name]
                technique_details += f"\n投稿{i+1}: 【バズテクニック: {tech_name}】\n{info['instruction']}\n例: {', '.join(info['examples'])}\n"
            else:
                technique_details += f"\n投稿{i+1}: 【ファン化: {tech_name}】\n{FANIFICATION_FORMATS[tech_name]}\n"
        else:
            info = BUZZ_TECHNIQUES[tech]
            technique_details += f"\n投稿{i+1}: 【バズテクニック: {tech}】\n{info['instruction']}\n"

    topic_instruction = f"\n今回のテーマ: {topic}" if topic else "\nテーマはAI活用術・AIツール紹介・借金返済に関連する内容から自由に選定してください。各投稿のテーマは被らないようにしてください。"

    current_status = f"""
【ポンタの現在の状況】
- 借金残高: {debt_amount:,}円
- 今月のAIアフィ収益: {monthly_earnings:,}円
- 日付: {datetime.date.today().strftime('%Y年%m月%d日')}
"""

    prompt = f"""あなたはThreadsの投稿を作成するプロです。
以下のキャラクター設定に基づいて、{num_posts}個の投稿を作成してください。

{CHARACTER_PROFILE}

{current_status}

{POST_STRUCTURE}

{topic_instruction}

【各投稿で使用するテクニック】
{technique_details}

【出力形式】
以下のJSON形式で出力してください。JSONのみを出力し、他のテキストは含めないでください。

{{
  "posts": [
    {{
      "id": 1,
      "technique": "使用したテクニック名",
      "theme": "投稿のテーマ",
      "content": "投稿本文（500文字以内）",
      "cta_comment": "コメント欄に投稿する内容（アフィリンク誘導文など、不要ならnull）"
    }}
  ]
}}
"""

    print(f"投稿を{num_posts}件生成中...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # JSONを抽出
    try:
        # コードブロック内のJSONを抽出
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)
    except json.JSONDecodeError:
        print("JSON解析エラー。生テキストを保存します。")
        result = {"raw_response": response_text}

    return result


def save_posts(posts_data: dict, output_dir: str = None):
    """生成した投稿をファイルに保存"""
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"posts_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {filepath}")

    # 人間が読みやすい形式でも保存
    txt_filename = f"posts_{timestamp}.txt"
    txt_filepath = os.path.join(output_dir, txt_filename)

    with open(txt_filepath, "w", encoding="utf-8") as f:
        f.write(f"=== Threads投稿 生成日時: {timestamp} ===\n\n")

        if "posts" in posts_data:
            for post in posts_data["posts"]:
                f.write(f"--- 投稿 {post['id']} ---\n")
                f.write(f"テクニック: {post['technique']}\n")
                f.write(f"テーマ: {post['theme']}\n")
                f.write(f"文字数: {len(post['content'])}文字\n\n")
                f.write(f"{post['content']}\n\n")
                if post.get("cta_comment"):
                    f.write(f"[コメント欄] {post['cta_comment']}\n")
                f.write("\n" + "=" * 50 + "\n\n")
        else:
            f.write(posts_data.get("raw_response", "エラー"))

    print(f"テキスト版保存: {txt_filepath}")
    return filepath, txt_filepath


# ============================================================
# メイン実行
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ポンタのThreads投稿自動生成")
    parser.add_argument("-n", "--num", type=int, default=10, help="生成する投稿数（デフォルト: 10）")
    parser.add_argument("-t", "--topic", type=str, default=None, help="テーマを指定")
    parser.add_argument("--technique", type=str, default=None,
                       choices=list(BUZZ_TECHNIQUES.keys()),
                       help="バズテクニックを指定")
    parser.add_argument("--debt", type=int, default=1200000, help="現在の借金残高")
    parser.add_argument("--earnings", type=int, default=0, help="今月のアフィ収益")
    parser.add_argument("--no-fan", action="store_true", help="ファン化投稿を含めない")

    args = parser.parse_args()

    result = generate_posts(
        num_posts=args.num,
        topic=args.topic,
        technique=args.technique,
        include_fan_post=not args.no_fan,
        debt_amount=args.debt,
        monthly_earnings=args.earnings,
    )

    save_posts(result)

    # 結果のプレビュー
    if "posts" in result:
        print(f"\n{'=' * 50}")
        print(f"  {len(result['posts'])}件の投稿を生成しました")
        print(f"{'=' * 50}\n")

        for post in result["posts"]:
            print(f"【{post['technique']}】{post['theme']}")
            print(f"{post['content'][:80]}...")
            print()
    else:
        print("生成結果を確認してください")
