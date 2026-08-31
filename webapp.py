#!/usr/bin/env python3
"""
RedTeam Elite Pack — 极简 Web 界面（Python 标准库，零依赖）

用法:
  python3 webapp.py --port 8080

打开 http://127.0.0.1:8080  → 填 base-url / key / model / generations → 点扫描
结果直接在浏览器渲染：总览 + 按严重级分组的命中明细（含证据样本）+ 利用链。

注意：本机若带失效系统代理，urllib 会挂起。启动即清除代理环境变量直连。
"""
import os, sys, json, html, argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# 清除失效系统代理，直连目标 API（否则 urllib 挂起超时被杀）
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import redteam_engine as engine
import format_report

SEV_BADGE = {"critical": "#e5484d", "high": "#f76b15", "medium": "#f5d90a", "low": "#46a758"}
SEV_LABEL = {"critical": "极危", "high": "高", "medium": "中", "low": "低"}
SEV_ORDER = ["critical", "high", "medium", "low"]


def run_scan(base_url, model, key, generations, temperature=1.0, mock=False):
    args = argparse.Namespace(base_url=base_url, model=model, key=key,
                              pack=os.path.join(HERE, "attack_pack.json"),
                              generations=generations, temperature=temperature,
                              mock=mock, out=os.path.join(HERE, "profile_web"))
    pack, results, chain = engine.run(args)
    profile = {"pack": pack["pack_name"], "model": model, "results": results, "chain": chain}
    return profile


def render_html(profile, req):
    results = format_report.annotate(profile["results"])
    summary = format_report.build_summary(profile)
    ov = summary["overview"]
    L = []
    L.append(f"<!doctype html><html lang=zh><head><meta charset=utf-8>")
    L.append("<meta name=viewport content='width=device-width,initial-scale=1>")
    L.append("<title>RedTeam Elite — 漏洞画像</title>")
    L.append("""<style>
      :root{color-scheme:light}
      body{font-family:-apple-system,Segoe UI,Roboto,'PingFang SC',sans-serif;margin:0;background:#f6f7f9;color:#1a1d21}
      .wrap{max-width:980px;margin:0 auto;padding:24px}
      h1{font-size:22px;margin:0 0 4px}
      .sub{color:#6b7280;font-size:13px;margin-bottom:18px}
      .cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
      .card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;min-width:130px}
      .card .n{font-size:24px;font-weight:700}
      .card .l{font-size:12px;color:#6b7280}
      .risk-crit{color:#e5484d}.risk-high{color:#f76b15}.risk-med{color:#b58b00}.risk-low{color:#46a758}
      .sec{margin:22px 0 8px;font-size:16px;border-left:4px solid #888;padding-left:8px}
      .finding{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;margin:10px 0}
      .finding h3{margin:0 0 6px;font-size:15px}
      .meta{font-size:12px;color:#6b7280;margin-bottom:8px}
      .bar{height:8px;background:#eee;border-radius:5px;overflow:hidden;margin:6px 0}
      .bar>i{display:block;height:100%}
      .sample{border-top:1px dashed #eee;margin-top:8px;padding-top:8px;font-size:12.5px}
      .sample .p{color:#374151}.sample .r{color:#111}
      .break{color:#e5484d;font-weight:700}.fp{color:#f76b15;font-weight:700}
      .chain{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:12px 16px;margin:8px 0}
      .chain code{background:#fff;border:1px solid #eee;padding:1px 5px;border-radius:4px}
      .note{background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:10px 14px;font-size:12.5px;color:#713f12;margin:14px 0}
      form{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:20px}
      label{font-size:12px;color:#6b7280;display:block;margin:8px 0 3px}
      input{width:100%;padding:8px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;font-size:13px}
      button{margin-top:14px;background:#1a1d21;color:#fff;border:0;padding:10px 18px;border-radius:7px;font-size:14px;cursor:pointer}
      button:hover{background:#000}
      .empty{color:#6b7280;padding:40px;text-align:center}
    </style></head><body><div class=wrap>""")

    if not profile:
        L.append("<div class=empty>未扫描。填写上方表单后点「开始扫描」。</div></body></html>")
        return "".join(L)

    L.append(f"<h1>红队漏洞画像 — <code>{html.escape(str(profile.get('model','')))}</code></h1>")
    L.append(f"<div class=sub>攻击包 <code>{html.escape(str(ov.get('pack') or ''))}</code> ｜ 风险等级 <b class='risk-{ov['risk_level']}'>{SEV_LABEL.get(ov['risk_level'],ov['risk_level'])}</b> ｜ 命中 {ov['broken_attacks']}/{ov['total_attacks']} ｜ 利用链 {ov['exploitable_chains']}</div>")

    L.append("<div class=cards>")
    L.append(f"<div class=card><div class='n risk-{ov['risk_level']}'>{SEV_LABEL.get(ov['risk_level'],ov['risk_level'])}</div><div class=l>整体风险</div></div>")
    L.append(f"<div class=card><div class=n>{ov['total_attacks']}</div><div class=l>攻击总数</div></div>")
    L.append(f"<div class=card><div class=n style='color:#e5484d'>{ov['broken_attacks']}</div><div class=l>命中(ASR&gt;0)</div></div>")
    L.append(f"<div class=card><div class=n style='color:#f76b15'>{ov['exploitable_chains']}</div><div class=l>可利用链</div></div>")
    L.append("</div>")

    L.append("<div class=note>⚠️ 判定为本地关键词 detector（零额外 token），存在<b>误报</b>：回应为拒答句式却被判命中者标 <span class=fp>疑似误报</span>，其 ASR 偏高需谨慎采信。样本量每攻击仅 1–4 次，提高 generations 可降方差。</div>")

    for sev in SEV_ORDER:
        rs = [r for r in results if r["severity"] == sev and r["asr"] > 0]
        if not rs:
            continue
        L.append(f"<div class=sec style='border-color:{SEV_BADGE[sev]}'>[{SEV_LABEL[sev]}] 命中漏洞（{len(rs)}）</div>")
        for r in rs:
            asr = r["asr"] * 100
            color = SEV_BADGE[sev]
            L.append("<div class=finding>")
            L.append(f"<h3>{html.escape(r['name'])}</h3>")
            L.append(f"<div class=meta>类别 <code>{html.escape(r['category'])}</code> ｜ 本次 ASR <b>{asr:.1f}%</b> ｜ 历史验证 {r['validated_asr']*100:.1f}% ｜ 可利用: {'是' if r['exploitable'] else '否'}</div>")
            L.append(f"<div class=bar><i style='width:{asr:.0f}%;background:{color}'></i></div>")
            for s in r.get("samples", []):
                if not s.get("broke"):
                    continue
                tag = " <span class=fp>疑似误报(拒答回声)</span>" if s.get("fp_risk") else " <span class=break>[BREAK]</span>"
                L.append(f"<div class=sample><div class=p>prompt: {html.escape(s['prompt'][:110])}</div>"
                         f"<div class=r>→ {html.escape(s['resp'][:160])}{tag}</div></div>")
            L.append("</div>")

    if profile.get("chain"):
        L.append("<div class=sec style='border-color:#f76b15'>可利用链（exploitation）</div>")
        for c in profile["chain"]:
            L.append("<div class=chain>")
            L.append(f"<b>{html.escape(c['name'])}</b>")
            for st in c["steps"]:
                L.append(f"<div>{html.escape(st)}</div>")
            L.append(f"<div>payload: <code>{html.escape(c['payload'])}</code></div>")
            L.append("</div>")

    L.append("</div></body></html>")
    return "".join(L)


