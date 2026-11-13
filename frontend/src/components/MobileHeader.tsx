import React from "react";
import { Menu, Building2, PlusCircle } from "lucide-react";
import { UserProfile } from "../types";
import { ThemeToggle } from "./ThemeToggle";

interface MobileHeaderProps {
  onOpenMobileMenu: () => void;
  onOpenOriginationModal: () => void;
  currentUser: UserProfile;
}

export const MobileHeader: React.FC<MobileHeaderProps> = ({
  onOpenMobileMenu,
  onOpenOriginationModal,
  currentUser,
}) => {
  return (
    <header className="lg:hidden sticky top-0 z-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800 h-16 px-4 flex items-center justify-between transition-colors">
      {/* Left: Hamburger + Brand */}
      <div className="flex items-center space-x-3 overflow-hidden">
        <button
          onClick={onOpenMobileMenu}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none cursor-pointer"
          aria-label="Open Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2.5 overflow-hidden">
          <div className="p-1.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-lg text-white shadow-md shadow-cyan-500/20 flex-shrink-0">
            <Building2 className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <span className="text-sm font-bold text-slate-900 dark:text-white tracking-tight truncate block">
              Loan Intelligence
            </span>
            <span className="text-[9px] text-cyan-600 dark:text-cyan-400 font-mono tracking-wider block -mt-0.5">
              ORIGINATION &amp; RISK
            </span>
          </div>
        </div>
      </div>

      {/* Right: Theme Toggle & Quick Action & Role Badge */}
      <div className="flex items-center space-x-2">
        <ThemeToggle compact />
        <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          {currentUser.role}
        </span>
        <button
          onClick={onOpenOriginationModal}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-lg text-xs font-medium shadow-sm transition-all cursor-pointer"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Simulate</span>
        </button>
      </div>
    </header>
  );
};
