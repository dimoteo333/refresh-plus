"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  Heart,
  Home as HomeIcon,
  Hotel,
  Search,
} from "lucide-react";

const navItems = [
  { label: "홈", icon: HomeIcon, href: "/" },
  { label: "즐겨찾기", icon: Heart, href: "/wishlist" },
  { label: "채팅", icon: Bot, href: "/chat" },
  { label: "검색", icon: Search, href: "/search" },
  { label: "MY숙소", icon: Hotel, href: "/my" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-50">
      <div className="mx-auto max-w-xl px-3 pb-[calc(env(safe-area-inset-bottom)+1rem)]">
        <div className="relative overflow-hidden rounded-[30px] border border-white/25 bg-white/40 shadow-[0_16px_60px_-30px_rgba(59,130,246,0.65)] backdrop-blur-2xl backdrop-saturate-150">
          <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-sky-100/45 to-blue-100/40" />
          <div className="absolute inset-x-6 top-0 h-px bg-white/70 blur-[1px] opacity-80" />
          <div className="relative flex items-center justify-between px-3 py-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className="flex flex-1 flex-col items-center gap-1 py-1 text-[11px] font-semibold text-slate-800 transition-transform active:scale-95"
                >
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-300 ${
                      isActive
                        ? "bg-gradient-to-br from-sky-500 to-blue-600 text-white shadow-lg scale-105"
                        : "bg-white/75 text-sky-700 shadow-inner hover:bg-white/90"
                    } ring-1 ring-white/50`}
                  >
                    <item.icon className="h-6 w-6" />
                  </div>
                  <span className={isActive ? "text-sky-700" : "text-slate-700"}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
