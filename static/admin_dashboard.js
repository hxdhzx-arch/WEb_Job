/**
 * admin_dashboard.js — 管理后台交互逻辑
 */

const API = '/api/v1';
let TOKEN = localStorage.getItem('admin_token') || '';
let CHARTS = {};

// ══════════════════════════════════════
//  工具函数
// ══════════════════════════════════════

async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (TOKEN) headers['Authorization'] = 'Bearer ' + TOKEN;
  const res = await fetch(API + path, { headers, ...opts });
  const data = await res.json();
  if (!res.ok && res.status === 401) {
    logout();
    throw new Error('Token 过期');
  }
  return data;
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function shortDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

function statusBadge(status) {
  const labels = {
    active: '活跃', paid: '已支付', pending: '待支付', expired: '已过期',
    cancelled: '已取消', failed: '失败', refunded: '已退款', past_due: '逾期',
    new: '新', contacted: '已联系', converted: '已转化', archived: '已归档',
    error: '错误', warning: '警告', info: '信息', trial: '试用',
  };
  return `<span class="status-badge status-${status}">${labels[status] || status}</span>`;
}

function roleBadge(role) {
  return `<span class="status-badge role-${role}">${role === 'admin' ? '管理员' : '用户'}</span>`;
}

function animateValue(el, end, prefix = '', suffix = '') {
  const duration = 800;
  const start = 0;
  const startTime = performance.now();
  function update(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const val = Math.round(start + (end - start) * ease);
    el.textContent = prefix + val.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ══════════════════════════════════════
//  登录 / 登出
// ══════════════════════════════════════

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('login-btn');
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';
  btn.classList.add('loading');
  btn.querySelector('span').textContent = '登录中...';

  try {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    const res = await fetch(API + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (!data.success) {
      errEl.textContent = data.message || '登录失败';
      errEl.style.display = 'block';
      return;
    }

    if (data.data.user.role !== 'admin') {
      errEl.textContent = '该账号没有管理员权限';
      errEl.style.display = 'block';
      return;
    }

    TOKEN = data.data.access_token;
    localStorage.setItem('admin_token', TOKEN);

    const user = data.data.user;
    document.getElementById('admin-name').textContent = user.nickname;
    document.getElementById('admin-email').textContent = user.email;
    document.getElementById('admin-avatar').textContent = (user.nickname || 'A')[0].toUpperCase();

    document.getElementById('login-overlay').style.display = 'none';
    document.getElementById('app').style.display = 'flex';

    loadOverview();
  } catch (err) {
    errEl.textContent = '网络错误，请重试';
    errEl.style.display = 'block';
  } finally {
    btn.classList.remove('loading');
    btn.querySelector('span').textContent = '登 录';
  }
});

function logout() {
  TOKEN = '';
  localStorage.removeItem('admin_token');
  document.getElementById('login-overlay').style.display = 'flex';
  document.getElementById('app').style.display = 'none';
}

document.getElementById('logout-btn').addEventListener('click', logout);

// 自动登录检测
(async function autoLogin() {
  if (!TOKEN) return;
  try {
    const data = await api('/auth/me');
    if (data.success && data.data.user.role === 'admin') {
      const user = data.data.user;
      document.getElementById('admin-name').textContent = user.nickname;
      document.getElementById('admin-email').textContent = user.email;
      document.getElementById('admin-avatar').textContent = (user.nickname || 'A')[0].toUpperCase();
      document.getElementById('login-overlay').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      loadOverview();
    } else {
      logout();
    }
  } catch (e) {
    logout();
  }
})();

// ══════════════════════════════════════
//  导航切换
// ══════════════════════════════════════

const pageTitles = {
  overview: '数据总览', users: '用户管理', orders: '订单流水',
  subscriptions: '订阅管理', analytics: '转化分析', usage: '用量统计',
  leads: '销售线索', errors: '错误日志',
};

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    const page = item.dataset.page;
    switchPage(page);
    // 关闭移动端侧边栏
    document.getElementById('sidebar').classList.remove('open');
  });
});

function switchPage(page) {
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  if (el) el.classList.add('active');

  document.getElementById('page-title').textContent = pageTitles[page] || page;

  // 按需加载数据
  const loaders = {
    overview: loadOverview,
    users: () => loadUsers(1),
    orders: () => loadOrders(1),
    subscriptions: () => loadSubscriptions(1),
    analytics: loadAnalytics,
    usage: loadUsage,
    leads: () => loadLeads(1),
    errors: () => loadErrors(1),
  };
  if (loaders[page]) loaders[page]();
}

