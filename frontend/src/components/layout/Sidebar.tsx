import { NavLink } from 'react-router-dom';
import {
  Home,
  FolderOpen,
  MessageSquare,
  Search,
  Settings,
  Activity,
  FileText,
  Sun,
  Moon,
} from 'lucide-react';
import { useStore } from '@/store';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Home },
  { path: '/projects', label: 'Projects', icon: FolderOpen },
  { path: '/sessions', label: 'Sessions', icon: MessageSquare },
  { path: '/prompts', label: 'Prompts', icon: FileText },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/analytics', label: 'Analytics', icon: Activity },
];

export default function Sidebar() {
  const theme = useStore((state) => state.ui.theme);
  const toggleTheme = useStore((state) => state.toggleTheme);

  return (
    <aside className="w-60 bg-layer-secondary border-r border-primary-c flex flex-col">
      {/* Header */}
      <div className="px-5 py-5 border-b border-primary-c flex items-center justify-between">
        <h1 className="text-xl font-semibold text-primary-c">ClaudeLens</h1>
        <button
          onClick={toggleTheme}
          className="p-1.5 bg-layer-tertiary border border-primary-c rounded-lg text-tertiary-c hover:bg-border hover:text-primary-c transition-all duration-200"
          title="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-3 text-tertiary-c hover:bg-layer-tertiary hover:text-primary-c transition-all duration-200 ${
                isActive
                  ? 'bg-layer-tertiary text-primary-c border-l-[3px] border-primary'
                  : ''
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div className="mt-auto p-5">
        <button className="flex items-center gap-3 px-3 py-2.5 w-full text-tertiary-c hover:bg-layer-tertiary hover:text-primary-c rounded-lg transition-all duration-200">
          <Settings className="h-5 w-5" />
          <span className="text-sm font-medium">Settings</span>
        </button>
      </div>
    </aside>
  );
}
