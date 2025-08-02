import { Menu, Search, Moon, Sun } from 'lucide-react';
import { useStore } from '@/store';

export default function Header() {
  const { toggleSidebar, theme, toggleTheme } = useStore((state) => state.ui);

  return (
    <header className="h-16 bg-background border-b border-border">
      <div className="h-full flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="text-xl font-semibold">ClaudeLens</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search conversations..."
              className="pl-10 pr-4 py-2 w-80 bg-muted/50 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-accent rounded-md transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
