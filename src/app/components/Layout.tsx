import type { ReactNode } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Settings,
  FileText,
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
    <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">
      {/* ── 顶部导航栏 ─────────────────────────────────────── */}
      <header className="h-14 bg-white/60 backdrop-blur-md border-b border-slate-200 flex-shrink-0 z-50">
        <div className="h-full px-8 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/tasks" className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight text-slate-800">
                Edu<span className="text-blue-600">Doc</span>
              </span>
            </Link>
          </div>

          {/* 右侧：操作按钮 + 通知 + 头像 */}
          <div className="flex items-center gap-3">
            <button className="relative p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/settings')}
              className="relative p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 border-2 border-blue-200 flex items-center justify-center text-white text-xs font-bold">
              U
            </div>
          </div>
        </div>
      </header>

      {/* ── 主体区域 ───────────────────────────────────────── */}
      <DependencyHealthBanner />
      <div className="flex flex-1 overflow-hidden">
        {/* 侧边栏 */}
        <aside className="w-60 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col overflow-hidden">
          {/* 品牌 Logo 区 */}
          <div className="px-5 pt-5 pb-3">
            <div className="flex items-center gap-3 mb-1.5">
              <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <BookOpen className="w-4.5 h-4.5 text-white" />
              </div>
              <div className="leading-tight">
                <div className="font-extrabold text-blue-700 text-sm">EduDoc</div>
                <div className="font-extrabold text-blue-700 text-sm">Platform</div>
              </div>
            </div>
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              教育文档处理平台
            </p>
          </div>

          {/* 主导航 */}
          <nav className="flex-1 px-3 py-4 overflow-y-auto">
            <div className="mb-2 px-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
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
                      ? 'bg-blue-600 text-white font-medium shadow-sm shadow-blue-200'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-blue-600 font-medium'
                  }`}
                >
                  <item.icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-blue-100' : 'text-slate-400 group-hover:text-blue-500'}`} />
                  <span className="text-xs font-semibold tracking-wide">{item.name}</span>
                </button>
              );
            })}
          </nav>

          {/* 底部导航 */}
          <div className="px-3 py-4 border-t border-slate-100 bg-slate-50/50">
            <div className="mb-2 px-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
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
                      ? 'bg-slate-200/50 text-slate-800 font-semibold'
                      : 'text-slate-500 hover:bg-slate-200/30 hover:text-slate-700 font-medium'
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
