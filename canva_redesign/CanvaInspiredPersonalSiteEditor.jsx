import React from 'react';
import {
  Home,
  LayoutTemplate,
  Image,
  Type,
  CloudUpload,
  Wrench,
  Folder,
  Grid3X3,
  Sparkles,
  Search,
  Mic,
  Eye,
  Share2,
  Plus,
  ChevronDown,
  Monitor,
  PencilLine,
  Crown,
  Wand2,
} from 'lucide-react';
import './canva-editor.css';

const templateCards = [
  { title: 'Landing Hero', tag: '简洁亮色', img: 'linear-gradient(135deg,#dbeafe,#ffffff 60%,#c4b5fd)' },
  { title: 'Portfolio Dark', tag: '高级深色', img: 'linear-gradient(135deg,#0f172a,#111827 60%,#1d4ed8)' },
  { title: 'Creator Intro', tag: '个人展示', img: 'linear-gradient(135deg,#f5d0fe,#ffffff 60%,#fed7aa)' },
  { title: 'Minimal Resume', tag: '作品集', img: 'linear-gradient(135deg,#f8fafc,#ffffff 60%,#e2e8f0)' },
  { title: 'Startup Bio', tag: '科技感', img: 'linear-gradient(135deg,#d1fae5,#ffffff 60%,#bfdbfe)' },
  { title: 'Elegant Cards', tag: '品牌风', img: 'linear-gradient(135deg,#ede9fe,#ffffff 60%,#fbcfe8)' },
];

function LeftRailItem({ icon, label, active = false }) {
  return (
    <button className={`rail-item ${active ? 'active' : ''}`}>
      <span className="rail-icon">{icon}</span>
      <span className="rail-label">{label}</span>
    </button>
  );
}

function TemplateCard({ title, tag, img }) {
  return (
    <div className="template-card">
      <div className="template-thumb" style={{ background: img }}>
        <div className="thumb-chip">{tag}</div>
      </div>
      <div className="template-meta">
        <div className="template-title">{title}</div>
        <button className="ghost-mini">使用</button>
      </div>
    </div>
  );
}

export default function CanvaInspiredPersonalSiteEditor() {
  return (
    <div className="editor-shell">
      <header className="topbar">
        <div className="topbar-left">
          <div className="logo-dot">◉</div>
          <button className="top-link active">文件</button>
          <button className="top-link">调整尺寸</button>
          <button className="top-link">编辑</button>
          <div className="divider" />
          <div className="project-name">个人网站专家 / 未命名设计</div>
        </div>

        <div className="topbar-right">
          <button className="pill premium"><Crown size={15} /> 升级专业版</button>
          <button className="icon-pill"><Eye size={16} /> 预览</button>
          <button className="icon-pill primary"><Share2 size={16} /> 发布网站</button>
        </div>
      </header>

      <div className="workspace">
        <aside className="left-rail">
          <LeftRailItem icon={<Home size={18} />} label="模板" active />
          <LeftRailItem icon={<LayoutTemplate size={18} />} label="素材" />
          <LeftRailItem icon={<Type size={18} />} label="文字" />
          <LeftRailItem icon={<Image size={18} />} label="品牌" />
          <LeftRailItem icon={<CloudUpload size={18} />} label="上传" />
          <LeftRailItem icon={<Wrench size={18} />} label="工具" />
          <LeftRailItem icon={<Folder size={18} />} label="项目" />
          <LeftRailItem icon={<Grid3X3 size={18} />} label="应用" />
          <LeftRailItem icon={<Sparkles size={18} />} label="AI 生图" />
        </aside>

        <section className="side-panel">
          <div className="prompt-box">
            <div className="prompt-title">描述你的理想网站</div>
            <textarea
              className="prompt-input"
              defaultValue={'帮我生成一个极简、专业、带作品展示和个人介绍的个人网站，风格参考 Canva 的编辑器布局。'}
            />
            <div className="prompt-actions">
              <button className="circle-btn"><Image size={16} /></button>
              <button className="circle-btn"><Mic size={16} /></button>
            </div>
          </div>

          <button className="generate-btn"><Wand2 size={16} /> 生成设计</button>

          <div className="template-grid">
            {templateCards.map((card) => (
              <TemplateCard key={card.title} {...card} />
            ))}
          </div>
        </section>

        <main className="stage-area">
          <div className="stage-toolbar">
            <div className="stage-search">
              <Search size={16} />
              <input placeholder="搜索页面、模块或模板…" />
            </div>
            <div className="stage-toolbar-right">
              <button className="ghost-btn">刷新画布</button>
              <button className="primary-btn">一键生成网站方案</button>
            </div>
          </div>

          <div className="canvas-wrap">
            <div className="page-canvas">
              <div className="hero-block">
                <div className="hero-badge">PERSONAL SITE</div>
                <h1>把你的个人网站，做得像个真正的设计工具。</h1>
                <p>
                  这里不是黑乎乎一整块预览区，而是有明确层级、模块、缩放、页面管理和模板入口的编辑工作台。
                </p>
                <div className="hero-actions">
                  <button className="primary-btn">开始编辑</button>
                  <button className="ghost-btn">查看模板</button>
                </div>
              </div>

              <div className="content-grid">
                <div className="info-card tall">
                  <div className="card-kicker">关于我</div>
                  <div className="card-title">极简但不空，专业但不死板</div>
                  <div className="card-text">
                    你的旧版问题不是“功能少”，而是视觉节奏不对：左边太空、右边太闷、中心没有真正的页面感。
                  </div>
                </div>

                <div className="info-card">
                  <div className="card-kicker">项目展示</div>
                  <div className="card-title">案例一 / 品牌官网</div>
                  <div className="mini-line" />
                  <div className="mini-line short" />
                </div>

                <div className="info-card">
                  <div className="card-kicker">服务内容</div>
                  <div className="card-title">设计系统 / 个人品牌 / 作品集</div>
                  <div className="chip-row">
                    <span>UI</span>
                    <span>Brand</span>
                    <span>Web</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bottom-bar">
            <button className="page-thumb active">1</button>
            <button className="square-btn"><Plus size={18} /></button>
            <button className="square-btn"><ChevronDown size={18} /></button>
            <div className="zoom-box">
              <div className="zoom-line" />
              <span>92%</span>
            </div>
            <div className="page-meta"><Monitor size={16} /> 页面 1/1</div>
            <button className="ghost-btn icon-only"><PencilLine size={16} /></button>
          </div>
        </main>
      </div>
    </div>
  );
}