// 移动端菜单
document.getElementById('menu-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

// 时间
function updateTime() {
  const now = new Date();
  document.getElementById('topbar-time').textContent = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
setInterval(updateTime, 1000);
updateTime();

// ══════════════════════════════════════
//  数据总览
// ══════════════════════════════════════

async function loadOverview() {
  try {
    const [overview, conversion, usageStats] = await Promise.all([
      api('/admin/analytics/overview'),
      api('/admin/analytics/conversion?days=30'),
      api('/admin/usage/stats?days=30'),
    ]);

    if (overview.success) {
      const d = overview.data;
      animateValue(document.getElementById('m-total-users'), d.total_users);
      animateValue(document.getElementById('m-revenue'), d.total_revenue, '¥ ');
      animateValue(document.getElementById('m-conversion'), d.conversion_rate, '', '%');
      document.getElementById('m-new-7d').textContent = `近7天 +${d.new_users_7d}`;
      document.getElementById('m-paid-users').textContent = `${d.paid_users} 位付费用户`;
      document.getElementById('m-active-subs').textContent = `${d.active_subscriptions} 个活跃订阅`;
    }

    if (usageStats.success) {
      const d = usageStats.data;
      animateValue(document.getElementById('m-api-calls'), d.total_calls);
      const topFeature = Object.entries(d.by_feature || {}).sort((a, b) => b[1] - a[1])[0];
      document.getElementById('m-features').textContent = topFeature ? `热门: ${topFeature[0]}` : '暂无数据';

      // 每日用量图
      renderLineChart('chart-users',
        (conversion.data?.daily_registrations || []).map(i => i.date),
        (conversion.data?.daily_registrations || []).map(i => i.count),
        '新注册', '#8B5CF6'
      );

      // 收入图
      renderBarChart('chart-revenue',
        (conversion.data?.daily_payments || []).map(i => i.date),
        (conversion.data?.daily_payments || []).map(i => i.revenue),
        '收入 (¥)', '#3B82F6'
      );

      // 功能分布图
      renderFeatureChart('chart-features', d.by_feature || {});
    }
  } catch (err) {
    console.error('加载总览失败:', err);
  }
}

// ══════════════════════════════════════
//  用户管理
// ══════════════════════════════════════

let userSearchTimer;
document.getElementById('user-search').addEventListener('input', (e) => {
  clearTimeout(userSearchTimer);
  userSearchTimer = setTimeout(() => loadUsers(1), 400);
});
document.getElementById('user-role-filter').addEventListener('change', () => loadUsers(1));

async function loadUsers(page) {
  const search = document.getElementById('user-search').value.trim();
  const role = document.getElementById('user-role-filter').value;
  let url = `/admin/users?page=${page}&per_page=15`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (role) url += `&role=${role}`;

  try {
    const data = await api(url);
    if (!data.success) return;
    const { items, total, pages } = data.data;
    const tbody = document.getElementById('users-tbody');

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><p>暂无用户数据</p></td></tr>';
      document.getElementById('users-pagination').innerHTML = '';
      return;
    }

    tbody.innerHTML = items.map(u => `
      <tr>
        <td>${u.id}</td>
        <td>${u.email || u.phone || '—'}</td>
        <td>${u.nickname || '—'}</td>
        <td>${roleBadge(u.role)}</td>
        <td><strong>${u.credits_left}</strong></td>
        <td>—</td>
        <td>${shortDate(u.created_at)}</td>
        <td><button class="action-btn" onclick="showUserDetail(${u.id})">详情</button></td>
      </tr>
    `).join('');

    renderPagination('users-pagination', page, pages, total, loadUsers);
  } catch (err) {
    console.error('加载用户失败:', err);
  }
}

async function showUserDetail(userId) {
  try {
    const data = await api(`/admin/users/${userId}`);
    if (!data.success) return;
    const { user: u, subscription: sub, plan } = data.data;

    document.getElementById('user-modal-body').innerHTML = `
      <div class="info-row"><span class="info-label">ID</span><span class="info-value">${u.id}</span></div>
      <div class="info-row"><span class="info-label">UUID</span><span class="info-value">${u.uuid}</span></div>
      <div class="info-row"><span class="info-label">邮箱</span><span class="info-value">${u.email || '未绑定'}</span></div>
      <div class="info-row"><span class="info-label">手机</span><span class="info-value">${u.phone || '未绑定'}</span></div>
      <div class="info-row"><span class="info-label">昵称</span><span class="info-value">${u.nickname}</span></div>
      <div class="info-row"><span class="info-label">角色</span><span class="info-value">${roleBadge(u.role)}</span></div>
      <div class="info-row"><span class="info-label">算力余额</span><span class="info-value"><strong>${u.credits_left}</strong></span></div>
      <div class="info-row"><span class="info-label">已使用</span><span class="info-value">${u.total_used || 0}</span></div>
      <div class="info-row"><span class="info-label">邮箱验证</span><span class="info-value">${u.email_verified ? '✅ 已验证' : '❌ 未验证'}</span></div>
      <div class="info-row"><span class="info-label">试用到期</span><span class="info-value">${u.trial_ends_at ? formatDate(u.trial_ends_at) : '—'}</span></div>
      <div class="info-row"><span class="info-label">当前套餐</span><span class="info-value">${plan ? plan.display_name : '免费版'}</span></div>
      <div class="info-row"><span class="info-label">订阅状态</span><span class="info-value">${sub ? statusBadge(sub.status) + ' (剩余' + sub.days_until_expiry + '天)' : '无订阅'}</span></div>
      <div class="info-row"><span class="info-label">登录次数</span><span class="info-value">${u.login_count}</span></div>
      <div class="info-row"><span class="info-label">最后登录</span><span class="info-value">${formatDate(u.last_login_at)}</span></div>
      <div class="info-row"><span class="info-label">注册时间</span><span class="info-value">${formatDate(u.created_at)}</span></div>
      <div class="info-row"><span class="info-label">IP</span><span class="info-value">${u.ip_address || '—'}</span></div>
      <div class="info-row"><span class="info-label">设备</span><span class="info-value">${u.device_hash || '—'}</span></div>
    `;

    document.getElementById('user-modal-actions').innerHTML = `
      <button class="btn-outline" onclick="adjustCredits(${u.id}, 100)">+100 算力</button>
      <button class="btn-outline" onclick="adjustCredits(${u.id}, 500)">+500 算力</button>
      <button class="btn-primary" onclick="document.getElementById('user-modal').style.display='none'">关闭</button>
    `;

    document.getElementById('user-modal').style.display = 'flex';
  } catch (err) {
    console.error('加载用户详情失败:', err);
  }
}

async function adjustCredits(userId, amount) {
  try {
    await api(`/admin/users/${userId}/credits`, {
      method: 'PUT',
      body: JSON.stringify({ action: 'add', amount }),
    });
    showUserDetail(userId); // 刷新
    loadUsers(1);
  } catch (err) { console.error(err); }
}

// ══════════════════════════════════════
//  订单流水
// ══════════════════════════════════════

document.getElementById('order-status-filter').addEventListener('change', () => loadOrders(1));

async function loadOrders(page) {
  const status = document.getElementById('order-status-filter').value;
  let url = `/admin/orders?page=${page}&per_page=15`;
  if (status) url += `&status=${status}`;

  try {
    const data = await api(url);
    if (!data.success) return;
    const { items, total, pages } = data.data;
    const tbody = document.getElementById('orders-tbody');

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><p>暂无订单</p></td></tr>';
      document.getElementById('orders-pagination').innerHTML = '';
      return;
    }

    tbody.innerHTML = items.map(o => `
      <tr>
        <td style="font-family:monospace;font-size:.78rem">${o.order_no}</td>
        <td>${o.user_id}</td>
        <td>${o.plan_name || '—'}</td>
        <td><strong>¥${o.amount.toFixed(2)}</strong></td>
        <td>${o.discount_amount > 0 ? '<span style="color:#34D399">-¥' + o.discount_amount.toFixed(2) + '</span>' : '—'}</td>
        <td>${statusBadge(o.status)}</td>
        <td>${o.paid_at ? formatDate(o.paid_at) : '—'}</td>
        <td>${shortDate(o.created_at)}</td>
      </tr>
    `).join('');

    renderPagination('orders-pagination', page, pages, total, loadOrders);
  } catch (err) {
    console.error('加载订单失败:', err);
  }
}

