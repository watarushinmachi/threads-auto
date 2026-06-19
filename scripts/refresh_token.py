#!/usr/bin/env python3
"""
Threads長期トークンの自動更新
- 現在の THREADS_PONTA_TOKEN を th_refresh_token で延長（有効期限を60日リセット）
- 新トークンを GITHUB_OUTPUT(token=) とログマスクで安全に後続ステップへ渡す
- 注意：トークンは「発行から24時間以上・60日未満」でないとリフレッシュ不可
"""
import os
import sys
import requests

BASE = "https://graph.threads.net"


def main():
    tok = os.environ.get("THREADS_PONTA_TOKEN", "").strip()
    if not tok:
        print("THREADS_PONTA_TOKEN が空です", file=sys.stderr)
        sys.exit(1)

    r = requests.get(f"{BASE}/refresh_access_token", params={
        "grant_type": "th_refresh_token",
        "access_token": tok,
    })
    j = r.json()
    new = j.get("access_token")
    if not new:
        print(f"リフレッシュ失敗: {r.status_code} {j}", file=sys.stderr)
        sys.exit(1)

    days = round(j.get("expires_in", 0) / 86400, 1)
    # GitHub Actionsのログで新トークンをマスク
    print(f"::add-mask::{new}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"token={new}\n")
    # ローカル実行時のフォールバック（CIでは使わない）
    if not out:
        with open("new_token.txt", "w") as f:
            f.write(new)
    print(f"✅ トークン更新成功（残り約 {days} 日に延長）")


if __name__ == "__main__":
    main()
