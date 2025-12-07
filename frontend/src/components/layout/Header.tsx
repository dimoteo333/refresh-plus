"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { User, CreditCard, LogOut, Loader2 } from "lucide-react";

export default function Header() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-blue-600">
              Refresh Plus
            </Link>
            <nav className="ml-10 flex items-center space-x-4">
              <Link
                href="/"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                홈
              </Link>
              <Link
                href="/search"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                숙소 검색
              </Link>
              <Link
                href="/my"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                MY 숙소
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
            {isLoading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">로딩 중...</span>
              </div>
            ) : isAuthenticated && user ? (
              <div className="flex items-center gap-4">
                {/* 사용자 이름 */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg">
                  <User className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-semibold text-blue-900">
                    {user.name}님
                  </span>
                </div>

                {/* 포인트 */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 rounded-lg">
                  <CreditCard className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-semibold text-green-900">
                    {user.points}P
                  </span>
                </div>

                {/* 로그아웃 버튼 */}
                <button
                  onClick={logout}
                  className="flex items-center gap-2 px-3 py-1.5 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4 text-red-600" />
                  <span className="text-sm font-medium text-red-900">로그아웃</span>
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
              >
                로그인
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
