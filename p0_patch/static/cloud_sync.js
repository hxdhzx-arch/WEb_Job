/* ══════════════════════════════════════
   cloud_sync.js — 云端简历同步 + 多简历管理
   
   依赖: credits.js (PowerSystem), script.js (resumeData, TC, ...)
   在 resume_builder.html 中 script.js 之后加载
   ══════════════════════════════════════ */
var CloudSync = (function () {
  var _uid = "";
  var _bound = false;
  var _currentResumeId = null;  // 当前编辑的云端简历 ID
  var _saving = false;
  var _lastSaveHash = "";       // 防止重复保存相同内容
  var _syncIndicator = null;

  // ── 初始化 ──
  function init(uid, bound) {
    _uid = uid;
    _bound = bound;

    // 创建同步状态指示器
    _createSyncIndicator();

    // 如果未绑定，显示"已有账号？登录恢复"入口
    if (!bound) {
      _showLoginHint();
    }

    // 尝试从 URL 参数恢复 resume_id
    var params = new URLSearchParams(window.location.search);
    var rid = params.get("resume_id");
    if (rid) _currentResumeId = parseInt(rid);

    // 如果已绑定，拉取简历列表并显示新建按钮
    if (bound) {
      _loadResumeList();
      var nb = document.getElementById("cloud-new-btn");
      if (nb) nb.style.display = "";
    }

    _updateSyncStatus();
  }

  // ── 绑定成功后触发 ──
  function onBound(uid) {
    _uid = uid;
    _bound = true;
    _updateSyncStatus();
    // 立即保存当前编辑内容到云端
    saveToCloud(true);
    _loadResumeList();
    // 显示新建按钮
    var nb = document.getElementById("cloud-new-btn");
    if (nb) nb.style.display = "";
    // 移除登录提示
    var hint = document.getElementById("cloud-login-hint");
    if (hint) hint.style.display = "none";
  }

  // ── 自动保存 (由 script.js 的 liveRender 调用) ──
  var _autoSaveTimer = null;
  function scheduleAutoSave() {
    if (!_bound) return;
    if (_autoSaveTimer) clearTimeout(_autoSaveTimer);
    _autoSaveTimer = setTimeout(function () {
      saveToCloud(false);
    }, 3000);  // 编辑后 3 秒自动保存
  }

  // ── 保存到云端 ──
  async function saveToCloud(isManual) {
    if (!_bound || !_uid || _saving) return;
    if (typeof resumeData === "undefined" || typeof TC === "undefined") return;

    // 检查内容是否变化
    var hash = JSON.stringify(resumeData) + JSON.stringify(TC);
    if (hash === _lastSaveHash && !isManual) return;

    _saving = true;
    _setSyncStatus("saving");

    try {
      var title = _generateTitle();
      var resp = await fetch("/api/resumes/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: _uid,
          resume_id: _currentResumeId,
          title: title,
          resume_data: resumeData,
          template_config: TC,
          is_default: true
        })
      });
      var d = await resp.json();
      if (d.error) {
        if (d.need_bind) {
          _setSyncStatus("local");
          return;
        }
        console.error("Cloud save error:", d.error);
        _setSyncStatus("error");
        return;
      }
      _currentResumeId = d.resume_id;
      _lastSaveHash = hash;
      _setSyncStatus("saved");

      // 更新简历列表
      _loadResumeList();
    } catch (e) {
      console.error("Cloud save failed:", e);
      _setSyncStatus("error");
    } finally {
      _saving = false;
    }
  }

  // ── 从云端加载简历 ──
  async function loadFromCloud(resumeId) {
    if (!_uid) return;
    try {
      var resp = await fetch(
        "/api/resumes/load?user_id=" + encodeURIComponent(_uid) +
        "&resume_id=" + resumeId
      );
      var d = await resp.json();
      if (d.error) {
        alert("加载失败: " + d.error);
        return;
      }
      applyResume(d);
    } catch (e) {
      alert("加载失败，请重试");
    }
  }

  // ── 应用简历数据到编辑器 ──
  function applyResume(data) {
    if (!data) return;

    if (data.resume_data) {
      // 全局变量来自 script.js
      if (typeof resumeData !== "undefined") {
        Object.assign(resumeData, data.resume_data);
      }
    }
    if (data.template_config) {
      if (typeof TC !== "undefined") {
        Object.assign(TC, data.template_config);
      }
    }
    if (data.id) {
      _currentResumeId = data.id;
    }

    // 刷新编辑器 UI（这些函数定义在 script.js 中）
    if (typeof syncFormFromState === "function") syncFormFromState();
    if (typeof syncControlsFromTC === "function") syncControlsFromTC();
    if (typeof renderWorkExperience === "function") renderWorkExperience();
    if (typeof renderEducation === "function") renderEducation();
    if (typeof buildTplGrid === "function") buildTplGrid();
    if (typeof renderPreview === "function") renderPreview();
    if (typeof saveToLocal === "function") saveToLocal();

    _lastSaveHash = JSON.stringify(data.resume_data || {}) + JSON.stringify(data.template_config || {});
    _setSyncStatus("saved");

    if (typeof PowerSystem !== "undefined") {
      PowerSystem.toast("☁️ 简历已从云端恢复");
    }
  }

  // ── 新建简历 ──
  async function createNew() {
    if (!_bound) {
      if (typeof PowerSystem !== "undefined") PowerSystem.showBind("绑定账号后可创建多份简历");
      return;
    }
    _currentResumeId = null;
    _lastSaveHash = "";
    // 重置到空白状态（script.js 的 resetAll 太激进，我们只清数据不 reload）
    if (typeof resumeData !== "undefined") {
      resumeData.basic = { name: "", age: "", phone: "", email: "", city: "", years: "", photo: "" };
      resumeData.intent = { job: "", salary: "" };
      resumeData.education = [{ school: "", major: "", degree: "", time: "" }];
      resumeData.work = [{ company: "", title: "", time: "", duties: [""] }];
      resumeData.skills = "";
      resumeData.intro = "";
      resumeData.certs = "";
    }
    if (typeof syncFormFromState === "function") syncFormFromState();
    if (typeof renderWorkExperience === "function") renderWorkExperience();
    if (typeof renderEducation === "function") renderEducation();
    if (typeof renderPreview === "function") renderPreview();
    _setSyncStatus("local");
  }

  // ── 删除简历 ──
  async function deleteResume(resumeId) {
    if (!confirm("确定删除这份简历？此操作不可恢复。")) return;
    try {
      var resp = await fetch("/api/resumes/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: _uid, resume_id: resumeId })
      });
      var d = await resp.json();
      if (d.error) { alert(d.error); return; }
      if (_currentResumeId === resumeId) {
        _currentResumeId = null;
        _lastSaveHash = "";
      }
      _loadResumeList();
      if (typeof PowerSystem !== "undefined") PowerSystem.toast("已删除");
    } catch (e) {
      alert("删除失败");
    }
  }

  // ── 加载简历列表 ──
  async function _loadResumeList() {
    if (!_bound || !_uid) return;
    var container = document.getElementById("cloud-resume-list");
    if (!container) return;

    try {
      var resp = await fetch("/api/resumes/list?user_id=" + encodeURIComponent(_uid));
      var d = await resp.json();
      if (d.error) return;

      var resumes = d.resumes || [];
      container.innerHTML = "";

      if (resumes.length === 0) {
        container.innerHTML = '<div class="crl-empty">暂无云端简历，编辑后自动保存</div>';
        container.style.display = "block";
        return;
      }

      for (var i = 0; i < resumes.length; i++) {
        var r = resumes[i];
        var isCurrent = _currentResumeId === r.id;
        var date = new Date(r.updated_at * 1000);
        var dateStr = (date.getMonth() + 1) + "/" + date.getDate() + " " +
                      date.getHours() + ":" + ("0" + date.getMinutes()).slice(-2);

        var div = document.createElement("div");
        div.className = "crl-item" + (isCurrent ? " active" : "");
        div.innerHTML =
          '<div class="crl-info" onclick="CloudSync.loadFromCloud(' + r.id + ')">' +
            '<span class="crl-title">' + _escHtml(r.title) +
              (r.is_default ? ' <span class="crl-default">默认</span>' : '') +
            '</span>' +
            '<span class="crl-meta">' + _escHtml(r.preview_name || "未填写") + ' · ' + dateStr + '</span>' +
          '</div>' +
          '<button class="crl-del" onclick="CloudSync.deleteResume(' + r.id + ')" title="删除">×</button>';
        container.appendChild(div);
      }
      container.style.display = "block";
    } catch (e) {
      console.error("Load resume list failed:", e);
    }
  }

  // ── 同步状态指示器 ──
  function _createSyncIndicator() {
    var toolbar = document.getElementById("quick-bar");
    if (!toolbar) return;

    var indicator = document.createElement("div");
    indicator.id = "cloud-sync-indicator";
    indicator.className = "toolbar-group";
    indicator.style.cssText = "font-size:11px;font-weight:600;gap:3px";
    indicator.innerHTML = '<span id="sync-icon">💾</span><span id="sync-text">仅本地</span>';
    toolbar.appendChild(indicator);
    _syncIndicator = indicator;
  }

  function _setSyncStatus(status) {
    var icon = document.getElementById("sync-icon");
    var text = document.getElementById("sync-text");
    if (!icon || !text) return;
    var map = {
      "saving": { icon: "⏳", text: "保存中...", color: "#F59E0B" },
      "saved":  { icon: "☁️", text: "已同步",   color: "#10B981" },
      "local":  { icon: "💾", text: "仅本地",   color: "#6B7280" },
      "error":  { icon: "⚠️", text: "同步失败", color: "#EF4444" }
    };
    var s = map[status] || map["local"];
    icon.textContent = s.icon;
    text.textContent = s.text;
    text.style.color = s.color;
  }

  function _updateSyncStatus() {
    _setSyncStatus(_bound ? "saved" : "local");
  }

  // ── 显示"已有账号？登录恢复" ──
  function _showLoginHint() {
    var toolbar = document.getElementById("quick-bar");
    if (!toolbar) return;
    // 检查是否已有（防止重复创建）
    if (document.getElementById("cloud-login-hint")) return;

    var hint = document.createElement("div");
    hint.id = "cloud-login-hint";
    hint.className = "toolbar-group";
    hint.innerHTML = '<button class="toolbar-btn" onclick="PowerSystem.showLogin()" style="color:#7C3AED;border-color:rgba(124,58,237,.25)">🔑 已有账号？恢复简历</button>';
    toolbar.appendChild(hint);
  }

  // ── 自动生成简历标题 ──
  function _generateTitle() {
    if (typeof resumeData === "undefined") return "未命名简历";
    var parts = [];
    if (resumeData.basic && resumeData.basic.name) parts.push(resumeData.basic.name);
    if (resumeData.intent && resumeData.intent.job) parts.push(resumeData.intent.job);
    if (parts.length > 0) return parts.join(" - ");
    return "未命名简历";
  }

  function _escHtml(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  return {
    init: init,
    onBound: onBound,
    scheduleAutoSave: scheduleAutoSave,
    saveToCloud: saveToCloud,
    loadFromCloud: loadFromCloud,
    applyResume: applyResume,
    createNew: createNew,
    deleteResume: deleteResume,
    getCurrentResumeId: function () { return _currentResumeId; }
  };
})();
