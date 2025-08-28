import { NavLink, useNavigate } from 'react-router-dom';
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
  Download,
  Shield,
  LogOut,
  Users,
  Gauge,
} from 'lucide-react';
import { useStore } from '@/store';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Home },
  { path: '/projects', label: 'Projects', icon: FolderOpen },
  { path: '/sessions', label: 'Sessions', icon: MessageSquare },
  { path: '/prompts', label: 'Prompts', icon: FileText },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/analytics', label: 'Analytics', icon: Activity },
  { path: '/usage', label: 'Usage', icon: Gauge },
  { path: '/import-export', label: 'Import/Export', icon: Download },
  { path: '/backup', label: 'Backup & Restore', icon: Shield },
];

export default function Sidebar() {
  const theme = useStore((state) => state.ui.theme);
  const toggleTheme = useStore((state) => state.toggleTheme);
  const setApiKey = useStore((state) => state.setApiKey);
  const setAccessToken = useStore((state) => state.setAccessToken);
  const { apiKey, accessToken } = useStore((state) => state.auth);
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    setApiKey(null);
    setAccessToken(null);
    toast.success('Logged out successfully');
    navigate('/login');
  };

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

      {/* Settings and Logout */}
      <div className="mt-auto p-5 space-y-2">
        {/* Admin Dashboard - Only for admin users */}
        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 w-full text-tertiary-c hover:bg-layer-tertiary hover:text-primary-c rounded-lg transition-all duration-200 ${
                isActive ? 'bg-layer-tertiary text-primary-c' : ''
              }`
            }
          >
            <Users className="h-5 w-5" />
            <span className="text-sm font-medium">Admin Dashboard</span>
          </NavLink>
        )}

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 w-full text-tertiary-c hover:bg-layer-tertiary hover:text-primary-c rounded-lg transition-all duration-200 ${
              isActive ? 'bg-layer-tertiary text-primary-c' : ''
            }`
          }
        >
          <Settings className="h-5 w-5" />
          <span className="text-sm font-medium">Settings</span>
        </NavLink>

        {/* Show logout button only if authenticated via UI (not via environment API key) */}
        {(accessToken || (apiKey && !import.meta.env.VITE_API_KEY)) && (
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 w-full text-tertiary-c hover:bg-layer-tertiary hover:text-primary-c rounded-lg transition-all duration-200"
          >
            <LogOut className="h-5 w-5" />
            <span className="text-sm font-medium">Logout</span>
          </button>
        )}
      </div>
    </aside>
  );
}
