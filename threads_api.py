"""
Threads API 自動化システム
- 投稿の自動公開
- インサイト（分析データ）取得
- キーワード検索（競合リサーチ）
- 返信の取得・管理
"""

import requests
import json
import time
import os
import datetime

THREADS_API_BASE = "https://graph.threads.net/v1.0"

# ============================================================
# アカウント設定
# ============================================================
ACCOUNTS = {
    "ponta": {
        "name": "ポンタ",
        "token": os.environ.get("THREADS_PONTA_TOKEN", ""),
        "user_id": None,  # 初回実行時に自動取得
    },
    "luna": {
        "name": "ルナ",
        "token": os.environ.get("THREADS_LUNA_TOKEN", ""),
        "user_id": None,
    },
}


# ============================================================
# ユーザー情報取得
# ============================================================
def get_user_profile(account_key: str) -> dict:
    """ユーザーのプロフィール情報を取得"""
    token = ACCOUNTS[account_key]["token"]
    url = f"{THREADS_API_BASE}/me"
    params = {
        "fields": "id,username,threads_profile_picture_url,threads_biography",
        "access_token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "id" in data:
        ACCOUNTS[account_key]["user_id"] = data["id"]
        print(f"[{ACCOUNTS[account_key]['name']}] ユーザーID: {data['id']}, @{data.get('username', '?')}")

    return data


# ============================================================
# 投稿の公開
# ============================================================
def publish_post(account_key: str, text: str, image_url: str = None) -> dict:
    """
    Threadsに投稿を公開する（2ステップ）
    1. メディアコンテナを作成
    2. コンテナを公開
    """
    token = ACCOUNTS[account_key]["token"]
    user_id = ACCOUNTS[account_key]["user_id"]

    if not user_id:
        get_user_profile(account_key)
        user_id = ACCOUNTS[account_key]["user_id"]

    # Step 1: メディアコンテナ作成
    create_url = f"{THREADS_API_BASE}/{user_id}/threads"
    params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": token,
    }
    if image_url:
        params["media_type"] = "IMAGE"
        params["image_url"] = image_url

    resp = requests.post(create_url, params=params)
    container = resp.json()

    if "id" not in container:
        print(f"エラー（コンテナ作成）: {container}")
        return container

    container_id = container["id"]
    print(f"コンテナ作成: {container_id}")

    # 少し待つ（Metaの処理時間）
    time.sleep(3)

    # Step 2: 公開
    publish_url = f"{THREADS_API_BASE}/{user_id}/threads_publish"
    params = {
        "creation_id": container_id,
        "access_token": token,
    }
    resp = requests.post(publish_url, params=params)
    result = resp.json()

    if "id" in result:
        print(f"[{ACCOUNTS[account_key]['name']}] 投稿公開成功! ID: {result['id']}")
    else:
        print(f"エラー（公開）: {result}")

    return result


def publish_multiple_posts(account_key: str, posts: list, interval_minutes: int = 60):
    """複数の投稿を時間間隔を空けて公開"""
    results = []
    for i, post in enumerate(posts):
        text = post if isinstance(post, str) else post.get("content", "")
        print(f"\n--- 投稿 {i+1}/{len(posts)} ---")
        result = publish_post(account_key, text)
        results.append(result)

        if i < len(posts) - 1:
            wait_seconds = interval_minutes * 60
            print(f"次の投稿まで{interval_minutes}分待機...")
            time.sleep(wait_seconds)

    return results


# ============================================================
# インサイト（分析）取得
# ============================================================
def get_post_insights(account_key: str, post_id: str) -> dict:
    """特定の投稿のインサイトを取得"""
    token = ACCOUNTS[account_key]["token"]
    url = f"{THREADS_API_BASE}/{post_id}"
    params = {
        "fields": "id,text,timestamp,like_count,reply_count,repost_count,quote_count,views",
        "access_token": token,
    }
    resp = requests.get(url, params=params)
    return resp.json()


