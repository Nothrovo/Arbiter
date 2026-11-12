/* Theme manager — applies a design-token theme to <html data-theme> and
   persists the choice to localStorage. Imported by settings and applied
   early via an inline script in index.html to avoid a flash of unstyled
   content. */

export const THEMES = [
  ['dark', 'Gelap (Default)', '#111111'],
  ['light', 'Terang', '#f4f4f5'],
  ['midnight', 'Midnight Biru', '#121a2f'],
  ['ember', 'Ember Amber', '#201910'],
  ['forest', 'Hutan Hijau', '#131c15'],
  ['violet', 'Violet', '#1b1528'],
  ['contrast', 'Kontras Tinggi', '#000000'],
];

const KEY = 'arbiter:theme';

export function themeNames() {
  return THEMES.map(([key]) => key);
}

export function getTheme() {
  try {
    const stored = localStorage.getItem(KEY);
    if (stored && themeNames().includes(stored)) return stored;
  } catch {
    /* localStorage unavailable (privacy mode) */
  }
  return 'dark';
}

export function applyTheme(name) {
  const theme = themeNames().includes(name) ? name : 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* non-fatal: theme still applies for this session */
  }
  return theme;
}

export function initTheme() {
  applyTheme(getTheme());
}
