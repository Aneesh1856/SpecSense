"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="w-full border-b border-white/10 bg-[#0A0A0A] px-6 py-4 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center space-x-8">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
          <span className="text-xl font-bold tracking-tight text-white">SpecSense</span>
        </Link>

        {/* Navigation Links */}
        <div className="flex space-x-6">
          <Link
            href="/"
            className={`text-sm font-medium transition-colors ${
              pathname === "/" ? "text-white" : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Generate
          </Link>
          <Link
            href="/specbot"
            className={`text-sm font-medium transition-colors ${
              pathname === "/specbot" ? "text-white" : "text-gray-400 hover:text-gray-200"
            }`}
          >
            SpecBot
          </Link>
          <Link
            href="/history"
            className={`text-sm font-medium transition-colors ${
              pathname === "/history" ? "text-white" : "text-gray-400 hover:text-gray-200"
            }`}
          >
            History
          </Link>
        </div>
      </div>

      {/* Right side label */}
      <div className="hidden md:flex items-center">
        <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold tracking-wide uppercase">
          Round 2 · NU Hackathon 2026
        </span>
      </div>
    </nav>
  );
}
