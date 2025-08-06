import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  ColorBlindMode,
  ColorPalette,
  colorBlindPalettes,
} from './colorBlindUtils';

interface ColorBlindContextType {
  mode: ColorBlindMode;
  setMode: (mode: ColorBlindMode) => void;
  colors: ColorPalette;
  getCSSVariables: () => Record<string, string>;
}

const ColorBlindContext = createContext<ColorBlindContextType | undefined>(
  undefined
);

const useColorBlind = () => {
  const context = useContext(ColorBlindContext);
  if (!context) {
    throw new Error('useColorBlind must be used within a ColorBlindProvider');
  }
  return context;
};

interface ColorBlindProviderProps {
  children: React.ReactNode;
}

export const ColorBlindProvider: React.FC<ColorBlindProviderProps> = ({
  children,
}) => {
  const [mode, setMode] = useState<ColorBlindMode>(() => {
    // Load from localStorage if available
    const saved = localStorage.getItem('colorBlindMode');
    return (saved as ColorBlindMode) || 'none';
  });

  const colors = colorBlindPalettes[mode];

  // Save to localStorage when mode changes
  useEffect(() => {
    localStorage.setItem('colorBlindMode', mode);

    // Apply CSS variables to root element
    const root = document.documentElement;
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    // Add class to body for additional styling if needed
    document.body.classList.remove(
      'color-blind-protanopia',
      'color-blind-deuteranopia',
      'color-blind-tritanopia',
      'color-blind-monochrome'
    );
    if (mode !== 'none') {
      document.body.classList.add(`color-blind-${mode}`);
    }
  }, [mode, colors]);

  const getCSSVariables = () => {
    const vars: Record<string, string> = {};
    Object.entries(colors).forEach(([key, value]) => {
      vars[`--color-${key}`] = value;
    });
    return vars;
  };

  return (
    <ColorBlindContext.Provider
      value={{ mode, setMode, colors, getCSSVariables }}
    >
      {children}
    </ColorBlindContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export { useColorBlind };
