# Metaverde ChatGPT Business Autofill Engine

自动化表单批量填报与身份独立随机化系统，专门用于自动化申请 Metaverde ChatGPT Business Partner URL。

![Python 3](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 特性亮点

- ⚡ **零第三方依赖 (Zero-Dependency)**：采用 Python 3 原生标准库（`http.server` 与 `urllib`），无需 `pip install` 任何库，开箱即用。
- 🎲 **每单独立动态随机身份**：
  - 每提交一个邮箱，自动动态抽取匹配真实的欧美名与姓（First / Last Name）。
  - 动态组合 300+ 种科技/咨询类合规企业名称（Organization）并生成匹配的企业官网。
  - 随机配置美国常见合规区号电话（202 / 415 / 312 / 646 等）。
  - 随机轮询多条自然真实的业务需求描述（Intended Use）。
- 📂 **海量邮箱批量导入与高容错解析**：
  - 支持拖放或粘贴 `.txt` / `.csv` 文件。
  - 内置全局邮箱正则提取器，无论是纯邮箱、带密码混杂格式（如 `user----pass----email`）还是特殊分隔符，均能自动准确抓取并去重。
- 🛡️ **反爬与安全规避**：
  - 每次提交前自动向目标页发起预检，实时提取最新的 `_source_context` 防重放令牌。
  - 自动保留 `_gotcha` 蜜罐为空，防止触发服务端反爬拦截。
  - 自定义队列提交间隔时间（默认 3 秒/次），防接口风控封禁。
- 📊 **可视化 Web 控制台**：
  - 实时进度条与指标看板（总数 / 成功 / 失败 / 剩余）。
  - 实时流式执行日志与明细结果表格。
  - 支持中途 **【暂停】**、**【继续】**、**【终止】**。
  - 任务完成后支持一键导出包含随机身份与返回码的 **CSV 报告**。

---

## 🚀 快速开始

### 1. 克隆仓库与启动

```bash
git clone https://github.com/HUAer07/metaverde-autofill.git
cd metaverde-autofill
python3 app.py
```

终端打印就绪后，在浏览器访问控制台：
```
http://127.0.0.1:5005
```

### 2. 批量提交操作

1. 进入控制台的 **【批量邮箱导入】** 面板；
2. 拖入或粘贴你的邮箱列表文件（如 `1000邮箱.txt`）；
3. 勾选 **`🎲 开启【每单独立随机身份】`**；
4. 设定间隔时间（建议 2~5 秒）及申请席位数；
5. 点击 **【▶ 开始批量提交】**，系统将自动开始全流程提交。

---

## 🛠️ 技术架构

```
               ┌──────────────────────────────────────┐
               │         Browser Web Console          │
               │   (Dark Modern UI / Queue Manager)   │
               └──────────────────┬───────────────────┘
                                  │ JSON REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Local Python Backend (app.py)                       │
│  - Native HTTP Server (0.0.0.0:5005)                                │
│  - Dynamic Token Scraper (extracts _source_context & action URL)    │
│  - Identity Randomizer (Names, Companies, Domains, Phones, Uses)    │
│  - Request Dispatcher (Safe POST with Anti-Bot HoneyPot Isolation)  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTPS Form POST
                                  ▼
                   Target Partner Form Endpoint
```

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE)。仅供自动化测试与技术研究使用。
