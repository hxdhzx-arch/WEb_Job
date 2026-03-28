# 信任合规补丁

## 一键安装

```bash
cd ~/job_WEB
unzip -o ~/Downloads/trust_patch.zip -d ~/job_WEB/
bash trust_patch/install.sh
```

## 修复内容

| # | 位置 | 原文（有问题） | 修正后 |
|---|------|--------------|--------|
| 1 | privacy.html | 「数据不会被写入任何数据库」 | 如实描述：未绑定=内存处理不持久化；绑定后=SQLite 云端存储 |
| 2 | index.html 首页 | 「绝不上传云端存储」 | 改为「个人信息 AI 处理前自动脱敏」+ 链接 |
| 3 | privacy.html | 「不使用第三方追踪 Cookie」 | 如实披露 FingerprintJS 及用途 |
| 4 | terms.html | 无第三方 AI 披露 | 新增 Google Gemini API 数据流转说明 |
| 5 | 各页面 trust-badge | 「分析完成后数据立即销毁」 | 区分绑定/未绑定 + 第三方 AI 说明 |
| 6 | terms.html | 无 AI 内容免责 | 新增生成内容准确性声明 |