def get_user_posts(account_key: str, limit: int = 25) -> list:
    """ユーザーの投稿一覧を取得"""
    token = ACCOUNTS[account_key]["token"]
    user_id = ACCOUNTS[account_key]["user_id"]

    if not user_id:
        get_user_profile(account_key)
        user_id = ACCOUNTS[account_key]["user_id"]

    url = f"{THREADS_API_BASE}/{user_id}/threads"
    params = {
        "fields": "id,text,timestamp,like_count,reply_count,repost_count,quote_count,views",
        "limit": limit,
        "access_token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    return data.get("data", [])


def analyze_posts(account_key: str, days: int = 1) -> dict:
    """直近の投稿を分析して改善点を抽出"""
    posts = get_user_posts(account_key, limit=50)

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    recent_posts = []

    for post in posts:
        ts = post.get("timestamp", "")
        if ts:
            post_time = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if post_time >= cutoff:
                recent_posts.append(post)

    if not recent_posts:
        print(f"直近{days}日間の投稿が見つかりません")
        return {"posts": [], "summary": "投稿なし"}

    # 分析サマリー
    total_views = sum(p.get("views", 0) for p in recent_posts)
    total_likes = sum(p.get("like_count", 0) for p in recent_posts)
    total_replies = sum(p.get("reply_count", 0) for p in recent_posts)
    total_reposts = sum(p.get("repost_count", 0) for p in recent_posts)

    best_post = max(recent_posts, key=lambda p: p.get("views", 0))
    worst_post = min(recent_posts, key=lambda p: p.get("views", 0))

    summary = {
        "period": f"直近{days}日間",
        "post_count": len(recent_posts),
        "total_views": total_views,
        "avg_views": total_views // len(recent_posts) if recent_posts else 0,
        "total_likes": total_likes,
        "total_replies": total_replies,
        "total_reposts": total_reposts,
        "best_post": {
            "text": best_post.get("text", "")[:100],
            "views": best_post.get("views", 0),
            "likes": best_post.get("like_count", 0),
        },
        "worst_post": {
            "text": worst_post.get("text", "")[:100],
            "views": worst_post.get("views", 0),
            "likes": worst_post.get("like_count", 0),
        },
    }

    print(f"\n{'='*50}")
    print(f"[{ACCOUNTS[account_key]['name']}] {summary['period']}の分析")
    print(f"{'='*50}")
    print(f"投稿数: {summary['post_count']}")
    print(f"合計表示: {summary['total_views']:,}")
    print(f"平均表示: {summary['avg_views']:,}")
    print(f"合計いいね: {summary['total_likes']}")
    print(f"合計コメント: {summary['total_replies']}")
    print(f"合計リポスト: {summary['total_reposts']}")
    print(f"\nベスト投稿 ({summary['best_post']['views']:,}表示):")
    print(f"  {summary['best_post']['text']}")
    print(f"\nワースト投稿 ({summary['worst_post']['views']:,}表示):")
    print(f"  {summary['worst_post']['text']}")

    return {"posts": recent_posts, "summary": summary}


# ============================================================
# キーワード検索（競合リサーチ）
# ============================================================
def search_threads(account_key: str, keyword: str, limit: int = 10) -> list:
    """キーワードで投稿を検索（競合リサーチ用）"""
    token = ACCOUNTS[account_key]["token"]
    user_id = ACCOUNTS[account_key]["user_id"]

    if not user_id:
        get_user_profile(account_key)
        user_id = ACCOUNTS[account_key]["user_id"]

    url = f"{THREADS_API_BASE}/{user_id}/threads_keyword_search"
    params = {
        "q": keyword,
        "fields": "id,text,timestamp,like_count,reply_count,repost_count,quote_count,views,username",
        "limit": limit,
        "access_token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    results = data.get("data", [])

    print(f"\n「{keyword}」の検索結果: {len(results)}件")
    for i, post in enumerate(results):
        views = post.get("views", "?")
        likes = post.get("like_count", 0)
        username = post.get("username", "?")
        text = post.get("text", "")[:80]
        print(f"  {i+1}. @{username} | {views}表示 | {likes}いいね")
        print(f"     {text}")

    return results


# ============================================================
# 返信の取得
# ============================================================
def get_replies(account_key: str, post_id: str) -> list:
    """特定の投稿への返信を取得"""
    token = ACCOUNTS[account_key]["token"]
    url = f"{THREADS_API_BASE}/{post_id}/replies"
    params = {
        "fields": "id,text,timestamp,username,like_count",
        "access_token": token,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    return data.get("data", [])


# ============================================================
# 毎朝の自動ルーティン
# ============================================================
def daily_routine(account_key: str):
    """
    毎朝の自動ルーティン:
    1. 前日の投稿分析
    2. 競合バズ投稿リサーチ
    3. 分析結果をファイルに保存
    """
    import anthropic

    name = ACCOUNTS[account_key]["name"]
    print(f"\n{'='*60}")
    print(f"  {name} - 毎朝の自動分析ルーティン")
    print(f"  {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print(f"{'='*60}")

    # 1. ユーザー情報取得
    get_user_profile(account_key)

    # 2. 前日の投稿分析
    print("\n📊 前日の投稿分析...")
    analysis = analyze_posts(account_key, days=1)

    # 3. 競合リサーチ
    print("\n🔍 競合バズ投稿リサーチ...")
    if account_key == "ponta":
        keywords = ["AI 副業", "借金返済", "AI 稼ぐ"]
    else:
        keywords = ["星座占い", "恋愛運", "タロット 恋愛"]

    competitor_posts = []
    for kw in keywords:
        results = search_threads(account_key, kw, limit=5)
        competitor_posts.extend(results)
        time.sleep(1)

    # バズ投稿TOP3を抽出
    if competitor_posts:
        competitor_posts.sort(key=lambda p: p.get("views", 0), reverse=True)
        top3 = competitor_posts[:3]
        print(f"\n🏆 競合バズ投稿TOP3:")
        for i, p in enumerate(top3):
            print(f"  {i+1}. {p.get('views', '?')}表示 | @{p.get('username', '?')}")
            print(f"     {p.get('text', '')[:100]}")
    else:
        top3 = []

    # 4. Claude APIで分析・改善点抽出
    print("\n🤖 AIによる分析・改善点抽出...")
    client = anthropic.Anthropic()

    analysis_prompt = f"""以下は{name}のThreadsアカウントの分析データです。

【前日の投稿分析】
{json.dumps(analysis.get('summary', {}), ensure_ascii=False, indent=2)}

【前日の全投稿】
{json.dumps([{{'text': p.get('text','')[:200], 'views': p.get('views',0), 'likes': p.get('like_count',0), 'replies': p.get('reply_count',0)}} for p in analysis.get('posts', [])], ensure_ascii=False, indent=2)}

【競合バズ投稿TOP3】
{json.dumps([{{'username': p.get('username',''), 'text': p.get('text','')[:200], 'views': p.get('views',0), 'likes': p.get('like_count',0)}} for p in top3], ensure_ascii=False, indent=2)}

以下を簡潔に分析してください：
1. 前日の投稿で一番伸びた投稿の要因（なぜ伸びたか）
2. 前日の投稿で伸びなかった投稿の改善点
3. 競合のバズ投稿から学べるポイント3つ
4. 今日の投稿で意識すべきこと

日本語で、箇条書きで簡潔に。
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    ai_analysis = response.content[0].text

    print(f"\n{ai_analysis}")

    # 5. 結果をファイルに保存
    output_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    report_path = os.path.join(output_dir, account_key, f"daily_report_{date_str}.txt")

    os.makedirs(os.path.join(output_dir, account_key), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"=== {name} デイリーレポート {date_str} ===\n\n")
        f.write(f"【投稿分析サマリー】\n")
        f.write(json.dumps(analysis.get("summary", {}), ensure_ascii=False, indent=2))
        f.write(f"\n\n【AI分析・改善点】\n")
        f.write(ai_analysis)
        f.write(f"\n\n【競合バズTOP3】\n")
        for i, p in enumerate(top3):
            f.write(f"{i+1}. @{p.get('username','')} | {p.get('views',0)}表示\n")
            f.write(f"   {p.get('text','')[:150]}\n\n")

    print(f"\n📄 レポート保存: {report_path}")

    return {
        "analysis": analysis,
        "competitor_top3": top3,
        "ai_insights": ai_analysis,
    }


# ============================================================
# メイン実行
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Threads API自動化")
    parser.add_argument("account", choices=["ponta", "luna"], help="対象アカウント")
    parser.add_argument("--profile", action="store_true", help="プロフィール取得")
    parser.add_argument("--post", type=str, default=None, help="テキストを投稿")
    parser.add_argument("--analyze", action="store_true", help="前日の投稿を分析")
    parser.add_argument("--search", type=str, default=None, help="キーワードで検索")
    parser.add_argument("--daily", action="store_true", help="毎朝の自動ルーティン実行")
    parser.add_argument("--days", type=int, default=1, help="分析対象の日数")

    args = parser.parse_args()

    if args.profile:
        result = get_user_profile(args.account)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.post:
        result = publish_post(args.account, args.post)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.analyze:
        analyze_posts(args.account, days=args.days)

    elif args.search:
        search_threads(args.account, args.search)

    elif args.daily:
        daily_routine(args.account)

    else:
        parser.print_help()
