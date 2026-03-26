// ============================================================
// 🎨 THEME CONFIG — Đổi theme chỉ cần thay dòng ACTIVE_THEME
// ============================================================

export type ThemeName = 'indigo' | 'emerald' | 'blue' | 'orange' | 'rose'

// ▼▼▼ ĐỔI THEME TẠI ĐÂY ▼▼▼
export const ACTIVE_THEME: ThemeName = 'blue'
// ▲▲▲ ĐỔI THEME TẠI ĐÂY ▲▲▲

interface ThemeColors {
  // Primary palette
  50:  string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  // Gradient end color (secondary)
  grad: string
  // Chart stroke
  chart: string
  // Tailwind class names (for bg / text / border / ring)
  bgLight:     string   // e.g. bg-indigo-50
  bgMed:       string   // e.g. bg-indigo-600
  bgGrad:      string   // e.g. from-indigo-600 to-violet-600
  textPrimary: string   // e.g. text-indigo-700
  textMed:     string   // e.g. text-indigo-600
  textLight:   string   // e.g. text-indigo-500
  borderLight: string   // e.g. border-indigo-200
  ring:        string   // e.g. focus:ring-indigo-200
  hoverBg:     string   // e.g. hover:bg-indigo-700
  activeBg:    string   // sidebar active pill
}

const themes: Record<ThemeName, ThemeColors> = {
  indigo: {
    50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc',
    400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca',
    grad: '#8b5cf6', chart: '#6366f1',
    bgLight: 'bg-indigo-50',   bgMed: 'bg-indigo-600',
    bgGrad: 'bg-gradient-to-r from-indigo-600 to-violet-600',
    textPrimary: 'text-indigo-700', textMed: 'text-indigo-600', textLight: 'text-indigo-500',
    borderLight: 'border-indigo-200', ring: 'focus:ring-indigo-200',
    hoverBg: 'hover:bg-indigo-700', activeBg: 'bg-indigo-50',
  },
  emerald: {
    50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7',
    400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857',
    grad: '#0d9488', chart: '#10b981',
    bgLight: 'bg-emerald-50',   bgMed: 'bg-emerald-600',
    bgGrad: 'bg-gradient-to-r from-emerald-600 to-teal-600',
    textPrimary: 'text-emerald-700', textMed: 'text-emerald-600', textLight: 'text-emerald-500',
    borderLight: 'border-emerald-200', ring: 'focus:ring-emerald-200',
    hoverBg: 'hover:bg-emerald-700', activeBg: 'bg-emerald-50',
  },
  blue: {
    50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
    400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
    grad: '#0ea5e9', chart: '#3b82f6',
    bgLight: 'bg-blue-50',   bgMed: 'bg-blue-600',
    bgGrad: 'bg-gradient-to-r from-blue-600 to-sky-500',
    textPrimary: 'text-blue-700', textMed: 'text-blue-600', textLight: 'text-blue-500',
    borderLight: 'border-blue-200', ring: 'focus:ring-blue-200',
    hoverBg: 'hover:bg-blue-700', activeBg: 'bg-blue-50',
  },
  orange: {
    50: '#fff7ed', 100: '#ffedd5', 200: '#fed7aa', 300: '#fdba74',
    400: '#fb923c', 500: '#f97316', 600: '#ea580c', 700: '#c2410c',
    grad: '#f59e0b', chart: '#f97316',
    bgLight: 'bg-orange-50',   bgMed: 'bg-orange-600',
    bgGrad: 'bg-gradient-to-r from-orange-600 to-amber-500',
    textPrimary: 'text-orange-700', textMed: 'text-orange-600', textLight: 'text-orange-500',
    borderLight: 'border-orange-200', ring: 'focus:ring-orange-200',
    hoverBg: 'hover:bg-orange-700', activeBg: 'bg-orange-50',
  },
  rose: {
    50: '#fff1f2', 100: '#ffe4e6', 200: '#fecdd3', 300: '#fda4af',
    400: '#fb7185', 500: '#f43f5e', 600: '#e11d48', 700: '#be123c',
    grad: '#ec4899', chart: '#f43f5e',
    bgLight: 'bg-rose-50',   bgMed: 'bg-rose-600',
    bgGrad: 'bg-gradient-to-r from-rose-600 to-pink-600',
    textPrimary: 'text-rose-700', textMed: 'text-rose-600', textLight: 'text-rose-500',
    borderLight: 'border-rose-200', ring: 'focus:ring-rose-200',
    hoverBg: 'hover:bg-rose-700', activeBg: 'bg-rose-50',
  },
}

export const theme = themes[ACTIVE_THEME]

// Hex colors for use in inline styles / recharts (can't use Tailwind classes there)
export const themeHex = {
  primary:   theme[600],
  primary50: theme[50],
  primary100:theme[100],
  primary300:theme[300],
  primary400:theme[400],
  grad:      theme.grad,
  chart:     theme.chart,
}
