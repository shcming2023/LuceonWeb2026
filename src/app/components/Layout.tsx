import type { ReactNode } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Settings,
  BookOpen,
  Bell,
  GraduationCap,
  ListTodo,
  ShieldCheck,
  Activity,
} from 'lucide-react';
import { BatchProcessingController } from './BatchUploadModal';
import { DependencyHealthBanner } from './DependencyHealthBanner';

/* ── 侧边栏主导航（PRD v0.4 §10.3） ──────────────────── */
const SIDE_NAV = [
  { name: '任务管理',   href: '/tasks',     icon: ListTodo },
  { name: '成果库',     href: '/library',   icon: GraduationCap },
];

/* ── 侧边栏底部导航 ──────────────────────────────────────────── */
const BOTTOM_NAV = [
  { name: '一致性审计',   href: '/audit',             icon: ShieldCheck },
  { name: '系统健康',     href: '/ops/health',        icon: Activity },
  { name: '系统设置',     href: '/settings',          icon: Settings },
];

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="h-screen flex flex-col bg-[#f6f7fb] overflow-hidden">
      {/* ── 顶部导航栏 ─────────────────────────────────────── */}
      <header className="h-14 bg-white/85 backdrop-blur-xl border-b border-slate-200/80 flex-shrink-0 z-50">
        <div className="h-full px-8 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/tasks" className="flex items-center gap-2">
              <span className="font-extrabold text-xl text-slate-900">
                Edu<span className="text-blue-600">Doc</span>
              </span>
            </Link>
          </div>

          {/* 右侧：操作按钮 + 通知 + 头像 */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/ops/health')}
              className="relative p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors"
              title="查看系统健康"
            >
              <Bell className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/settings')}
              className="relative p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-9 h-9 rounded-full bg-slate-950 ring-4 ring-white flex items-center justify-center text-white text-xs font-bold shadow-sm">
              U
            </div>
          </div>
        </div>
      </header>

      {/* ── 主体区域 ───────────────────────────────────────── */}
      <DependencyHealthBanner />
      <div className="flex flex-1 overflow-hidden">
        {/* 侧边栏 */}
        <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200/80 flex flex-col overflow-hidden">
          {/* 品牌 Logo 区 */}
          <div className="px-5 pt-5 pb-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-950 px-4 py-4 text-white shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center flex-shrink-0">
                  <BookOpen className="w-5 h-5 text-blue-700" />
                </div>
                <div className="leading-tight">
                  <div className="font-extrabold text-sm">EduDoc</div>
                  <div className="font-semibold text-xs text-blue-100">Platform</div>
                </div>
              </div>
              <p className="mt-3 text-[11px] font-medium leading-relaxed text-slate-300">
                教育文档处理平台
              </p>
            </div>
          </div>

          {/* 主导航 */}
          <nav className="flex-1 px-3 py-4 overflow-y-auto">
            <div className="mb-2 px-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase">
                核心工作区
              </span>
            </div>
            {SIDE_NAV.map((item) => {
              const active = isActive(item.href);
              return (
                <button
                  key={item.href}
                  onClick={() => navigate(item.href)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 mb-1 rounded-lg text-sm transition-all duration-200 ${
                    active
                      ? 'bg-blue-50 text-blue-700 font-semibold ring-1 ring-blue-100 shadow-sm'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950 font-medium'
                  }`}
                >
                  <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${active ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                    <item.icon className="w-4 h-4 flex-shrink-0" />
                  </span>
                  <span className="text-sm font-semibold">{item.name}</span>
                </button>
              );
            })}
          </nav>

          {/* 底部导航 */}
          <div className="px-3 py-4 border-t border-slate-100 bg-slate-50/70">
            <div className="mb-2 px-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase">
                管理与治理
              </span>
            </div>
            {BOTTOM_NAV.map((item) => {
              const active = isActive(item.href);
              return (
                <button
                  key={item.href}
                  onClick={() => navigate(item.href)}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 mb-0.5 rounded-md text-xs transition-colors ${
                    active
                      ? 'bg-white text-slate-900 font-semibold shadow-sm ring-1 ring-slate-200'
                      : 'text-slate-500 hover:bg-white/80 hover:text-slate-700 font-medium'
                  }`}
                >
                  <item.icon className={`w-[14px] h-[14px] flex-shrink-0 ${active ? 'text-slate-600' : 'text-slate-400'}`} />
                  <span className="text-xs font-semibold">{item.name}</span>
                </button>
              );
            })}
            <div className="mt-2 px-3 text-[10px] text-slate-300">v0.7.0</div>
          </div>
        </aside>

        {/* 页面内容 */}
        <main className="flex-1 overflow-y-auto">
          {children}
          <BatchProcessingController />
        </main>
      </div>
    </div>
  );
}
