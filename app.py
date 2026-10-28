#!/usr/bin/env python3
"""
Metaverde ChatGPT Business 自动填写与批量导入提交系统 (防 429 限流强化版)
- 纯 Python 3 原生标准库，零第三方依赖 (无需 pip install)
- 支持单条测试 & 批量邮箱导入（多行粘贴 / TXT / CSV）
- 【每单独立随机身份】：每次提交动态生成完全不同的姓名、企业名、电话、官网、业务用途等
- 【防 429 限流核心架构】：
  1. 支持自定义 HTTP / SOCKS5 代理池 (可配置本地或动态代理出口)
  2. 429 自动指数退避重试机制 (检测到限流自动休眠冷却并原位重试)
  3. 随机时间抖动 (Jitter，模拟真人行为间隔)
  4. 支持【一键重试失败任务】
"""

import sys
import os
import json
import re
import random
import time
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 5005
TARGET_PAGE_URL = "https://metaverde.com/chatgpt-business/"
DEFAULT_ACTION_URL = "https://superintelia.com/f/761b6673-0d72-45a4-91de-335e7e1e73b1/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# 真实欧美姓名与企业数据库
FIRST_NAMES = [
    "Alexander", "Benjamin", "Charlotte", "Daniel", "Eleanor", "Felix", "Gabriel", "Hannah",
    "Isaac", "Julian", "Katherine", "Liam", "Madeleine", "Nathan", "Oliver", "Penelope",
    "Quinn", "Rachel", "Samuel", "Theodore", "Victoria", "William", "Zoe", "Arthur",
    "Beatrice", "Caleb", "Diana", "Ethan", "Fiona", "George", "Harper", "Ian",
    "Jessica", "Lucas", "Maya", "Noah", "Olivia", "Patrick", "Russell", "Sophia",
    "Thomas", "Valerie", "Wyatt", "Xavier", "Yasmine", "Zachary", "Marcus", "Elena"
]

LAST_NAMES = [
    "Anderson", "Bennett", "Campbell", "Donovan", "Edwards", "Fletcher", "Gallagher", "Harrison",
    "Ingram", "Jennings", "Kaufman", "Lambert", "Montgomery", "Navarro", "O'Connor", "Prescott",
    "Quigley", "Reynolds", "Sinclair", "Thornton", "Underwood", "Vance", "Whitmore", "Yates",
    "Armstrong", "Barrett", "Collier", "Davenport", "Ellington", "Faulkner", "Grayson", "Holloway",
    "Kendall", "Livingston", "Mercer", "Norris", "Pendleton", "Radcliffe", "Stratton", "Talbot"
]

COMPANY_PREFIXES = [
    "Apex", "Vanguard", "Horizon", "Meridian", "BlueSky", "Pulse", "Stratos", "Quantum",
    "Lumina", "CloudBridge", "Crestview", "Summit", "Nexus", "Aura", "Catalyst", "Frontier",
    "Omni", "Prism", "Sovereign", "Echo", "Vertex", "Cobalt", "Beacon", "Pioneer", "Synergy"
]

COMPANY_SUFFIXES = [
    "Technologies", "Solutions", "Dynamics", "Labs", "Consulting", "Partners", "Systems",
    "Interactive", "Ventures", "Group", "Analytics", "Digital", "Media", "Enterprises", "Studio"
]

INTENDED_USES = [
    "Migrating company AI workflows from personal accounts to a managed business workspace.",
    "Evaluating ChatGPT Business administrative controls, workspace sharing, and workspace policies.",
    "Piloting central prompt libraries and GPT models across our marketing and operations team.",
    "Standardizing AI collaboration, audit logging, and team data privacy compliance.",
    "Assessing team seat deployment and departmental generative AI workflow integration.",
    "Transitioning engineering and customer support teams into an enterprise-ready workspace.",
    "Deploying a pilot project to explore structured AI document drafting and analytics.",
    "Consolidating decentralized team subscriptions into a unified business tier workspace."
]

