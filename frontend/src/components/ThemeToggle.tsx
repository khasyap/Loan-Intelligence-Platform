import React from "react";
import { Sun, Moon, Laptop } from "lucide-react";
import { useTheme, Theme } from "../context/ThemeContext";

interface ThemeToggleProps {
  compact?: boolean;
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ compact = false, className = "" }) => {
  const { theme, resolvedTheme, setTheme } = useTheme();

  const options: { id: Theme; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "light", label: "Light", icon: Sun },
    { id: "dark", label: "Dark", icon: Moon },
    { id: "system", label: "Auto", icon: Laptop },
  ];

  if (compact) {
    // Quick single-button toggle between light and dark
    const nextTheme: Theme = resolvedTheme === "dark" ? "light" : "dark";
    return (
      <button
        onClick={() => setTheme(nextTheme)}
        className={`p-2 rounded-lg transition-colors border text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-sm cursor-pointer ${className}`}
        title={`Switch to ${nextTheme} theme (current: ${theme})`}
        aria-label="Toggle theme"
      >
        {resolvedTheme === "dark" ? (
          <Sun className="w-4 h-4 text-amber-400" />
        ) : (
          <Moon className="w-4 h-4 text-indigo-500" />
        )}
      </button>
    );
  }

  return (
    <div
      className={`inline-flex items-center p-0.5 rounded-lg border bg-slate-100 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 ${className}`}
      role="group"
      aria-label="Theme mode"
    >
      {options.map((opt) => {
        const Icon = opt.icon;
        const isActive = theme === opt.id;
        return (
          <button
            key={opt.id}
            onClick={() => setTheme(opt.id)}
            className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer ${
              isActive
                ? "bg-white dark:bg-slate-800 text-cyan-600 dark:text-cyan-400 shadow-sm font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
            title={`${opt.label} mode`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
};
