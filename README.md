# 简历 AI Pro — 免费智能简历优化工具

基于大语言模型的一站式简历优化平台：AI 诊断 → 智能润色 → 精美生成。

## ✨ 核心功能

- **简历诊断** — 5 维度评分 + 逐条改进建议
- **JD 匹配** — ATS 机筛通过率模拟 + 缺失关键词一键融合
- **AI 职业顾问** — 自然语言描述背景，AI 推荐岗位 + 生成 JD
- **简历生成器 Pro** — 14 套专业模板 / 推荐与自定义双模式 / 实时预览
- **AI 智能扩写** — 一句大白话 → STAR 法则专业描述
- **PDF 解析** — 拖拽旧简历，AI 自动结构化填充
- **AI 一键排版** — 按字数自动调整字号/行距，一页 A4 完美呈现
- **职场通工具箱** — 税后薪资/五险一金计算、Offer 对比、JD 解析 + 简历定制建议

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/resume-ai.git
cd resume-ai

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 Gemini API Key（免费获取: https://aistudio.google.com/apikey）

# 3. 启动
bash run.sh

# 4. 访问
# http://localhost:8000
```

## 📁 项目结构

```
├── app.py                 # Flask 主入口 (6 个 API 路由)
├── config.py              # API Key 轮询池
├── run.sh                 # 一键启动脚本
├── .env.example           # 环境变量示例
├── requirements.txt       # Python 依赖
├── services/
│   ├── gemini_client.py   # Gemini API 调用 (原生 HTTP)
│   ├── resume_analyzer.py # 简历诊断逻辑
│   └── jd_matcher.py      # JD 匹配逻辑
├── prompts/
│   ├── resume_prompt.txt  # 诊断提示词
│   └── jd_prompt.txt      # 匹配提示词
├── static/
│   ├── script.js          # 前端交互 (14模板引擎 + 状态管理)
│   └── style.css          # 全站样式
└── templates/
    ├── index.html          # 首页 (Mac Mockup 动画)
    ├── resume.html         # 简历诊断页
    ├── jd_match.html       # JD 匹配页 (AI 职业顾问)
    └── resume_builder.html # 简历编辑器 Pro
```

## 🛠 技术栈

- **后端**: Python 3.9+ / Flask / 原生 urllib (绕过 SDK 编码问题)
- **前端**: 纯 Vanilla JS + HTML/CSS (零框架依赖)
- **AI**: Google Gemini API (免费额度) / Groq (备选)
- **PDF**: PyMuPDF (fitz)

## ⚠️ 注意

- `.env` 文件包含 API Key，已被 `.gitignore` 排除，**不会上传到 GitHub**
- 首次运行 `run.sh` 会自动安装依赖
- macOS 用户请使用 8000 端口 (5000 被 AirPlay 占用)

## 📜 License

MIT
