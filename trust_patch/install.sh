#!/bin/bash
set -e

# ═══════════════════════════════════════
# 信任合规补丁 — 修复隐私声明与实际行为的矛盾
# ═══════════════════════════════════════
# 用法: cd ~/job_WEB && bash trust_patch/install.sh
# ═══════════════════════════════════════

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$PATCH_DIR/.." && pwd)"

echo "══════════════════════════════════════"
echo "  信任合规补丁安装"
echo "══════════════════════════════════════"

cd "$PROJECT_DIR"

if [ ! -f "app.py" ]; then
    echo "[错误] 未找到 app.py，请在项目根目录下运行"
    exit 1
fi

# ── 1. 备份 ──
BACKUP="backups/pre_trust_$(date +%Y%m%d_%H%M%S)"
echo "[1/5] 备份 → $BACKUP/"
mkdir -p "$BACKUP/templates"
for f in templates/privacy.html templates/terms.html templates/index.html templates/resume.html templates/jd_match.html templates/resume_builder.html; do
    [ -f "$f" ] && cp "$f" "$BACKUP/$f"
done
echo "  ✓ 备份完成"

# ── 2. 替换隐私政策和用户协议 ──
echo "[2/5] 替换 privacy.html + terms.html..."
cp "$PATCH_DIR/templates/privacy.html" templates/privacy.html
cp "$PATCH_DIR/templates/terms.html" templates/terms.html
echo "  ✓ 隐私政策已重写（如实描述 Gemini API + SQLite + FingerprintJS）"
echo "  ✓ 用户协议已重写（第三方 AI 披露 + 生成内容免责）"

# ── 3. 修复 index.html 首页信任徽章 ──
echo "[3/5] 修复 index.html 信任徽章..."

# 原文: "简历数据自动脱敏 · 阅后即焚 · 绝不上传云端存储"
# 修复: 去掉"阅后即焚"和"绝不上传云端存储"的绝对表述
if grep -q "绝不上传云端存储" templates/index.html; then
    sed -i.bak 's|简历数据自动脱敏 · 阅后即焚 · 绝不上传云端存储|个人信息 AI 处理前自动脱敏 · 详见<a href="/privacy" style="color:#059669;text-decoration:underline">隐私政策</a>|g' templates/index.html
    echo "  ✓ 首页英雄区信任文案已修正"
else
    echo "  ⏭ 首页信任文案已是新版本，跳过"
fi

# ── 4. 修复各页面信任徽章 ──
echo "[4/5] 修复 resume.html / jd_match.html / resume_builder.html 信任徽章..."

# 统一修复所有页面中的 trust-badge 描述
for page in templates/resume.html templates/jd_match.html templates/resume_builder.html; do
    if [ -f "$page" ] && grep -q "分析完成后数据立即销毁" "$page"; then
        sed -i.bak 's|<strong>隐私防火墙</strong>：您的手机号、邮箱等个人信息在发送给 AI 前已自动脱敏，分析完成后数据立即销毁。|<strong>隐私防火墙</strong>：您的手机号、邮箱等个人信息在发送给第三方 AI 模型前已自动脱敏替换。未绑定账号时，分析文本不做持久化存储。详见<a href="/privacy" target="_blank" style="color:#166534;text-decoration:underline">隐私政策</a>。|g' "$page"
        echo "  ✓ $page 信任徽章已修正"
    else
        echo "  ⏭ $page 已是新版本或不存在，跳过"
    fi
done

# 修复 resume_builder.html 的上传区 trust-badge
if [ -f "templates/resume_builder.html" ] && grep -q "文件分析后立即销毁" templates/resume_builder.html; then
    sed -i 's|<strong>隐私防火墙保护</strong>：您的简历仅用于本次 AI 分析，个人联系方式在发送给 AI 前已自动脱敏，文件分析后立即销毁。|<strong>隐私防火墙保护</strong>：上传的 PDF 仅在内存中解析后丢弃，个人联系方式在发送给第三方 AI 模型前已自动脱敏。如您绑定账号，编辑内容将保存到云端。|g' templates/resume_builder.html
    echo "  ✓ resume_builder.html 上传区信任徽章已修正"
fi

# ── 5. 清理 sed 备份文件 ──
echo "[5/5] 清理临时文件..."
find templates/ -name "*.bak" -delete 2>/dev/null || true
echo "  ✓ 完成"

echo ""
echo "══════════════════════════════════════"
echo "  ✅ 信任合规补丁安装完成！"
echo "══════════════════════════════════════"
echo ""
echo "  修复了 6 个矛盾点："
echo ""
echo "  ❌ → ✅ privacy.html"
echo "    旧：「数据不会写入任何数据库」"
echo "    新：如实描述 SQLite 存储（绑定后）+ Gemini API 传输"
echo ""
echo "  ❌ → ✅ index.html 首页"
echo "    旧：「绝不上传云端存储」"
echo "    新：「个人信息 AI 处理前自动脱敏」+ 链接到隐私政策"
echo ""
echo "  ❌ → ✅ privacy.html"
echo "    旧：「不使用第三方追踪 Cookie」"
echo "    新：如实披露 FingerprintJS 及其用途和局限"
echo ""
echo "  ⚠️ → ✅ terms.html"
echo "    新增：第三方 AI 服务披露（Google Gemini）"
echo "    新增：AI 生成内容准确性免责"
echo ""
echo "  ⚠️ → ✅ 各页面 trust-badge"
echo "    旧：「分析完成后数据立即销毁」"
echo "    新：区分已绑定/未绑定行为 + 链接隐私政策"
echo ""
echo "  备份位置: $BACKUP/"
echo "  回滚方法: cp -r $BACKUP/* ."
echo ""