// ══════════════════════════════════════
//  订阅管理
// ══════════════════════════════════════

document.getElementById('sub-status-filter').addEventListener('change', () => loadSubscriptions(1));

async function loadSubscriptions(page) {
  const status = document.getElementById('sub-status-filter').value;
  let url = `/admin/subscriptions?page=${page}&per_page=15`;
  if (status) url += `&status=${status}`;

  try {
    const data = await api(url);
    if (!data.success) return;
    const { items, total, pages } = data.data;
    const tbody = document.getElementById('subs-tbody');

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><p>暂无订阅</p></td></tr>';
      document.getElementById('subs-pagination').innerHTML = '';
      return;
    }

    tbody.innerHTML = items.map(s => `
      <tr>
        <td>${s.id}</td>
        <td>${s.user_id}</td>
        <td>${s.plan_name || '—'}</td>
        <td>${s.billing_cycle === 'yearly' ? '年付' : '月付'}</td>
        <td>${statusBadge(s.status)}</td>
        <td><strong>${s.days_until_expiry}</strong> 天</td>
        <td>${s.auto_renew ? '✅' : '❌'}</td>
        <td>${shortDate(s.current_period_start)}</td>
      </tr>
    `).join('');

    renderPagination('subs-pagination', page, pages, total, loadSubscriptions);
  } catch (err) {
    console.error('加载订阅失败:', err);
  }
}

