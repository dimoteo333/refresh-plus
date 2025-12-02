"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
              Refresh Plus
            </Link>
            <nav className="ml-10 flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                대시보드
              </Link>
              <Link
                href="/accommodations"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                숙소
              </Link>
              <Link
                href="/bookings"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                예약 현황
              </Link>
              <Link
                href="/wishlist"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                찜하기
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <UserButton afterSignOutUrl="/" />
          </div>
        </div>
      </div>
    </header>
  );
}
