"""
Discord通知システム - Threads運用
分析レポートと投稿プレビューをDiscordに送信
"""

import requests
import json
import os
import datetime

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1486708739519156448/6EApx0OGzlUtLxaNjBbJUwlZ4z1hKJMy7TVarivLu55E2ZjOw7RHHVdAclXRe-7N0Kum"
DISCORD_USER_ID = "1019117141133381634"
MENTION = f"<@{DISCORD_USER_ID}>"

THREAD_IDS = {
    "ponta_analysis": "1486708915902349372",
    "ponta_posts": "1486708159161831526",
    "luna_analysis": "1486707886305443870",
    "luna_posts": "1486707973064757289",
}


def send_to_discord(thread_key: str, content: str = None, embeds: list = None):
    """Discordの指定スレッドにメッセージを送信"""
    thread_id = THREAD_IDS[thread_key]
    url = f"{DISCORD_WEBHOOK_URL}?thread_id={thread_id}"

    payload = {}
    if content:
        payload["content"] = content[:2000]
    if embeds:
        payload["embeds"] = embeds

    resp = requests.post(url, json=payload)
    if resp.status_code in (200, 204):
        print(f"Discord送信成功: {thread_key}")
    else:
        print(f"Discord送信エラー: {resp.status_code} {resp.text}")
    return resp


def send_analysis_report(account: str, summary: dict, ai_insights: str, competitor_top3: list):
    """分析レポートをDiscordに送信"""
    thread_key = f"{account}_analysis"
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    name = "ポンタ" if account == "ponta" else "ルナ"

    embed = {
        "title": f"📊 {name} デイリー分析 - {today}",
        "color": 0x3498db if account == "ponta" else 0x9b59b6,
        "fields": [
            {"name": "投稿数", "value": str(summary.get("post_count", 0)), "inline": True},
            {"name": "合計表示", "value": f"{summary.get('total_views', 0):,}", "inline": True},
            {"name": "平均表示", "value": f"{summary.get('avg_views', 0):,}", "inline": True},
            {"name": "合計いいね", "value": str(summary.get("total_likes", 0)), "inline": True},
            {"name": "合計コメント", "value": str(summary.get("total_replies", 0)), "inline": True},
            {"name": "合計リポスト", "value": str(summary.get("total_reposts", 0)), "inline": True},
        ],
    }

    if summary.get("best_post"):
        embed["fields"].append({
            "name": "🏆 ベスト投稿",
            "value": f"{summary['best_post'].get('views', 0):,}表示 | {summary['best_post'].get('likes', 0)}いいね\n```{summary['best_post'].get('text', '')[:150]}```",
            "inline": False,
        })

    if summary.get("worst_post"):
        embed["fields"].append({
            "name": "📉 ワースト投稿",
            "value": f"{summary['worst_post'].get('views', 0):,}表示 | {summary['worst_post'].get('likes', 0)}いいね\n```{summary['worst_post'].get('text', '')[:150]}```",
            "inline": False,
        })

    send_to_discord(thread_key, content=f"{MENTION} 分析レポートが届きました", embeds=[embed])

    if ai_insights:
        send_to_discord(thread_key, content=f"**🤖 AI分析・改善点**\n{ai_insights[:1900]}")

    if competitor_top3:
        comp_text = "**🔍 競合バズ投稿TOP3**\n"
        for i, p in enumerate(competitor_top3):
            comp_text += f"\n**{i+1}.** @{p.get('username', '?')} | {p.get('views', '?')}表示\n"
            comp_text += f"```{p.get('text', '')[:200]}```\n"
        send_to_discord(thread_key, content=comp_text[:2000])


