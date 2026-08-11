import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'engineering-report-theme';

export const THEMES = [
  { id: 'dark', label: 'Dark' },
  { id: 'paper', label: 'Paper' },
];

const ThemeContext = createContext(null);

function preferredTheme() {
  if (typeof window === 'undefined') return 'paper';
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (THEMES.some((theme) => theme.id === saved)) return saved;
  return 'paper';
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(preferredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const value = useMemo(() => ({ theme, setTheme, themes: THEMES }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used inside ThemeProvider');
  return context;
}
