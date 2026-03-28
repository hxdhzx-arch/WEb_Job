# P0 补丁 — 云端简历存储 + 验证码绑定

## 一键安装

```bash
# 1. 备份 .env（重要！补丁不会动你的 .env）
cp ~/job_WEB/.env ~/Desktop/.env.backup

# 2. 进入项目目录
cd ~/job_WEB

# 3. 解压补丁（假设下载到 Downloads）
unzip -o ~/Downloads/p0_cloud_save.zip -d ~/job_WEB/

# 4. 运行安装脚本
bash p0_patch/install.sh

# 5. 启动
bash run.sh
```

## 安装脚本做了什么？

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 备份 | 所有被修改的文件备份到 `backups/pre_p0_时间戳/` |
| 2 | 替换后端 | `app.py` / `config.py` / `database.py` + 新增 `verify.py` / `email_sender.py` |
| 3 | 替换前端 | `credits.js` / `credits_components.html` + 新增 `cloud_sync.js` |
| 4 | 补丁 script.js | 在 `liveRender` 中注入 `CloudSync.scheduleAutoSave()` |
| 5 | 补丁 resume_builder.html | 添加 `cloud_sync.js` 引用 + 简历列表容器 |
| 6 | 补丁 style.css | 追加简历列表 CSS 样式 |

## 新增功能

- **验证码绑定**：输入邮箱 → 收验证码 → 输入验证码 → 绑定成功
- **验证码登录**：换设备后输入邮箱 → 验证码 → 恢复所有简历和算力
- **云端自动同步**：绑定后编辑简历 3 秒后自动保存到云端
- **多简历管理**：最多 10 份，左侧列表切换，带默认标记

## 新增 API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/verify/send` | POST | 发送验证码 |
| `/api/auth/login` | POST | 验证码登录 |
| `/api/resumes/save` | POST | 保存简历 |
| `/api/resumes/list` | GET | 简历列表 |
| `/api/resumes/load` | GET | 加载简历 |
| `/api/resumes/delete` | POST | 删除简历 |

## SMTP 配置（可选）

不配置 SMTP 时，验证码会打印到终端（开发模式），方便本地测试。

要启用邮件发送，在 `.env` 中添加：

```
# QQ 邮箱
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的QQ邮箱@qq.com
SMTP_PASS=你的授权码
SMTP_FROM=简历AI <你的QQ邮箱@qq.com>
```

获取 QQ 邮箱授权码：设置 → 账户 → POP3/SMTP 服务 → 开启 → 生成授权码

## 安全改进

- ✅ 修复 `bind_account` 中的 SQL 注入漏洞（`.format()` → 参数化查询）
- ✅ 验证码 5 分钟过期 + 60 秒冷却 + 5 次错误自动作废
- ✅ 同一邮箱每小时最多发 5 次验证码
- ✅ 简历接口校验 user_id 归属，防越权访问

## 回滚

```bash
cd ~/job_WEB
cp -r backups/pre_p0_最近的时间戳/* .
```