def send_post_preview(account: str, posts: list):
    """投稿プレビューをDiscordに送信し、👍で承認を求める"""
    thread_key = f"{account}_posts"
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    name = "ポンタ" if account == "ponta" else "ルナ"

    send_to_discord(
        thread_key,
        content=f"{MENTION}\n**📝 {name} 本日の投稿プレビュー - {today}**\n\n👍 リアクションで投稿を承認してください\n❌ で却下（再生成します）"
    )

    for i, post in enumerate(posts):
        text = post if isinstance(post, str) else post.get("content", str(post))
        technique = post.get("technique", "") if isinstance(post, dict) else ""

        embed = {
            "title": f"投稿 {i+1}/{len(posts)}" + (f" 【{technique}】" if technique else ""),
            "description": text[:4096],
            "color": [0xe74c3c, 0xe67e22, 0xf1c40f, 0x2ecc71, 0x3498db][i % 5],
            "footer": {"text": f"文字数: {len(text)} | 👍で承認 ❌で却下"},
        }
        send_to_discord(thread_key, embeds=[embed])

    send_to_discord(
        thread_key,
        content="⬆️ 各投稿に👍で個別承認\n\n✅ **全て承認する場合はこのメッセージに👍**\n🔄 全て再生成する場合は🔄リアクション"
    )


def send_publish_result(account: str, results: list):
    """投稿完了の通知"""
    thread_key = f"{account}_posts"
    name = "ポンタ" if account == "ponta" else "ルナ"

    success = sum(1 for r in results if "id" in r)
    failed = len(results) - success

    embed = {
        "title": f"✅ {name} 投稿完了",
        "color": 0x2ecc71 if failed == 0 else 0xe74c3c,
        "fields": [
            {"name": "成功", "value": f"{success}件", "inline": True},
            {"name": "失敗", "value": f"{failed}件", "inline": True},
        ],
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    send_to_discord(thread_key, content=f"{MENTION} 投稿が完了しました", embeds=[embed])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Discord通知テスト")
    parser.add_argument("--test", choices=["ponta", "luna", "all"], help="テスト送信")
    args = parser.parse_args()

    if args.test in ("ponta", "all"):
        send_analysis_report("ponta", {
            "post_count": 3, "total_views": 150, "avg_views": 50,
            "total_likes": 5, "total_replies": 2, "total_reposts": 1,
            "best_post": {"text": "借金120万のFランインキャがAIだけで人生変えられるか試す記録、始めます", "views": 80, "likes": 3},
            "worst_post": {"text": "AIで人生変えられるか調べまくった", "views": 20, "likes": 0},
        }, "1. フックが強い投稿が伸びた\n2. 具体的な数字がある投稿の方が反応が良い\n3. CTAを毎回入れるべき", [])

        send_post_preview("ponta", [
            {"content": "借金持ちがAIで月5万稼ぐまでにやったこと全部晒す\n\n・ChatGPT無料版で記事作成\n・A8.netでアフィリンク取得\n・Threadsで毎日発信\n・noteで情報まとめて販売\n\nまだ道半ばだけど\n同じように始めたい人はフォローして一緒に頑張ろう", "technique": "再現性×大量"},
            {"content": "借金あるって言うと\n大体こう返される\n\n「自己責任でしょ」\n\nうん、知ってる\n自分が一番わかってる\n\nでもそこで終わったら\n一生このままなんよ\n\n今はAIっていう武器がある\n初期費用もいらない\nスマホ1台で始められる\n\n自己責任で始めたこの挑戦\n自己責任で成功させるわ", "technique": "自己開示×信念"},
        ])

    if args.test in ("luna", "all"):
        send_analysis_report("luna", {
            "post_count": 2, "total_views": 100, "avg_views": 50,
            "total_likes": 3, "total_replies": 1, "total_reposts": 0,
            "best_post": {"text": "今朝の12星座恋愛運、お届けするよ🌙", "views": 70, "likes": 2},
            "worst_post": {"text": "片思い中の人に、星からのメッセージ💫", "views": 30, "likes": 1},
        }, "1. 12星座まとめ投稿の方が反応が良い\n2. コメント誘発をもっと強化すべき\n3. タップ投稿の構造を取り入れる", [])

        send_post_preview("luna", [
            {"content": "【3/27の恋愛運🌙12星座別】\n今日やるべきアクション付きだよ✨\n\n♈牡羊座：午後2時頃に好きな人にLINE送って\n♉牡牛座：白い服を着ると運気UP\n♊双子座：カフェでの偶然の出会いあり\n\n↓残り9星座はこちら", "technique": "タップ投稿×大量"},
            {"content": "コメントで教えて🌙\nあなたの星座を✨\n\n明日の恋愛運を一人一人個別に占ってあげるよ💕\n\n気軽に星座をコメントしてね\n占い結果は明日の朝にお返事するよ✨", "technique": "コメント誘発"},
        ])
