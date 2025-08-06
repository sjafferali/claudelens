import React from 'react';
import { useColorBlind } from '@/contexts/ColorBlindContext';
import { colorBlindModes } from '@/contexts/colorBlindUtils';
import { Eye, Palette, Check } from 'lucide-react';
import { cn } from '@/utils/cn';

interface ColorBlindSettingsProps {
  className?: string;
  compact?: boolean;
}

const ColorBlindSettings: React.FC<ColorBlindSettingsProps> = ({
  className = '',
  compact = false,
}) => {
  const { mode, setMode, colors } = useColorBlind();

  if (compact) {
    // Compact dropdown version for header/toolbar
    return (
      <div className={cn('relative group', className)}>
        <button
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-all',
            'bg-layer-tertiary text-tertiary-c hover:text-primary-c',
            mode !== 'none' &&
              'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30'
          )}
          title="Color blind mode settings"
        >
          <Eye className="h-4 w-4" />
          <span className="hidden sm:inline">Accessibility</span>
        </button>

        <div className="absolute right-0 mt-1 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
          <div className="p-2">
            <div className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider px-2 py-1">
              Color Blind Mode
            </div>
            {colorBlindModes.map((option) => (
              <button
                key={option.value}
                onClick={() => setMode(option.value)}
                className={cn(
                  'w-full text-left px-2 py-1.5 rounded text-sm transition-colors',
                  'hover:bg-slate-100 dark:hover:bg-slate-700',
                  mode === option.value &&
                    'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{option.label}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {option.description}
                    </div>
                  </div>
                  {mode === option.value && (
                    <Check className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Full settings panel version
  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2 mb-4">
        <Palette className="h-5 w-5 text-slate-500" />
        <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
          Color Accessibility Settings
        </h3>
      </div>

      <div className="space-y-2">
        {colorBlindModes.map((option) => (
          <button
            key={option.value}
            onClick={() => setMode(option.value)}
            className={cn(
              'w-full text-left p-3 rounded-lg border transition-all',
              mode === option.value
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium text-slate-700 dark:text-slate-200">
                  {option.label}
                </div>
                <div className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  {option.description}
                </div>
              </div>
              <div className="ml-4">
                {mode === option.value ? (
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                    <Check className="h-5 w-5" />
                    <span className="text-sm font-medium">Active</span>
                  </div>
                ) : (
                  <button className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
                    Activate
                  </button>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Color Preview */}
      <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">
          Current Color Palette Preview
        </h4>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(colors)
            .slice(0, 6)
            .map(([name, color]) => (
              <div key={name} className="flex items-center gap-2">
                <div
                  className="w-8 h-8 rounded border border-slate-300 dark:border-slate-600"
                  style={{ backgroundColor: color }}
                />
                <div className="text-sm">
                  <div className="font-medium text-slate-700 dark:text-slate-200 capitalize">
                    {name}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {color}
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
        <p className="text-xs text-amber-700 dark:text-amber-300">
          <strong>Note:</strong> Color blind modes adjust the color palette
          throughout the application to improve visibility for users with color
          vision deficiencies. Changes are saved automatically.
        </p>
      </div>
    </div>
  );
};

export default ColorBlindSettings;
