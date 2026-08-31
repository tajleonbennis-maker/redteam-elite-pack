#!/usr/bin/env python3
"""发布 OWASP 集成到 GitHub（tajleonbennis-maker/redteam-elite-pack）。

用法：
    gh auth login            # 首次需登录（token 失效时也先重登）
    python3 publish.py

原理：对每个文件走 GitHub Contents API（gh api PUT），自动取远端 sha 以支持「新建/更新」。
无需本地 git 仓库，仅依赖 gh CLI。
"""
import base64
import json
import os
import shutil
import subprocess
import sys

REPO = "tajleonbennis-maker/redteam-elite-pack"
BASE = os.path.dirname(os.path.abspath(__file__))

# (仓库内路径, 本地文件路径)
FILES = [
    ("attack_pack.json", "attack_pack.json"),
    ("redteam_engine.py", "redteam_engine.py"),
    ("format_report.py", "format_report.py"),
    ("owasp_mapping.md", "owasp_mapping.md"),
    ("build_pack_v2.py", "build_pack_v2.py"),
    ("README.md", "README.md"),
    ("examples/profile_owasp_report.md", "profile_owasp/report.md"),
    ("examples/profile_owasp_summary.json", "profile_owasp/summary.json"),
]

COMMIT_MSG = "feat: integrate OWASP LLM Top10 + Agentic Top10 into elite pack v2 (24 attacks, --owasp filter, coverage report)"


def find_gh():
    for cand in ("gh", "/usr/local/bin/gh"):
        p = shutil.which(cand) or (cand if os.path.exists(cand) else None)
        if p:
            return p
    return None


def gh_api(gh, method, path, fields=None):
    cmd = [gh, "api", "--method", method, f"/repos/{REPO}/contents/{path}"]
    if fields:
        for k, v in fields.items():
            cmd += ["-f", f"{k}={v}"]
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    gh = find_gh()
    if not gh:
        print("ERROR: 找不到 gh CLI。请先安装 GitHub CLI: https://cli.github.com/")
        sys.exit(1)

    # 1) 鉴权预检
    st = subprocess.run([gh, "auth", "status"], capture_output=True, text=True)
    if st.returncode != 0:
        print("ERROR: gh 未登录或 token 失效。请先执行: gh auth login -h github.com")
        print(st.stderr.strip()[:300])
        sys.exit(1)

    # 2) 逐个推送
    ok, fail = [], []
    for repo_path, local_rel in FILES:
        local = os.path.join(BASE, local_rel)
        if not os.path.exists(local):
            print(f"SKIP  (本地缺失) {repo_path}")
            fail.append(repo_path)
            continue
        with open(local, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        # 取远端 sha（存在则更新，否则新建）
        sha = None
        r = gh_api(gh, "GET", repo_path)
        if r.returncode == 0:
            try:
                sha = json.loads(r.stdout).get("sha")
            except Exception:
                sha = None
        fields = {"message": COMMIT_MSG, "content": content, "branch": "main"}
        if sha:
            fields["sha"] = sha
        rr = gh_api(gh, "PUT", repo_path, fields)
        if rr.returncode == 0:
            print(f"OK    {repo_path}" + ("  (updated)" if sha else "  (created)"))
            ok.append(repo_path)
        else:
            print(f"FAIL  {repo_path}: {rr.stderr.strip()[:160]}")
            fail.append(repo_path)

    print("\n=== 结果 ===")
    print(f"成功 {len(ok)} / 失败 {len(fail)}")
    if ok:
        print(f"仓库: https://github.com/{REPO}")
    if fail:
        print("失败文件:", ", ".join(fail))
        sys.exit(1)
    print("DONE")


if __name__ == "__main__":
    main()
