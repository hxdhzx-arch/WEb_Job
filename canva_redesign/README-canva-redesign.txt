这个文件包包含两个文件：

1. CanvaInspiredPersonalSiteEditor.jsx
2. canva-editor.css

使用方式：
- 把 JSX 文件作为你的页面组件替换当前 personal-site 编辑页
- 把 CSS 文件放到全局样式或当前组件样式中引入
- 项目需要安装 lucide-react: npm i lucide-react

如果你用的是 Ant Design：
- 外层布局可以直接塞进 Layout / Sider / Content
- 按钮、输入框、卡片都可以逐步替换为 antd 组件，但建议先把视觉骨架跑起来，再做组件化

核心改动目标：
- 用浅灰工作区 + 白色画布，替换现在的大块深色预览
- 把左侧 AI 面板做成更像 Canva 的“高密度模板+输入”结构
- 增加顶部渐变工具栏、底部页面缩放栏、模板卡片网格
- 让中间真正像一个“可编辑页面”而不是单纯预览框