// ══════════════════════════════════════
//  转化分析
// ══════════════════════════════════════

async function loadAnalytics() {
  try {
    const [churn, conversion] = await Promise.all([
      api('/admin/analytics/churn?days=30'),
      api('/admin/analytics/conversion?days=30'),
    ]);

    if (churn.success) {
      const c = churn.data;
      animateValue(document.getElementById('m-churned'), c.churned_subscriptions);
      animateValue(document.getElementById('m-cancelled'), c.cancelled_subscriptions);
      animateValue(document.getElementById('m-inactive'), c.inactive_users);
    }

    if (conversion.success) {
      const d = conversion.data;
      renderLineChart('chart-registrations',
        (d.daily_registrations || []).map(i => i.date),
        (d.daily_registrations || []).map(i => i.count),
        '注册数', '#8B5CF6'
      );
      renderBarChart('chart-payments',
        (d.daily_payments || []).map(i => i.date),
        (d.daily_payments || []).map(i => i.revenue),
        '收入 (¥)', '#10B981'
      );
    }
  } catch (err) {
    console.error('加载分析失败:', err);
  }
}

// ══════════════════════════════════════
//  用量统计
// ══════════════════════════════════════

async function loadUsage() {
  try {
    const data = await api('/admin/usage/stats?days=30');
    if (!data.success) return;
    const d = data.data;

    renderLineChart('chart-daily-usage',
      (d.daily || []).map(i => i.date),
      (d.daily || []).map(i => i.count),
      'API 调用', '#F59E0B'
    );

    renderDoughnutChart('chart-feature-pie', d.by_feature || {});
  } catch (err) {
    console.error('加载用量失败:', err);
  }
}

// ══════════════════════════════════════
//  线索
// ══════════════════════════════════════

document.getElementById('lead-status-filter').addEventListener('change', () => loadLeads(1));

// 给导出按钮加上 token
document.getElementById('export-leads-btn').addEventListener('click', (e) => {
  e.preventDefault();
  window.open(API + '/admin/leads/export?token=' + TOKEN);
});

async function loadLeads(page) {
  const status = document.getElementById('lead-status-filter').value;
  let url = `/admin/leads?page=${page}&per_page=15`;
  if (status) url += `&status=${status}`;

  try {
    const data = await api(url);
    if (!data.success) return;
    const { items, total, pages } = data.data;
    const tbody = document.getElementById('leads-tbody');

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><p>暂无线索</p></td></tr>';
      document.getElementById('leads-pagination').innerHTML = '';
      return;
    }

    tbody.innerHTML = items.map(l => `
      <tr>
        <td>${l.id}</td>
        <td>${l.name || '—'}</td>
        <td>${l.email || '—'}</td>
        <td>${l.phone || '—'}</td>
        <td>${l.company || '—'}</td>
        <td>${l.source}</td>
        <td>${statusBadge(l.status)}</td>
        <td>${shortDate(l.created_at)}</td>
      </tr>
    `).join('');

    renderPagination('leads-pagination', page, pages, total, loadLeads);
  } catch (err) {
    console.error('加载线索失败:', err);
  }
}

// ══════════════════════════════════════
//  错误日志
// ══════════════════════════════════════

document.getElementById('error-level-filter').addEventListener('change', () => loadErrors(1));

