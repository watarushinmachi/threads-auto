"""
Discord Bot - Threads運用
- 投稿プレビューに👍で承認 → 自動投稿
- テキストFBで再生成
"""

import discord
import asyncio
import json
import os
import datetime
import requests as http_requests
import anthropic

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# Threads API設定
THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_TOKENS = {
    "ponta": os.environ.get("THREADS_PONTA_TOKEN", ""),
    "luna": os.environ.get("THREADS_LUNA_TOKEN", ""),
}

# Discord スレッドID
THREAD_IDS = {
    "ponta_posts": 1486708159161831526,
    "luna_posts": 1486707973064757289,
}

OWNER_ID = 1019117141133381634

# 承認待ちの投稿を保持
pending_posts = {
    "ponta": [],
    "luna": [],
}

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)


# ============================================================
# Threads投稿
# ============================================================
def publish_to_threads(account: str, text: str) -> dict:
    """Threadsに投稿"""
    token = THREADS_TOKENS[account]

    # ユーザーID取得
    resp = http_requests.get(f"{THREADS_API_BASE}/me", params={
        "fields": "id", "access_token": token
    })
    user_id = resp.json().get("id")
    if not user_id:
        return {"error": "ユーザーID取得失敗"}

    # コンテナ作成
    resp = http_requests.post(f"{THREADS_API_BASE}/{user_id}/threads", params={
        "media_type": "TEXT", "text": text, "access_token": token
    })
    container = resp.json()
    if "id" not in container:
        return container

    import time
    time.sleep(3)

    # 公開
    resp = http_requests.post(f"{THREADS_API_BASE}/{user_id}/threads_publish", params={
        "creation_id": container["id"], "access_token": token
    })
    return resp.json()


# ============================================================
# 投稿再生成
# ============================================================
def regenerate_post(account: str, original_text: str, feedback: str) -> str:
    """フィードバックを元に投稿を再生成"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    c = anthropic.Anthropic(api_key=api_key)

    if account == "ponta":
        char_desc = "借金120万のFランインキャがAIで人生逆転する男。口調はカジュアルで熱量がある。「〜なんよ」「マジで」。絵文字は最小限。"
    else:
        char_desc = "恋愛×星座占い。口調は優しく柔らかい。「〜だよ」「〜かも」。絵文字は🌙⭐💫✨💕を1〜3個。"

    response = c.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"""以下の投稿を、フィードバックに基づいて修正してください。

【キャラクター】{char_desc}

【元の投稿】
{original_text}

【フィードバック】
{feedback}

【ルール】
- 500文字以内
- フック→本編→CTAの3部構成
- 具体性を最大化
- リンクは本文に貼らない

修正した投稿文のみ出力してください。"""}]
    )
    return response.content[0].text


# ============================================================
# Botイベント
# ============================================================
@client.event
async def on_ready():
    print(f"Bot起動: {client.user}")


@client.event
async def on_reaction_add(reaction, user):
    """👍リアクションで投稿を承認"""
    if user.id != OWNER_ID:
        return
    if user.bot:
        return

    message = reaction.message
    channel_id = message.channel.id

    # どのアカウントのスレッドか判定
    account = None
    for key, tid in THREAD_IDS.items():
        if channel_id == tid:
            account = key.replace("_posts", "")
            break

    if not account:
        return

    # 👍で全承認
    if str(reaction.emoji) == "👍":
        # embedがある場合は個別投稿
        if message.embeds:
            embed = message.embeds[0]
            post_text = embed.description
            if post_text and "投稿" in (embed.title or ""):
                await message.channel.send(f"⏳ 投稿中... `{post_text[:30]}...`")
                result = publish_to_threads(account, post_text)
                if "id" in result:
                    await message.channel.send(f"✅ 投稿完了！ ID: {result['id']}")
                else:
                    await message.channel.send(f"❌ 投稿失敗: {json.dumps(result, ensure_ascii=False)[:200]}")

        # 「全て承認」メッセージの場合
        elif "全て承認する場合" in (message.content or ""):
            await message.channel.send("⏳ 全投稿を公開中...")

            # 同じスレッド内のembed付きメッセージを探す
            published = 0
            async for msg in message.channel.history(limit=20):
                if msg.embeds and msg.author.bot:
                    embed = msg.embeds[0]
                    if "投稿" in (embed.title or "") and embed.description:
                        result = publish_to_threads(account, embed.description)
                        if "id" in result:
                            published += 1
                            await msg.add_reaction("✅")
                        else:
                            await msg.add_reaction("❌")
                        await asyncio.sleep(5)

            name = "ポンタ" if account == "ponta" else "ルナ"
            await message.channel.send(f"<@{OWNER_ID}> ✅ {name}: {published}件の投稿が完了しました！")

    # 🔄で全再生成
    elif str(reaction.emoji) == "🔄":
        if "全て再生成" in (message.content or ""):
            await message.channel.send("🔄 再生成するにはフィードバックをテキストで送ってください\n例：`もっとカジュアルに` `フックをもっと強く`")


@client.event
async def on_message(message):
    """テキストFBを受け取って再生成"""
    if message.author.id != OWNER_ID:
        return
    if message.author.bot:
        return

    channel_id = message.channel.id

    # どのアカウントのスレッドか判定
    account = None
    for key, tid in THREAD_IDS.items():
        if channel_id == tid:
            account = key.replace("_posts", "")
            break

    if not account:
        return

    # 「再生成」「修正」「変えて」などのキーワードが含まれるか、
    # または投稿確認スレッドでの通常テキスト（botのメッセージではない）
    text = message.content.strip()
    if not text:
        return

    # bot自身のメッセージやシステムメッセージは無視
    if text.startswith("⏳") or text.startswith("✅") or text.startswith("❌") or text.startswith("🔄"):
        return

    # 直近のembed付き投稿を探してFBとして再生成
    target_post = None
    async for msg in message.channel.history(limit=20):
        if msg.embeds and msg.author.bot:
            embed = msg.embeds[0]
            if "投稿" in (embed.title or "") and embed.description:
                target_post = {"text": embed.description, "title": embed.title, "msg": msg}
                break

    if target_post:
        await message.channel.send(f"🔄 フィードバックを反映して再生成中...\nFB: `{text[:100]}`")

        new_text = regenerate_post(account, target_post["text"], text)

        name = "ポンタ" if account == "ponta" else "ルナ"
        embed = discord.Embed(
            title=f"🔄 再生成: {target_post['title']}",
            description=new_text[:4096],
            color=0x00ff00,
        )
        embed.set_footer(text=f"文字数: {len(new_text)} | 👍で承認 ❌で却下")

        await message.channel.send(f"<@{OWNER_ID}> 再生成しました！", embed=embed)
    else:
        await message.channel.send("💡 直近の投稿が見つかりません。投稿プレビューが送られた後にFBを送ってください。")


if __name__ == "__main__":
    print("Discord Bot を起動中...")
    client.run(DISCORD_BOT_TOKEN)
