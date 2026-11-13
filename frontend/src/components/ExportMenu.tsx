import React, { useState, useRef, useEffect } from "react";
import { Download, FileSpreadsheet, FileText, Table, ChevronDown, Loader2 } from "lucide-react";
import { downloadReport } from "../services/api";

interface ExportMenuProps {
  baseEndpoint: string; // e.g. "/exports/executive" or "/exports/applications"
  defaultFilename: string; // e.g. "Executive_Portfolio_Report"
  label?: string; // default "Export"
  queryParams?: Record<string, string | number | undefined>;
  size?: "sm" | "md";
  align?: "left" | "right";
  className?: string;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
  baseEndpoint,
  defaultFilename,
  label = "Export",
  queryParams = {},
  size = "md",
  align = "right",
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loadingFormat, setLoadingFormat] = useState<"xlsx" | "pdf" | "csv" | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleDownload = async (format: "xlsx" | "pdf" | "csv") => {
    setLoadingFormat(format);
    setIsOpen(false);
    try {
      const searchParams = new URLSearchParams();
      searchParams.set("format", format);
      Object.entries(queryParams).forEach(([k, v]) => {
        if (v !== undefined && v !== "") {
          searchParams.set(k, String(v));
        }
      });
      const separator = baseEndpoint.includes("?") ? "&" : "?";
      const fullUrl = `${baseEndpoint}${separator}${searchParams.toString()}`;
      const ext = format === "xlsx" ? "xlsx" : format === "pdf" ? "pdf" : "csv";
      const dateStr = new Date().toISOString().slice(0, 10);
      const filename = `${defaultFilename}_${dateStr}.${ext}`;
      await downloadReport(fullUrl, filename);
    } catch (err: any) {
      alert(`Export failed: ${err.message || "Unknown network error"}`);
    } finally {
      setLoadingFormat(null);
    }
  };

  const isSmall = size === "sm";

  return (
    <div className={`relative inline-block text-left ${className}`} ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={loadingFormat !== null}
        className={`inline-flex items-center gap-1.5 font-medium rounded-lg border transition-all shadow-sm focus:outline-none cursor-pointer ${
          isSmall ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-xs sm:text-sm"
        } bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/80 hover:text-slate-900 dark:hover:text-white disabled:opacity-50`}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        {loadingFormat !== null ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-500" />
        ) : (
          <Download className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
        )}
        <span>{loadingFormat ? `Generating ${loadingFormat.toUpperCase()}...` : label}</span>
        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div
          className={`absolute z-50 mt-1.5 w-48 rounded-xl shadow-xl border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 py-1.5 ring-1 ring-black ring-opacity-5 animate-in fade-in zoom-in-95 duration-100 ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800/80 mb-1">
            Download As
          </div>
          <button
            onClick={() => handleDownload("xlsx")}
            className="w-full text-left px-3 py-2 text-xs flex items-center gap-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <div className="p-1 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">Excel Spreadsheet</div>
              <div className="text-[10px] text-slate-600 dark:text-slate-400">.xlsx with styles &amp; filters</div>
            </div>
          </button>
          <button
            onClick={() => handleDownload("csv")}
            className="w-full text-left px-3 py-2 text-xs flex items-center gap-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Table className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">CSV Data File</div>
              <div className="text-[10px] text-slate-600 dark:text-slate-400">.csv comma-separated</div>
            </div>
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            className="w-full text-left px-3 py-2 text-xs flex items-center gap-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <div className="p-1 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400">
              <FileText className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="font-semibold">PDF Document</div>
              <div className="text-[10px] text-slate-600 dark:text-slate-400">.pdf with executive headers</div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};