async function loadErrors(page) {
  const level = document.getElementById('error-level-filter').value;
  let url = `/admin/errors?page=${page}&per_page=15`;
  if (level) url += `&level=${level}`;

  try {
    const data = await api(url);
    if (!data.success) return;
    const { items, total, pages } = data.data;
    const tbody = document.getElementById('errors-tbody');

    if (!items.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>🎉 暂无错误日志</p></td></tr>';
      document.getElementById('errors-pagination').innerHTML = '';
      return;
    }

    tbody.innerHTML = items.map(e => `
      <tr>
        <td>${e.id}</td>
        <td>${statusBadge(e.level)}</td>
        <td>${e.module || '—'}</td>
        <td style="font-family:monospace;font-size:.78rem">${e.endpoint || '—'}</td>
        <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis" title="${(e.message||'').replace(/"/g,'&quot;')}">${e.message || '—'}</td>
        <td>${e.user_id || '—'}</td>
        <td>${shortDate(e.created_at)}</td>
      </tr>
    `).join('');

    renderPagination('errors-pagination', page, pages, total, loadErrors);
  } catch (err) {
    console.error('加载错误日志失败:', err);
  }
}

// ══════════════════════════════════════
//  分页组件
// ══════════════════════════════════════

function renderPagination(containerId, currentPage, totalPages, total, loadFn) {
  const el = document.getElementById(containerId);
  if (totalPages <= 1) { el.innerHTML = `<span class="page-info">共 ${total} 条</span>`; return; }

  let html = `<button ${currentPage <= 1 ? 'disabled' : ''} onclick="void(0)" data-p="${currentPage - 1}">上一页</button>`;
  html += `<span class="page-info">${currentPage} / ${totalPages} (共${total}条)</span>`;
  html += `<button ${currentPage >= totalPages ? 'disabled' : ''} onclick="void(0)" data-p="${currentPage + 1}">下一页</button>`;

  el.innerHTML = html;
  el.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = parseInt(btn.dataset.p);
      if (p >= 1 && p <= totalPages) loadFn(p);
    });
  });
}

// ══════════════════════════════════════
//  Chart.js 图表
// ══════════════════════════════════════

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1E293B',
      titleColor: '#F1F5F9',
      bodyColor: '#94A3B8',
      borderColor: '#334155',
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8,
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(148,163,184,.08)', drawBorder: false },
      ticks: { color: '#64748B', font: { size: 11 }, maxTicksLimit: 10 },
    },
    y: {
      grid: { color: 'rgba(148,163,184,.08)', drawBorder: false },
      ticks: { color: '#64748B', font: { size: 11 } },
      beginAtZero: true,
    },
  },
};

function destroyChart(id) {
  if (CHARTS[id]) { CHARTS[id].destroy(); delete CHARTS[id]; }
}

function renderLineChart(canvasId, labels, data, label, color) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  CHARTS[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.map(shortDate),
      datasets: [{
        label,
        data,
        borderColor: color,
        backgroundColor: color + '18',
        fill: true,
        tension: .4,
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
      }],
    },
    options: { ...CHART_DEFAULTS },
  });
}

function renderBarChart(canvasId, labels, data, label, color) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  CHARTS[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.map(shortDate),
      datasets: [{
        label,
        data,
        backgroundColor: color + '88',
        hoverBackgroundColor: color,
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: { ...CHART_DEFAULTS },
  });
}

function renderFeatureChart(canvasId, byFeature) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const entries = Object.entries(byFeature).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return;

  const colors = ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#F43F5E', '#F97316', '#06B6D4', '#84CC16'];
  const featureNames = {
    resume_analyze: '简历诊断', jd_match: 'JD匹配', auto_fill: '智能扩写',
    polish: '简历润色', career_advisor: '职业顾问', keyword_inject: '关键词融合',
    export_word: 'Word导出',
  };

  CHARTS[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: entries.map(([k]) => featureNames[k] || k),
      datasets: [{
        data: entries.map(([, v]) => v),
        backgroundColor: entries.map((_, i) => colors[i % colors.length] + '88'),
        hoverBackgroundColor: entries.map((_, i) => colors[i % colors.length]),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y',
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, grid: { display: false } },
      },
    },
  });
}

function renderDoughnutChart(canvasId, byFeature) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const entries = Object.entries(byFeature).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return;

  const colors = ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#F43F5E', '#F97316', '#06B6D4', '#84CC16'];
  const featureNames = {
    resume_analyze: '简历诊断', jd_match: 'JD匹配', auto_fill: '智能扩写',
    polish: '简历润色', career_advisor: '职业顾问', keyword_inject: '关键词融合',
    export_word: 'Word导出',
  };

  CHARTS[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: entries.map(([k]) => featureNames[k] || k),
      datasets: [{
        data: entries.map(([, v]) => v),
        backgroundColor: entries.map((_, i) => colors[i % colors.length]),
        borderWidth: 0,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94A3B8', font: { size: 12 }, padding: 12 },
        },
        tooltip: CHART_DEFAULTS.plugins.tooltip,
      },
    },
  });
}
