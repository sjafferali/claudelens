import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  MessageSquare,
  Search,
  ChevronLeft,
  Settings,
  Activity,
} from 'lucide-react';
import { useStore } from '@/store';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/projects', label: 'Projects', icon: FolderOpen },
  { path: '/sessions', label: 'Sessions', icon: MessageSquare },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/analytics', label: 'Analytics', icon: Activity },
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useStore((state) => state.ui);

  return (
    <aside
      className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-background border-r border-border transition-all duration-300 ${
        sidebarOpen ? 'w-64' : 'w-16'
      }`}
    >
      <div className="flex flex-col h-full">
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-accent'
                    }`
                  }
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {sidebarOpen && (
                    <span className="truncate">{item.label}</span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="p-4 border-t border-border">
          <button className="flex items-center gap-3 px-3 py-2 w-full rounded-md hover:bg-accent transition-colors">
            <Settings className="h-5 w-5 flex-shrink-0" />
            {sidebarOpen && <span className="truncate">Settings</span>}
          </button>
        </div>

        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-6 p-1 bg-background border border-border rounded-full hover:bg-accent transition-colors"
          aria-label="Toggle sidebar"
        >
          <ChevronLeft
            className={`h-4 w-4 transition-transform ${
              !sidebarOpen ? 'rotate-180' : ''
            }`}
          />
        </button>
      </div>
    </aside>
  );
}