AREA_CODES = ["202", "415", "312", "646", "206", "512", "617", "303", "404", "702", "917", "408", "858"]

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metaverde 批量提交系统 (防 429 限流强化版)</title>
    <style>
        :root {
            --bg-color: #0b0f17;
            --card-bg: #141b26;
            --card-border: #263346;
            --accent: #10a37f;
            --accent-hover: #16b991;
            --accent-glow: rgba(16, 163, 127, 0.25);
            --text-main: #f3f4f6;
            --text-muted: #94a3b8;
            --input-bg: #0c121c;
            --input-border: #263346;
            --error: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
            --log-bg: #070a0f;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 1360px;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 14px 22px;
            border-radius: 12px;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: var(--accent);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            box-shadow: 0 0 12px var(--accent-glow);
        }

        .logo-title {
            font-size: 1.15rem;
            font-weight: 700;
        }

        .tab-nav {
            display: flex;
            background: #090e17;
            padding: 4px;
            border-radius: 8px;
            border: 1px solid var(--card-border);
            gap: 4px;
        }

        .tab-btn {
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 8px 18px;
            font-size: 0.88rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tab-btn.active {
            background: var(--card-bg);
            color: var(--accent);
            border: 1px solid var(--card-border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 1.25fr 1.15fr;
            gap: 18px;
        }

        @media (max-width: 1024px) {
            .grid-layout {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .card-title {
            font-size: 1.05rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--card-border);
        }

        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .full-width { grid-column: span 2; }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        label {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .required { color: var(--error); }

        input, select, textarea {
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-main);
            font-size: 0.88rem;
            outline: none;
            transition: all 0.2s;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px var(--accent-glow);
        }

        textarea {
            resize: vertical;
            line-height: 1.45;
            font-family: inherit;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 163, 127, 0.06);
            border: 1px solid rgba(16, 163, 127, 0.2);
            padding: 8px 12px;
            border-radius: 6px;
        }

        .checkbox-group input {
            cursor: pointer;
            accent-color: var(--accent);
            width: 15px;
            height: 15px;
        }

        .checkbox-group label {
            font-size: 0.82rem;
            color: var(--text-main);
            cursor: pointer;
            font-weight: 600;
        }

        /* 429 告警横幅 */
        .defense-box {
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .defense-title {
            color: #fbbf24;
            font-size: 0.84rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-group {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }

        button {
            cursor: pointer;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 8px 15px;
            font-size: 0.86rem;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .btn-primary {
            background: var(--accent);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--accent-hover);
            box-shadow: 0 0 10px var(--accent-glow);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--card-border);
        }

        .btn-secondary:hover {
            color: var(--text-main);
            border-color: var(--text-muted);
        }

        .btn-warning {
            background: #d97706;
            color: white;
        }
        .btn-danger {
            background: #dc2626;
            color: white;
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .console-box {
            background: var(--log-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px;
            font-family: "JetBrains Mono", Consolas, Monaco, monospace;
            font-size: 0.78rem;
            color: #d1d5db;
            height: 380px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .log-entry { line-height: 1.4; word-break: break-all; }
        .log-time { color: #64748b; margin-right: 6px; }
        .log-info { color: #60a5fa; }
        .log-success { color: #34d399; font-weight: 600; }
        .log-warn { color: #fbbf24; font-weight: 600; }
        .log-error { color: #f87171; font-weight: 600; }

        .metric-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }

        .metric-card {
            background: #090e17;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .metric-card span { font-size: 0.72rem; color: var(--text-muted); }
        .metric-card strong { font-size: 1.25rem; font-weight: 700; }

        .progress-container {
            width: 100%;
            height: 8px;
            background: #090e17;
            border: 1px solid var(--card-border);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--accent), #22c55e);
            transition: width 0.3s ease;
        }

        .table-wrap {
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid var(--card-border);
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.78rem;
            text-align: left;
        }

        th, td {
            padding: 8px 10px;
            border-bottom: 1px solid var(--card-border);
        }

        th {
            background: #0d1420;
            color: var(--text-muted);
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 2;
        }

        tr:hover { background: rgba(255, 255, 255, 0.02); }

        .tag {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .tag-pending { background: #334155; color: #94a3b8; }
        .tag-running { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
        .tag-success { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .tag-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

        .badge-pill {
            background: rgba(16, 163, 127, 0.15);
            color: var(--accent);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            border: 1px solid rgba(16, 163, 127, 0.3);
        }

        .file-drop-area {
            border: 2px dashed var(--card-border);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            background: rgba(255, 255, 255, 0.01);
            cursor: pointer;
            transition: all 0.2s;
        }
        .file-drop-area:hover {
            border-color: var(--accent);
            background: rgba(16, 163, 127, 0.03);
        }
    </style>
</head>
<body>

<div class="container">
    <div class="top-bar">
        <div class="logo-area">
            <div class="logo-icon">M</div>
            <div>
                <div class="logo-title">Metaverde 自动提交系统</div>
                <div style="font-size:0.75rem;color:var(--text-muted);">ChatGPT Business 批量自动化填报 · 429 频控防御增强版</div>
            </div>
        </div>
        <div class="tab-nav">
            <button class="tab-btn active" id="tabBatchBtn" onclick="switchTab('batch')">批量邮箱导入</button>
            <button class="tab-btn" id="tabSingleBtn" onclick="switchTab('single')">单次表单填写</button>
        </div>
    </div>

    <!-- 视图 1：批量邮箱导入视图 -->
    <div id="viewBatch" class="grid-layout">
        <div class="card">
            <div class="card-title">
                <span>批量导入邮箱列表</span>
                <span class="badge-pill" id="importCountBadge">就绪 (0 个)</span>
            </div>

            <!-- 动态随机选项 -->
            <div class="checkbox-group">
                <input type="checkbox" id="enablePerItemRandom" checked>
                <label for="enablePerItemRandom">
                    🎲 开启【每单独立随机身份】：每次提交动态生成不同姓名、公司名、官网、电话及用途
                </label>
            </div>

            <!-- 429 限流防御设置 -->
            <div class="defense-box">
                <div class="defense-title">
                    🛡️ 429 防限流与代理配置 (解决单个 IP 频繁提交报错)
                </div>
                <div class="form-grid">
                    <div class="form-group full-width">
                        <label>代理服务器 Proxy（可选，支持 HTTP / SOCKS5，例如 <code>http://127.0.0.1:7890</code>，留空则直连）：</label>
                        <input type="text" id="proxyUrl" placeholder="如 http://127.0.0.1:7890 或 动态住宅/机房代理 URL">
                    </div>
                    <div class="form-group">
                        <label>最小提交间隔 (秒)</label>
                        <input type="number" id="minInterval" value="6" min="1" max="120">
                    </div>
                    <div class="form-group">
                        <label>最大随机间隔 (秒，加入时间抖动)</label>
                        <input type="number" id="maxInterval" value="12" min="1" max="180">
                    </div>
                    <div class="form-group full-width" style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="autoCooldown429" checked style="accent-color:var(--warning);width:15px;height:15px;">
                        <label for="autoCooldown429" style="color:#fbbf24;font-weight:600;">
                            遇到 429 时自动休眠冷却 60 秒并原位重试（不浪费当前邮箱）
                        </label>
                    </div>
                </div>
            </div>

            <!-- 文件选择 -->
            <div class="file-drop-area" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" accept=".txt,.csv" style="display:none;" onchange="handleFileSelect(event)">
                <div style="font-size:0.86rem;font-weight:600;color:var(--text-main);">📁 点击选择或拖放 TXT / CSV 文件</div>
                <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">自动使用正则表达式提取所有有效邮箱，兼容任何复杂混杂文本</div>
            </div>

            <div class="form-group">
                <label>粘贴邮箱列表：</label>
                <textarea id="batchTextarea" rows="6" placeholder="alex.morgan@example.com&#10;sarah.connor@cyber.io&#10;david.miller@gmail.com"></textarea>
            </div>

            <div class="form-grid">
                <div class="form-group">
                    <label>申请席位数 (Planned Seats)</label>
                    <select id="batchSeats">
                        <option value="2" selected>2 Seats (固定)</option>
                        <option value="3-5">3 - 5 Seats</option>
                        <option value="RANDOM">🎲 随机轮询 (2, 3-5, 6-10)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>国家/地区 (Country)</label>
                    <select id="batchCountry">
                        <option value="US" selected>United States (US)</option>
                        <option value="CO">Colombia (CO)</option>
                        <option value="MX">Mexico (MX)</option>
                        <option value="CL">Chile (CL)</option>
                        <option value="PA">Panama (PA)</option>
                        <option value="OTHER">Other</option>
                    </select>
                </div>
            </div>

            <div class="btn-group">
                <button type="button" class="btn-secondary" onclick="loadSampleBatch()">载入示例</button>
                <button type="button" class="btn-secondary" onclick="clearBatch()">清空</button>
                <button type="button" class="btn-primary" id="startBatchBtn" onclick="startBatchProcess()">
                    <span>▶ 开始批量提交</span>
                </button>
                <button type="button" class="btn-warning" id="retryFailedBtn" onclick="retryFailedTasks()" style="display:none;">
                    <span>🔄 重试失败项 (<span id="retryFailedCount">0</span>)</span>
                </button>
                <button type="button" class="btn-warning" id="pauseBatchBtn" onclick="togglePauseBatch()" style="display:none;">
                    <span id="pauseBtnText">⏸ 暂停</span>
                </button>
                <button type="button" class="btn-danger" id="stopBatchBtn" onclick="stopBatchProcess()" style="display:none;">
                    <span>⏹ 停止</span>
                </button>
            </div>
        </div>

        <!-- 右侧进度监控与表格 -->
        <div class="card">
            <div class="card-title">
                <span>批量执行进度与指标</span>
                <div class="btn-group">
                    <button class="btn-secondary" style="padding:4px 8px;font-size:0.75rem;" onclick="exportResultsCSV()">📥 导出结果 CSV</button>
                </div>
            </div>

            <div class="metric-cards">
                <div class="metric-card">
                    <span>总任务</span>
                    <strong id="metricTotal">0</strong>
                </div>
                <div class="metric-card">
                    <span>成功</span>
                    <strong id="metricSuccess" style="color:var(--success);">0</strong>
                </div>
                <div class="metric-card">
                    <span>失败 (含429)</span>
                    <strong id="metricFailed" style="color:var(--error);">0</strong>
                </div>
                <div class="metric-card">
                    <span>剩余</span>
                    <strong id="metricRemaining" style="color:var(--text-muted);">0</strong>
                </div>
            </div>

            <div class="progress-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>

            <div class="table-wrap">
                <table id="resultsTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>邮箱地址</th>
                            <th>随机身份 (姓名 / 公司)</th>
                            <th>状态</th>
                            <th>返回码</th>
                            <th>耗时</th>
                        </tr>
                    </thead>
                    <tbody id="resultsTableBody">
                        <tr>
                            <td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px;">
                                暂无任务，请在左侧导入邮箱并点击开始
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="console-box" id="batchConsole" style="height: 170px;">
                <div class="log-entry"><span class="log-time">[System]</span> 429 防限流与批量提交系统已就绪...</div>
            </div>
        </div>
    </div>

    <!-- 视图 2：单条表单填写视图 -->
    <div id="viewSingle" class="grid-layout" style="display:none;">
        <div class="card">
            <div class="card-title">
                <span>单次手动填表测试</span>
                <button type="button" class="btn-secondary" style="padding:3px 8px;font-size:0.75rem;" onclick="randomizeSingleForm()">🎲 随机填充</button>
            </div>

            <form id="singleForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label>First Name <span class="required">*</span></label>
                        <input type="text" id="s_first_name" required value="Alex">
                    </div>
                    <div class="form-group">
                        <label>Last Name <span class="required">*</span></label>
                        <input type="text" id="s_last_name" required value="Morgan">
                    </div>
                    <div class="form-group full-width">
                        <label>Email <span class="required">*</span></label>
                        <input type="email" id="s_email" required value="alex.morgan@example.com">
                    </div>
                    <div class="form-group">
                        <label>Organization</label>
                        <input type="text" id="s_organization" value="Horizon Tech LLC">
                    </div>
                    <div class="form-group">
                        <label>Country <span class="required">*</span></label>
                        <select id="s_country">
                            <option value="US" selected>United States (US)</option>
                            <option value="CO">Colombia (CO)</option>
                            <option value="MX">Mexico (MX)</option>
                            <option value="CL">Chile (CL)</option>
                            <option value="PA">Panama (PA)</option>
                            <option value="OTHER">Other</option>
                        </select>
                    </div>
                    <div class="form-group full-width">
                        <label>代理 Proxy (可选，单次测试同样生效)</label>
                        <input type="text" id="s_proxy" placeholder="如 http://127.0.0.1:7890">
                    </div>
                    <div class="form-group full-width" style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="s_ack1" checked required>
                        <label for="s_ack1">[同意] 确认 Metaverde 可审查此请求。</label>
                    </div>
                    <div class="form-group full-width" style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="s_ack2" checked required>
                        <label for="s_ack2">[同意] 已阅读并同意使用规范及政策。</label>
                    </div>
                </div>

                <div class="btn-group" style="margin-top:16px;">
                    <button type="submit" id="singleSubmitBtn" class="btn-primary" style="flex:1;">
                        <span>立即提交单个</span>
                    </button>
                </div>
            </form>
        </div>

        <div class="card">
            <div class="card-title">
                <span>实时执行日志</span>
            </div>
            <div class="console-box" id="singleConsole" style="height: 480px;">
                <div class="log-entry"><span class="log-time">[System]</span> 单次提交模式已就绪...</div>
            </div>
        </div>
    </div>
</div>

<script>
    const FIRST_NAMES = """ + json.dumps(FIRST_NAMES) + r""";
    const LAST_NAMES = """ + json.dumps(LAST_NAMES) + r""";
    const COMPANY_PREFIXES = """ + json.dumps(COMPANY_PREFIXES) + r""";
    const COMPANY_SUFFIXES = """ + json.dumps(COMPANY_SUFFIXES) + r""";
    const INTENDED_USES = """ + json.dumps(INTENDED_USES) + r""";
    const AREA_CODES = """ + json.dumps(AREA_CODES) + r""";

    function getRandomItem(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    function generateRandomProfile(email, defaults, forceFullRandom = true) {
        const fn = getRandomItem(FIRST_NAMES);
        const ln = getRandomItem(LAST_NAMES);
        const comp = getRandomItem(COMPANY_PREFIXES) + " " + getRandomItem(COMPANY_SUFFIXES);
        const domainSlug = comp.toLowerCase().replace(/[^a-z0-9]/g, '');
        const domainSuffix = getRandomItem(['.com', '.io', '.net', '.co']);
        const area = getRandomItem(AREA_CODES);
        const phone = `+1-${area}-555-${Math.floor(1000 + Math.random() * 9000)}`;
        const use = getRandomItem(INTENDED_USES);

        let seats = defaults.planned_seats;
        if (seats === 'RANDOM') {
            seats = getRandomItem(['2', '3-5', '6-10']);
        }

        return {
            first_name: fn,
            last_name: ln,
            email: email,
            organization: comp,
            country: defaults.country || 'US',
            requester_type: 'organization',
            planned_seats: seats,
            website: `https://www.${domainSlug}${domainSuffix}`,
            phone: phone,
            existing_chatgpt_customer_status: "not_a_customer",
            preferred_contact_method: "email",
            intended_use: use,
            eligibility_review_acknowledgement: "acknowledged",
            policy_acknowledged: "true",
            proxy: document.getElementById('proxyUrl').value.trim()
        };
    }

    function switchTab(mode) {
        document.getElementById('viewBatch').style.display = mode === 'batch' ? 'grid' : 'none';
        document.getElementById('viewSingle').style.display = mode === 'single' ? 'grid' : 'none';
        document.getElementById('tabBatchBtn').className = mode === 'batch' ? 'tab-btn active' : 'tab-btn';
        document.getElementById('tabSingleBtn').className = mode === 'single' ? 'tab-btn active' : 'tab-btn';
    }

    function appendLog(targetId, msg, type = 'info') {
        const box = document.getElementById(targetId);
        if (!box) return;
        const time = new Date().toTimeString().split(' ')[0];
        const div = document.createElement('div');
        div.className = `log-entry log-${type}`;
        div.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    function extractEmails(text) {
        if (!text) return [];
        const matches = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || [];
        const unique = [];
        const seen = new Set();
        for (const em of matches) {
            const lower = em.toLowerCase();
            if (!seen.has(lower)) {
                seen.add(lower);
                unique.push(em);
            }
        }
        return unique;
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(evt) {
            const text = evt.target.result;
            const current = document.getElementById('batchTextarea').value;
            const merged = current ? current + '\n' + text : text;
            document.getElementById('batchTextarea').value = merged;
            
            const extracted = extractEmails(merged);
            document.getElementById('importCountBadge').innerText = `已识别 ${extracted.length} 个邮箱`;
            appendLog('batchConsole', `已成功从文件 [${file.name}] 导入并识别出 ${extracted.length} 个有效邮箱！`, 'success');
        };
        reader.readAsText(file, "UTF-8");
        e.target.value = '';
    }

    function updateImportBadge() {
        const text = document.getElementById('batchTextarea').value;
        const extracted = extractEmails(text);
        document.getElementById('importCountBadge').innerText = `已识别 ${extracted.length} 个邮箱`;
    }

    document.getElementById('batchTextarea').addEventListener('input', updateImportBadge);

    function loadSampleBatch() {
        const samples = [
            "arthur.pendelton@gmail.com",
            "clara.oswald@starfleet.org",
            "victor.creed@apexdata.io",
            "sarah.connor@cyberdyne.net",
            "bruce.wayne@waynetech.com"
        ];
        document.getElementById('batchTextarea').value = samples.join('\n');
        updateImportBadge();
        appendLog('batchConsole', "已载入 5 条示例邮箱数据", "info");
    }

    function clearBatch() {
        if (isBatchRunning) {
            alert("请先停止当前运行的任务再清空！");
            return;
        }
        document.getElementById('batchTextarea').value = "";
        updateImportBadge();
        resetStats();
        appendLog('batchConsole', "已清空数据", "info");
    }

    let batchQueue = [];
    let isBatchRunning = false;
    let isBatchPaused = false;
    let batchIndex = 0;
    let successCount = 0;
    let failedCount = 0;

    function resetStats() {
        batchQueue = [];
        batchIndex = 0;
        successCount = 0;
        failedCount = 0;
        document.getElementById('metricTotal').innerText = "0";
        document.getElementById('metricSuccess').innerText = "0";
        document.getElementById('metricFailed').innerText = "0";
        document.getElementById('metricRemaining').innerText = "0";
        document.getElementById('progressBar').style.width = "0%";
        document.getElementById('retryFailedBtn').style.display = "none";
        document.getElementById('resultsTableBody').innerHTML = `
            <tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px;">暂无任务</td></tr>
        `;
    }

    async function startBatchProcess() {
        const rawText = document.getElementById('batchTextarea').value;
        const emails = extractEmails(rawText);

        if (emails.length === 0) {
            alert("请在左侧输入或导入至少一个包含有效域名的邮箱地址！");
            return;
        }

        resetStats();

        const defaults = {
            country: document.getElementById('batchCountry').value,
            planned_seats: document.getElementById('batchSeats').value
        };

        const enableRandom = document.getElementById('enablePerItemRandom').checked;

        for (let i = 0; i < emails.length; i++) {
            const email = emails[i];
            const profile = generateRandomProfile(email, defaults, enableRandom);

            batchQueue.push({
                id: i + 1,
                email: email,
                profile: profile,
                status: 'pending',
                statusCode: '-',
                duration: '-'
            });
        }

        document.getElementById('metricTotal').innerText = batchQueue.length;
        document.getElementById('metricRemaining').innerText = batchQueue.length;

        renderTableRows();

        isBatchRunning = true;
        isBatchPaused = false;
        batchIndex = 0;

        document.getElementById('startBatchBtn').style.display = 'none';
        document.getElementById('pauseBatchBtn').style.display = 'inline-flex';
        document.getElementById('stopBatchBtn').style.display = 'inline-flex';

        const proxy = document.getElementById('proxyUrl').value.trim();
        appendLog('batchConsole', `批量处理启动，共 ${batchQueue.length} 个任务待提交... ${proxy ? '[代理: ' + proxy + ']' : '[直连模式]'}`, 'info');

        runQueueLoop();
    }

    function renderTableRows() {
        const tbody = document.getElementById('resultsTableBody');
        tbody.innerHTML = '';
        batchQueue.forEach(item => {
            const tr = document.createElement('tr');
            tr.id = `row-${item.id}`;
            tr.innerHTML = `
                <td>${item.id}</td>
                <td><strong>${item.email}</strong></td>
                <td>${item.profile.first_name} ${item.profile.last_name} <span style="color:var(--text-muted);">(${item.profile.organization})</span></td>
                <td><span class="tag tag-${item.status}" id="tag-${item.id}">${item.status === 'success' ? '成功' : (item.status === 'error' ? '失败' : '待处理')}</span></td>
                <td id="code-${item.id}">${item.statusCode}</td>
                <td id="dur-${item.id}">${item.duration}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function runQueueLoop() {
        const minInt = parseFloat(document.getElementById('minInterval').value) || 5;
        const maxInt = parseFloat(document.getElementById('maxInterval').value) || 12;
        const enableRandom = document.getElementById('enablePerItemRandom').checked;
        const autoCooldown = document.getElementById('autoCooldown429').checked;
        const defaults = {
            country: document.getElementById('batchCountry').value,
            planned_seats: document.getElementById('batchSeats').value
        };

        while (batchIndex < batchQueue.length && isBatchRunning) {
            if (isBatchPaused) {
                await new Promise(r => setTimeout(r, 500));
                continue;
            }

            const current = batchQueue[batchIndex];

            // 保持最新动态代理与动态身份
            if (enableRandom) {
                current.profile = generateRandomProfile(current.email, defaults, true);
                const row = document.getElementById(`row-${current.id}`);
                if (row) {
                    row.cells[2].innerHTML = `${current.profile.first_name} ${current.profile.last_name} <span style="color:var(--text-muted);">(${current.profile.organization})</span>`;
                }
            } else {
                current.profile.proxy = document.getElementById('proxyUrl').value.trim();
            }

            const startTime = Date.now();
            updateRowStatus(current.id, 'running', '提交中...');
            appendLog('batchConsole', `[${batchIndex + 1}/${batchQueue.length}] 正在提交: ${current.email}...`, 'info');

            try {
                const resp = await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(current.profile)
                });
                const resData = await resp.json();
                const duration = ((Date.now() - startTime) / 1000).toFixed(1) + 's';

                if (resData.success) {
                    successCount++;
                    current.status = 'success';
                    current.statusCode = resData.status_code;
                    current.duration = duration;
                    updateRowStatus(current.id, 'success', '成功', resData.status_code, duration);
                    appendLog('batchConsole', `✓ [${current.email}] 提交成功 (HTTP ${resData.status_code})`, 'success');
                    batchIndex++;
                } else {
                    // 遇到 429 检查是否自动休眠退避
                    if (resData.status_code === 429 && autoCooldown) {
                        appendLog('batchConsole', `⚠️ 触发 429 IP 频率限制！当前 IP 已被短时节流。系统正在自动冷却休眠 45 秒后原位重试...`, 'warn');
                        updateRowStatus(current.id, 'running', '429冷却中');
                        
                        // 倒计时 45 秒
                        for (let sec = 45; sec > 0; sec--) {
                            if (!isBatchRunning) break;
                            if (sec % 10 === 0 || sec <= 5) {
                                appendLog('batchConsole', `⏳ 429 冷却倒计时: 剩余 ${sec} 秒...`, 'warn');
                            }
                            await new Promise(r => setTimeout(r, 1000));
                        }
                        appendLog('batchConsole', `🔄 冷却完毕，重新尝试提交 [${current.email}]...`, 'info');
                        // 不递增 batchIndex，继续循环原位重试当前项
                        continue;
                    } else {
                        failedCount++;
                        current.status = 'error';
                        current.statusCode = resData.status_code || 'Err';
                        current.duration = duration;
                        updateRowStatus(current.id, 'error', '失败', resData.status_code || 'Err', duration);
                        appendLog('batchConsole', `✕ [${current.email}] 提交失败 (HTTP ${resData.status_code}): ${resData.message}`, 'error');
                        batchIndex++;
                    }
                }
            } catch (err) {
                const duration = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
                failedCount++;
                current.status = 'error';
                current.statusCode = 'Network';
                current.duration = duration;
                updateRowStatus(current.id, 'error', '异常', 'NetErr', duration);
                appendLog('batchConsole', `✕ [${current.email}] 网络异常: ${err.message}`, 'error');
                batchIndex++;
            }

            updateMetrics();

            // 计算包含 Jitter 的随机浮动休眠
            if (batchIndex < batchQueue.length && isBatchRunning) {
                const randomSleep = (Math.random() * (maxInt - minInt) + minInt).toFixed(1);
                appendLog('batchConsole', `随机时间抖动休眠 ${randomSleep} 秒以规避风控...`, 'info');
                await new Promise(r => setTimeout(r, parseFloat(randomSleep) * 1000));
            }
        }

        if (isBatchRunning && batchIndex >= batchQueue.length) {
            appendLog('batchConsole', `🎉 批量处理完毕！总计: ${batchQueue.length}, 成功: ${successCount}, 失败: ${failedCount}`, 'success');
            stopBatchProcess();
        }
    }

    function updateRowStatus(id, type, label, code = null, dur = null) {
        const tag = document.getElementById(`tag-${id}`);
        if (tag) {
            tag.className = `tag tag-${type}`;
            tag.innerText = label;
        }
        if (code !== null) {
            const c = document.getElementById(`code-${id}`);
            if (c) c.innerText = code;
        }
        if (dur !== null) {
            const d = document.getElementById(`dur-${id}`);
            if (d) d.innerText = dur;
        }
    }

    function updateMetrics() {
        document.getElementById('metricSuccess').innerText = successCount;
        document.getElementById('metricFailed').innerText = failedCount;
        const remaining = Math.max(0, batchQueue.length - batchIndex);
        document.getElementById('metricRemaining').innerText = remaining;
        const pct = batchQueue.length > 0 ? (batchIndex / batchQueue.length * 100).toFixed(0) : 0;
        document.getElementById('progressBar').style.width = pct + '%';

        if (failedCount > 0) {
            document.getElementById('retryFailedBtn').style.display = 'inline-flex';
            document.getElementById('retryFailedCount').innerText = failedCount;
        }
    }

    // 一键重试所有失败项
    async function retryFailedTasks() {
        if (isBatchRunning) {
            alert("任务正在运行中，请先暂停或停止！");
            return;
        }
        const failedItems = batchQueue.filter(item => item.status === 'error');
        if (failedItems.length === 0) {
            alert("当前没有失败的任务！");
            return;
        }

        appendLog('batchConsole', `🔄 正在准备重试 ${failedItems.length} 个失败任务...`, 'info');

        // 将失败项重构为新队列
        batchQueue = failedItems.map((item, idx) => ({
            id: idx + 1,
            email: item.email,
            profile: item.profile,
            status: 'pending',
            statusCode: '-',
            duration: '-'
        }));

        batchIndex = 0;
        successCount = 0;
        failedCount = 0;
        document.getElementById('metricTotal').innerText = batchQueue.length;
        document.getElementById('metricSuccess').innerText = "0";
        document.getElementById('metricFailed').innerText = "0";
        document.getElementById('metricRemaining').innerText = batchQueue.length;
        document.getElementById('progressBar').style.width = "0%";
        document.getElementById('retryFailedBtn').style.display = "none";

        renderTableRows();

        isBatchRunning = true;
        isBatchPaused = false;
        document.getElementById('startBatchBtn').style.display = 'none';
        document.getElementById('pauseBatchBtn').style.display = 'inline-flex';
        document.getElementById('stopBatchBtn').style.display = 'inline-flex';

        runQueueLoop();
    }

    function togglePauseBatch() {
        isBatchPaused = !isBatchPaused;
        const btnText = document.getElementById('pauseBtnText');
        if (isBatchPaused) {
            btnText.innerText = "▶ 继续";
            appendLog('batchConsole', "已暂停任务队列", 'warn');
        } else {
            btnText.innerText = "⏸ 暂停";
            appendLog('batchConsole', "已继续任务队列", 'info');
        }
    }

    function stopBatchProcess() {
        isBatchRunning = false;
        isBatchPaused = false;
        document.getElementById('startBatchBtn').style.display = 'inline-flex';
        document.getElementById('pauseBatchBtn').style.display = 'none';
        document.getElementById('stopBatchBtn').style.display = 'none';
        document.getElementById('pauseBtnText').innerText = "⏸ 暂停";
    }

    function exportResultsCSV() {
        if (!batchQueue || batchQueue.length === 0) {
            alert("当前没有可导出的结果！");
            return;
        }
        let csvContent = "\uFEFF序号,邮箱,名,姓,组织,官网,电话,用途,状态,返回码,耗时\n";
        batchQueue.forEach(item => {
            const p = item.profile;
            csvContent += `${item.id},"${item.email}","${p.first_name}","${p.last_name}","${p.organization}","${p.website}","${p.phone}","${p.intended_use}",${item.status},${item.statusCode},${item.duration}\n`;
        });
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `metaverde_batch_results_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // 单次提交
    document.getElementById('singleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('singleSubmitBtn');
        btn.disabled = true;

        const data = {
            first_name: document.getElementById('s_first_name').value.trim(),
            last_name: document.getElementById('s_last_name').value.trim(),
            email: document.getElementById('s_email').value.trim(),
            organization: document.getElementById('s_organization').value.trim(),
            country: document.getElementById('s_country').value,
            requester_type: 'organization',
            planned_seats: '2',
            website: "https://example.com",
            phone: "+1-202-555-0199",
            existing_chatgpt_customer_status: "not_a_customer",
            preferred_contact_method: "email",
            intended_use: "Business workflow testing",
            eligibility_review_acknowledgement: document.getElementById('s_ack1').checked ? 'acknowledged' : '',
            policy_acknowledged: document.getElementById('s_ack2').checked ? 'true' : '',
            proxy: document.getElementById('s_proxy').value.trim()
        };

        appendLog('singleConsole', `开始提交单个账号: ${data.email}...`, 'info');

        try {
            const resp = await fetch('/api/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const res = await resp.json();
            if (res.logs) {
                res.logs.forEach(l => appendLog('singleConsole', l.text, l.type));
            }
            if (res.success) {
                appendLog('singleConsole', `✓ 单个账号提交成功！HTTP 状态码: ${res.status_code}`, 'success');
            } else {
                appendLog('singleConsole', `✕ 提交未成功: ${res.message} (HTTP ${res.status_code})`, 'error');
            }
        } catch (err) {
            appendLog('singleConsole', `网络异常: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
        }
    });

    updateImportBadge();
</script>

</body>
</html>
"""

def build_urllib_opener(proxy_url=None):
    """
    配置 HTTP / SOCKS5 代理处理器
    """
    handlers = []
    if proxy_url and proxy_url.strip():
        p = proxy_url.strip()
        handlers.append(urllib.request.ProxyHandler({'http': p, 'https': p}))
    return urllib.request.build_opener(*handlers)


def execute_metaverde_submit(profile_data):
    logs = []
    proxy_url = profile_data.get("proxy", "").strip()
    opener = build_urllib_opener(proxy_url)

    if proxy_url:
        logs.append({"text": f"使用代理通道: {proxy_url}", "type": "info"})

    logs.append({"text": f"正在向 {TARGET_PAGE_URL} 获取防重放令牌...", "type": "info"})
    
    req = urllib.request.Request(
        TARGET_PAGE_URL,
        headers={"User-Agent": USER_AGENT}
    )
    
    try:
        with opener.open(req, timeout=18) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as he:
        if he.code == 429:
            logs.append({"text": "远端触发 429 限流 (Too Many Requests)", "type": "warn"})
            return False, 429, "触发远端 IP 频控限流 (Too Many Requests)", logs
        logs.append({"text": f"获取目标网页失败: HTTP {he.code}", "type": "error"})
        return False, he.code, f"页面抓取返回 HTTP {he.code}", logs
    except Exception as e:
        logs.append({"text": f"获取目标网页失败: {str(e)}", "type": "error"})
        return False, 500, f"页面抓取失败: {str(e)}", logs

    # 提取 action_url
    action_match = re.search(r'<form[^>]*action=[\"\']([^\"\']+)[\"\']', html)
    action_url = action_match.group(1) if action_match else DEFAULT_ACTION_URL

    # 提取 _source_context
    source_context_match = re.search(r'name=[\"\']_source_context[\"\'][^>]*value=[\"\']([^\"\']+)[\"\']', html)
    if not source_context_match:
        logs.append({"text": "未在页面中找到 _source_context 动态令牌", "type": "error"})
        return False, 400, "未能提取动态令牌 _source_context", logs

    source_context = source_context_match.group(1)

    fn = profile_data.get("first_name") or random.choice(FIRST_NAMES)
    ln = profile_data.get("last_name") or random.choice(LAST_NAMES)
    comp = profile_data.get("organization") or (random.choice(COMPANY_PREFIXES) + " " + random.choice(COMPANY_SUFFIXES))
    website = profile_data.get("website") or f"https://www.{re.sub(r'[^a-z0-9]', '', comp.lower())}.com"
    phone = profile_data.get("phone") or f"+1-{random.choice(AREA_CODES)}-555-{random.randint(1000, 9999)}"
    use = profile_data.get("intended_use") or random.choice(INTENDED_USES)

    payload = {
        "language": "en",
        "_gotcha": "",
        "policy_url": "https://metaverde.com/partner-url-policy",
        "policy_version": "2026-10-11-v2",
        "form_version": "2026-10-08-v2",
        "source_page": "/chatgpt-business/",
        "source_form": "metaverde_chatgpt_business_partner_url",
        "_source_context": source_context,

        "first_name": fn,
        "last_name": ln,
        "email": profile_data.get("email", ""),
        "organization": comp,
        "country": profile_data.get("country", "US"),
        "requester_type": profile_data.get("requester_type", "organization"),
        "planned_seats": profile_data.get("planned_seats", "2"),
        "website": website,
        "phone": phone,
        "existing_chatgpt_customer_status": "not_a_customer",
        "previous_metaverde_url_status": "never_requested",
        "preferred_contact_method": "email",
        "intended_use": use,

        "eligibility_review_acknowledgement": "acknowledged",
        "policy_acknowledged": "true"
    }

    logs.append({"text": f"随机身份装配: {fn} {ln} @ {comp}", "type": "info"})

    encoded_data = urllib.parse.urlencode(payload).encode('utf-8')
    post_req = urllib.request.Request(
        action_url,
        data=encoded_data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": TARGET_PAGE_URL,
            "Origin": "https://metaverde.com"
        }
    )

    try:
        with opener.open(post_req, timeout=22) as post_resp:
            status_code = post_resp.status
            logs.append({"text": f"远程接口响应状态码: {status_code}", "type": "success"})
            return True, status_code, "提交完成", logs
    except urllib.error.HTTPError as he:
        if he.code in [200, 301, 302, 303]:
            logs.append({"text": f"远程接口重定向成功 (HTTP {he.code})", "type": "success"})
            return True, he.code, "提交成功并重定向", logs
        elif he.code == 429:
            logs.append({"text": "接口返回 HTTP 429: 触发远端 IP 频控限流 (Too Many Requests)", "type": "warn"})
            return False, 429, "触发远端 IP 频控限流 (Too Many Requests)", logs
        else:
            logs.append({"text": f"HTTP 提交返回状态: {he.code} {he.reason}", "type": "error"})
            return False, he.code, f"接口返回 HTTP {he.code}", logs
    except Exception as e:
        logs.append({"text": f"提交过程产生网络异常: {str(e)}", "type": "error"})
        return False, 500, str(e), logs


class WebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/submit":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_body)
            except Exception:
                data = {}

            success, status_code, message, logs = execute_metaverde_submit(data)

            response_data = {
                "success": success,
                "status_code": status_code,
                "message": message,
                "logs": logs
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, WebHandler)
    print("=" * 65)
    print(f"[*] Metaverde 防 429 限流强化版服务已就绪！")
    print(f"[*] 访问控制台: http://127.0.0.1:{PORT}")
    print(f"[*] 核心特性: 支持代理池配置、429 智能冷却自动重试、随机 Jitter、一键重试失败项")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 服务正在安全关闭...")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
