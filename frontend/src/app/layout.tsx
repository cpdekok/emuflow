"use client";

import "./globals.css";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <html lang="nl" className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>EmuFlow Dashboard</title>
        <meta name="description" content="EmuFlow - Emulator Management Dashboard" />
      </head>
      <body className="bg-slate-900 text-white antialiased">
        <div className="flex min-h-screen">
          {/* Mobile overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-20 bg-black/60 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar — hidden on mobile, shown via overlay */}
          <div
            className={`fixed inset-y-0 left-0 z-30 transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 lg:flex lg:flex-shrink-0 ${
              sidebarOpen ? "translate-x-0" : "-translate-x-full"
            }`}
          >
            <Sidebar />
          </div>

          {/* Main content */}
          <div className="flex flex-col flex-1 min-w-0">
            {/* Mobile top bar */}
            <header className="flex items-center gap-3 px-4 py-3 bg-slate-900 border-b border-slate-700/60 lg:hidden">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                aria-label={sidebarOpen ? "Sluit menu" : "Open menu"}
              >
                {sidebarOpen ? (
                  <XMarkIcon className="w-6 h-6" />
                ) : (
                  <Bars3Icon className="w-6 h-6" />
                )}
              </button>
              <span className="text-lg font-bold">🎮 EmuFlow</span>
            </header>

            {/* Page content */}
            <main className="flex-1 p-6 lg:p-8 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
