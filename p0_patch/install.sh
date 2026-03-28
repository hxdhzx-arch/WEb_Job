#!/bin/bash
set -e

# ═══════════════════════════════════════
# P0 补丁安装脚本 — 云端简历存储 + 验证码绑定
# ═══════════════════════════════════════
# 用法: cd ~/job_WEB && bash p0_patch/install.sh
# ═══════════════════════════════════════

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$PATCH_DIR/.." && pwd)"

echo "══════════════════════════════════════"
echo "  P0 补丁安装 — 云端存储 + 验证码"
echo "══════════════════════════════════════"
echo ""
echo "  项目目录: $PROJECT_DIR"
echo "  补丁目录: $PATCH_DIR"
echo ""

cd "$PROJECT_DIR"

# ── 0. 安全检查 ──
if [ ! -f "app.py" ]; then
    echo "[错误] 未找到 app.py，请确认在项目根目录下运行"
    echo "  正确用法: cd ~/job_WEB && bash p0_patch/install.sh"
    exit 1
fi

# ── 1. 备份 ──
BACKUP="backups/pre_p0_$(date +%Y%m%d_%H%M%S)"
echo "[1/6] 备份现有文件 → $BACKUP/"
mkdir -p "$BACKUP/services" "$BACKUP/static" "$BACKUP/templates"

for f in app.py config.py .env.example; do
    [ -f "$f" ] && cp "$f" "$BACKUP/$f"
done
for f in services/database.py static/credits.js static/script.js static/style.css templates/credits_components.html templates/resume_builder.html; do
    [ -f "$f" ] && cp "$f" "$BACKUP/$f"
done
echo "  ✓ 备份完成"

# ── 2. 替换后端文件 ──
echo "[2/6] 安装后端文件..."
cp "$PATCH_DIR/app.py" app.py
cp "$PATCH_DIR/config.py" config.py
cp "$PATCH_DIR/services/database.py" services/database.py
cp "$PATCH_DIR/services/verify.py" services/verify.py
cp "$PATCH_DIR/services/email_sender.py" services/email_sender.py
cp "$PATCH_DIR/.env.example" .env.example
echo "  ✓ app.py / config.py / database.py / verify.py / email_sender.py"

# ── 3. 替换前端文件 ──
echo "[3/6] 安装前端文件..."
cp "$PATCH_DIR/static/credits.js" static/credits.js
cp "$PATCH_DIR/static/cloud_sync.js" static/cloud_sync.js
cp "$PATCH_DIR/templates/credits_components.html" templates/credits_components.html
echo "  ✓ credits.js / cloud_sync.js / credits_components.html"

# ── 4. 补丁 script.js — 注入 CloudSync 自动保存 ──
echo "[4/6] 补丁 script.js（注入云端自动保存）..."

if grep -q "CloudSync" static/script.js; then
    echo "  ⏭ script.js 已包含 CloudSync，跳过"
else
    # 替换 liveRender 的定义
    sed -i.bak 's|var liveRender=debounce(function(){renderPreview();saveToLocal();},80);|var liveRender=debounce(function(){renderPreview();saveToLocal();if(typeof CloudSync!=="undefined")CloudSync.scheduleAutoSave();},80);|' static/script.js

    sed -i 's|var liveRenderSlow=debounce(function(){renderPreview();saveToLocal();},150);|var liveRenderSlow=debounce(function(){renderPreview();saveToLocal();if(typeof CloudSync!=="undefined")CloudSync.scheduleAutoSave();},150);|' static/script.js

    # 验证是否成功
    if grep -q "CloudSync" static/script.js; then
        echo "  ✓ liveRender / liveRenderSlow 已注入 CloudSync"
    else
        echo "  ⚠ 自动注入失败，请手动修改（见 README）"
    fi
fi

# ── 5. 补丁 resume_builder.html — 加载 cloud_sync.js + 简历列表 UI ──
echo "[5/6] 补丁 resume_builder.html..."

if grep -q "cloud_sync.js" templates/resume_builder.html; then
    echo "  ⏭ resume_builder.html 已包含 cloud_sync.js，跳过"
