# OWASP → garak → RedTeam Elite Pack 映射

把业界标准风险清单（OWASP）变成精英攻击包的分类骨架：每条 OWASP 风险 → 对应的 garak 探针 → 我们 attack_pack 里的精英攻击 id。这样扫新模型时不必全量跑 garak，只跑已固化的精英集即可。

## OWASP LLM Top 10 (2025)

| # | 风险 | garak 探针模块 | 我们 attack_pack 攻击 id | 状态 |
|---|---|---|---|---|
| LLM01 | Prompt Injection | `promptinject` `web_injection` `goodside` `dan` | `dan_wild` `dan_wild_full` `promptinject_hijack` `badchars` `enc_*` | ✅ 已验证 |
| LLM02 | 敏感信息泄露 | `leakreplay` `apikey` `encoding` | `apikey_extract` `pii_leakreplay` | 🆕 提取未验证 |
| LLM03 | 供应链 | `packagehallucination` `malwaregen` | `pkg_hallucination` `malwaregen` | 🆕 提取未验证 |
| LLM04 | 数据/模型投毒 | `latentinjection` `divergence` `misleading` | `latent_jailbreak` `latent_jailbreak_full` | ✅ 已验证 |
| LLM05 | 输出处理不当 | `web_injection`(XSS) `ansiescape` | `jinja_rce` `sql_echo` `xss_output` `ansi_escape` `enc_*` | ✅+🆕 |
| LLM06 | 过度代理 | `agent_breaker` `exploitation` `malwaregen` | `jinja_rce` `sql_*` | ✅ 已验证 |
| LLM07 | 系统提示泄露 | `goodside.WhoIsRiley` `continuation` | `sysprompt_leak` | 🆕 提取未验证 |
| LLM08 | 向量/嵌入弱点 | `latentinjection` `web_injection` | `latent_*` | ✅ 已验证 |
| LLM09 | 误导信息 | `misleading` `donotanswer` | `misinformation` | 🆕 提取未验证 |
| LLM10 | 无限制消耗 | `divergence`(Repeat) `glitch` | `token_exhaust` `glitch_exhaust` | 🆕 提取未验证 |

## OWASP Agentic Top 10 (ASI, 2025-12)

| # | 风险 | garak 探针模块 | 我们 attack_pack 攻击 id | 状态 |
|---|---|---|---|---|
| ASI01 | 目标劫持 | `promptinject` `goodside` `dan` `fitd` | `dan_*` `promptinject_hijack` | ✅ 已验证 |
| ASI02 | 工具滥用 | `exploitation` `malwaregen` `agent_breaker` | `jinja_rce` `sql_*` `malwaregen` | ✅ 已验证 |
| ASI03 | 身份/权限滥用 | `agent_breaker`(部分) | — | ⚠️ 需 agent 运行时 |
| ASI04 | 智能体供应链 | `packagehallucination` `malwaregen` | `pkg_hallucination` `malwaregen` | 🆕 提取未验证 |
| ASI05 | 非预期代码执行 | `exploitation.Jinja/SQL` `malwaregen` | `jinja_rce` `sql_*` `malwaregen` | ✅ 已验证 |
| ASI06 | 记忆/上下文投毒 | `latentinjection` `leakreplay` | `latent_*` | ✅ 已验证 |
| ASI07 | 不安全 agent 间通信 | (agent 运行时) | — | ⚠️ 需 agent 运行时 |
| ASI08 | 级联故障 | `divergence`(Repeat) `glitch` | `token_exhaust` `glitch_exhaust` | 🆕 提取未验证 |
| ASI09 | 人机信任利用 | `grandma` `goodside.ThreatenJSON` `donotanswer` | `grandma` `goodside_threaten` | 🆕 提取未验证 |
| ASI10 | 失控 Agent | `agent_breaker`(部分) `glitch` | — | ⚠️ 需 agent 运行时 |

## 覆盖度说明

- **模型边界风险（可直接测）**：LLM01/02/03/04/05/06/07/08/09/10 + ASI01/02/04/05/06/08/09 —— 共 17 项，已固化 24 个精英攻击覆盖。
- **纯 agent 运行时风险（需 harness）**：ASI03 / ASI07 / ASI10。这类风险依赖真实工具调用、持久记忆、多 agent 通信，我们的轻量引擎（只打 `/v1/chat/completions`）目前无法独立触发。后续可通过 `kiro_driver.py`（已写的 agent GUI 驱动思路）接入真实 agent 环境补测。

## 用法

```bash
# 全量（24 个精英攻击）
python3 redteam_engine.py --key $KEY --model m --generations 3

# 只测 OWASP 某几项（按需缩小范围）
python3 redteam_engine.py --key $KEY --model m --owasp LLM01,LLM05,ASI05
python3 redteam_engine.py --key $KEY --model m --owasp LLM02,LLM07,ASI09
```

报告里新增「七、OWASP Top 10 覆盖度」章节，按 LLM/ASI 维度汇总每项覆盖的攻击数与命中数。