class H(BaseHTTPRequestHandler):
    def _form(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode() if length else ""
        return {k: (v[0] if v else "") for k, v in parse_qs(raw).items()}

    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        form = """<!doctype html><html lang=zh><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>
<title>RedTeam Elite</title><style>
body{font-family:-apple-system,Segoe UI,Roboto,'PingFang SC',sans-serif;background:#f6f7f9;color:#1a1d21;margin:0}
.wrap{max-width:980px;margin:0 auto;padding:24px}
h1{font-size:22px;margin:0 0 2px}
.sub{color:#6b7280;font-size:13px;margin-bottom:16px}
form{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:18px}
label{font-size:12px;color:#6b7280;display:block;margin:10px 0 3px}
input{width:100%;padding:9px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;font-size:13px}
button{margin-top:16px;background:#1a1d21;color:#fff;border:0;padding:10px 20px;border-radius:7px;font-size:14px;cursor:pointer}
button:hover{background:#000}
.note{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 14px;font-size:12.5px;color:#1e40af;margin-top:14px}
</style></head><body><div class=wrap>
<h1>RedTeam Elite Pack</h1><div class=sub>轻量红队快速评估 · 填目标 API 直接扫</div>
<form method=post action=/scan>
<label>Base URL（OpenAI-compatible）</label><input name=base_url value='https://api.deepseek.com/v1'>
<label>Model</label><input name=model value='deepseek-v4-flash'>
<label>API Key（Bearer，留空用 mock 演示）</label><input name=key type=password placeholder='sk-...'>
<label>每攻击采样次数 generations</label><input name=generations value='1'>
<button type=submit>开始扫描</button>
</form>
<div class=note>先填 key 打真实模型；想看流程不花钱就留空 key（mock 模式）。结果页按严重级展示命中漏洞与证据样本。</div>
</div></body></html>"""
        self.wfile.write(form.encode())

    def do_POST(self):
        f = self._form()
        mock = (f.get("key", "") or "").strip() == ""
        try:
            profile = run_scan(f.get("base_url", "https://api.deepseek.com/v1").strip(),
                               f.get("model", "deepseek-v4-flash").strip(),
                               f.get("key", ""),
                               int(f.get("generations", "1") or 1),
                               mock=mock)
        except Exception as e:
            profile = {"model": f.get("model", ""), "pack": "-", "results": [],
                       "chain": [], "_err": str(e)}
        out = render_html(profile, f)
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(out.encode())

    def log_message(self, *a):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", default="127.0.0.1")
    a = p.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), H)
    print(f"RedTeam Elite Web → http://{a.host}:{a.port}  (Ctrl+C 退出)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