else
    # 5a. 在 script.js 引用后面加入 cloud_sync.js
    sed -i.bak 's|<script src="/static/script.js"></script>|<script src="/static/script.js"></script>\n<script src="/static/cloud_sync.js"></script>|' templates/resume_builder.html

    # 5b. 在 mode-toggle-wrapper 前面插入简历列表容器 + 新建按钮
    sed -i 's|<!-- Mode Toggle -->|<!-- Cloud Resume List -->\n  <div id="cloud-resume-list" class="cloud-resume-list" style="display:none"></div>\n  <button class="btn-add" onclick="CloudSync.createNew()" id="cloud-new-btn" style="margin-bottom:8px;border-style:solid;border-color:rgba(124,58,237,.2);color:#7C3AED;display:none">+ 新建简历</button>\n\n  <!-- Mode Toggle -->|' templates/resume_builder.html

    if grep -q "cloud_sync.js" templates/resume_builder.html; then
        echo "  ✓ cloud_sync.js 引用 + 简历列表容器已插入"
    else
        echo "  ⚠ 自动注入失败，请手动修改（见 README）"
    fi
fi

# ── 6. 补丁 style.css — 追加简历列表样式 ──
echo "[6/6] 补丁 style.css（追加云端简历列表样式）..."

if grep -q "cloud-resume-list" static/style.css; then
    echo "  ⏭ style.css 已包含简历列表样式，跳过"
else
    cat >> static/style.css << 'CSSEOF'

/* ═══ Cloud Resume List (P0 Patch) ═══ */
.cloud-resume-list{margin-bottom:10px;max-height:180px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--bg)}
.cloud-resume-list::-webkit-scrollbar{width:4px}
.cloud-resume-list::-webkit-scrollbar-thumb{background:#D1D5DB;border-radius:2px}
.crl-item{display:flex;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);transition:background .15s;cursor:pointer}
.crl-item:last-child{border-bottom:none}
.crl-item:hover{background:rgba(0,122,255,.04)}
.crl-item.active{background:rgba(0,122,255,.08)}
.crl-info{flex:1;min-width:0}
.crl-title{display:block;font-size:.8rem;font-weight:600;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.crl-default{display:inline-block;padding:0 5px;background:#EEF2FF;color:#7C3AED;border-radius:3px;font-size:.6rem;font-weight:700;vertical-align:middle;margin-left:4px}
.crl-meta{display:block;font-size:.68rem;color:var(--text-hint);margin-top:1px}
.crl-del{background:none;border:none;color:#D1D5DB;font-size:16px;cursor:pointer;padding:4px;border-radius:4px;transition:all .15s;flex-shrink:0}
.crl-del:hover{color:#EF4444;background:rgba(239,68,68,.08)}
.crl-empty{padding:14px;text-align:center;font-size:.78rem;color:var(--text-hint)}
CSSEOF
    echo "  ✓ 简历列表 CSS 已追加"
fi

# ── 完成 ──
echo ""
echo "══════════════════════════════════════"
echo "  ✅ P0 补丁安装完成！"
echo "══════════════════════════════════════"
echo ""
echo "  新增功能:"
echo "    • 验证码绑定（邮箱/手机号）"
echo "    • 验证码登录（换设备恢复）"
echo "    • 云端简历自动同步（绑定后）"
echo "    • 多简历管理（最多 10 份）"
echo ""
echo "  新增 API 路由:"
echo "    POST /api/verify/send    — 发送验证码"
echo "    POST /api/auth/login     — 验证码登录"
echo "    POST /api/resumes/save   — 保存简历"
echo "    GET  /api/resumes/list   — 简历列表"
echo "    GET  /api/resumes/load   — 加载简历"
echo "    POST /api/resumes/delete — 删除简历"
echo ""
echo "  下一步:"
echo "    1. 编辑 .env 添加 SMTP 配置（可选，不配则验证码打印到终端）"
echo "    2. bash run.sh 启动服务"
echo "    3. 首次启动自动创建 verify_codes / resumes 表"
echo ""
echo "  备份位置: $BACKUP/"
echo "  回滚方法: cp -r $BACKUP/* ."
echo ""
