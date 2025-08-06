// Utility functions and constants for color blind mode
// Separated from ColorBlindContext.tsx to avoid fast refresh warnings

export type ColorBlindMode =
  | 'none'
  | 'protanopia'
  | 'deuteranopia'
  | 'tritanopia'
  | 'monochrome';

export interface ColorPalette {
  user: string;
  assistant: string;
  tool: string;
  system: string;
  branch: string;
  sidechain: string;
  success: string;
  error: string;
  warning: string;
  info: string;
}

export const defaultPalette: ColorPalette = {
  user: '#3b82f6', // blue-500
  assistant: '#10b981', // emerald-500
  tool: '#9333ea', // purple-600
  system: '#64748b', // slate-500
  branch: '#fbbf24', // amber-400
  sidechain: '#9333ea', // purple-600
  success: '#22c55e', // green-500
  error: '#ef4444', // red-500
  warning: '#f59e0b', // amber-500
  info: '#3b82f6', // blue-500
};

// Color blind friendly palettes
// Based on research from colorbrewer2.org and accessible color guidelines
export const colorBlindPalettes: Record<ColorBlindMode, ColorPalette> = {
  none: defaultPalette,

  // Red-green color blindness (most common)
  protanopia: {
    user: '#0173B2', // Blue
    assistant: '#56B4E9', // Light blue
    tool: '#CC79A7', // Pink
    system: '#999999', // Gray
    branch: '#E69F00', // Orange
    sidechain: '#CC79A7', // Pink
    success: '#009E73', // Teal
    error: '#D55E00', // Red-orange
    warning: '#F0E442', // Yellow
    info: '#0173B2', // Blue
  },

  // Red-green color blindness (second most common)
  deuteranopia: {
    user: '#0173B2', // Blue
    assistant: '#56B4E9', // Light blue
    tool: '#CC79A7', // Pink
    system: '#999999', // Gray
    branch: '#E69F00', // Orange
    sidechain: '#CC79A7', // Pink
    success: '#009E73', // Teal
    error: '#D55E00', // Red-orange
    warning: '#F0E442', // Yellow
    info: '#0173B2', // Blue
  },

  // Blue-yellow color blindness (rare)
  tritanopia: {
    user: '#D55E00', // Red-orange
    assistant: '#009E73', // Teal
    tool: '#CC79A7', // Pink
    system: '#999999', // Gray
    branch: '#0173B2', // Blue
    sidechain: '#CC79A7', // Pink
    success: '#009E73', // Teal
    error: '#D55E00', // Red-orange
    warning: '#56B4E9', // Light blue
    info: '#0173B2', // Blue
  },

  // Complete color blindness (very rare)
  monochrome: {
    user: '#000000', // Black
    assistant: '#404040', // Dark gray
    tool: '#808080', // Medium gray
    system: '#B0B0B0', // Light gray
    branch: '#606060', // Gray
    sidechain: '#808080', // Medium gray
    success: '#202020', // Very dark gray
    error: '#000000', // Black
    warning: '#505050', // Gray
    info: '#303030', // Dark gray
  },
};

// Export color blind modes for use in settings
export const colorBlindModes: {
  value: ColorBlindMode;
  label: string;
  description: string;
}[] = [
  { value: 'none', label: 'None', description: 'Default colors' },
  {
    value: 'protanopia',
    label: 'Protanopia',
    description: 'Red-green color blindness (red weak)',
  },
  {
    value: 'deuteranopia',
    label: 'Deuteranopia',
    description: 'Red-green color blindness (green weak)',
  },
  {
    value: 'tritanopia',
    label: 'Tritanopia',
    description: 'Blue-yellow color blindness',
  },
  {
    value: 'monochrome',
    label: 'Monochrome',
    description: 'Complete color blindness',
  },
];
