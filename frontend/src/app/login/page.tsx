"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Lock, User as UserIcon, AlertCircle, CheckCircle, Loader2 } from "lucide-react";

function LoginContent() {
  const [step, setStep] = useState<"welcome" | "credentials">("welcome");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const { login, user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/";

  // 이미 로그인되어 있으면 리다이렉트
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      console.log("Already authenticated, redirecting to:", redirect);
      router.push(redirect);
    }
  }, [isLoading, isAuthenticated, user, redirect, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoggingIn(true);

    try {
      const result = await login(username, password);
      console.log("Login successful, user data:", result);

      // 로그인 성공 - 짧은 딜레이 후 리다이렉트
      // (상태 업데이트와 쿼리 무효화를 위한 시간)
      setTimeout(() => {
        console.log("Redirecting to:", redirect);
        router.push(redirect);
        setIsLoggingIn(false);
      }, 200);

    } catch (err: any) {
      console.error("Login error:", err);
      setError(err.message || "로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.");
      setIsLoggingIn(false);
    }
  };

  // 웰컴 스크린
  if (step === "welcome") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-white flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* 로고 & 타이틀 */}
          <div className="text-center mb-8">
            <div className="inline-block p-4 bg-gradient-to-br from-sky-500 to-blue-600 rounded-3xl mb-4 shadow-xl">
              <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">
              Refresh Plus
            </h1>
            <p className="text-slate-600">
              신한은행 임직원을 위한 연성소 예약 플랫폼
            </p>
          </div>

          {/* 기능 소개 */}
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-sky-100/70 mb-6">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-sky-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">포인트 기반 공정 배정</h3>
                  <p className="text-sm text-slate-600 mt-1">높은 점수 순으로 자동 배정되어 공정합니다</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">실시간 알림</h3>
                  <p className="text-sm text-slate-600 mt-1">예약 결과를 즉시 확인할 수 있습니다</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">간편한 관리</h3>
                  <p className="text-sm text-slate-600 mt-1">찜한 숙소와 예약을 한눈에 관리합니다</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setStep("credentials")}
              className="w-full mt-8 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white py-4 px-6 rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all transform hover:scale-[1.02] active:scale-[0.98]"
            >
              룰루랄라 계정으로 로그인
            </button>

            <p className="text-xs text-center text-slate-500 mt-4">
              기존 룰루랄라 계정으로 로그인하시면 자동으로 연동됩니다
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 로그인 폼
  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* 뒤로 가기 버튼 */}
        <button
          onClick={() => setStep("welcome")}
          className="mb-6 text-slate-600 hover:text-slate-900 flex items-center gap-2 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>이전으로</span>
        </button>

        {/* 로그인 카드 */}
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-sky-100/70">
          <div className="text-center mb-8">
            <div className="inline-block p-3 bg-gradient-to-br from-sky-500 to-blue-600 rounded-2xl mb-3">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900">로그인</h2>
            <p className="text-slate-600 mt-1">룰루랄라 계정 정보를 입력해주세요</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                룰루랄라 아이디
              </label>
              <div className="relative">
                <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="아이디를 입력하세요"
                  className="w-full pl-12 pr-4 py-4 rounded-xl border-2 border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all"
                  required
                  autoFocus
                  disabled={isLoggingIn}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                비밀번호
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  className="w-full pl-12 pr-4 py-4 rounded-xl border-2 border-slate-200 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 outline-none transition-all"
                  required
                  disabled={isLoggingIn}
                />
              </div>
            </div>

            <div className="bg-sky-50 rounded-xl p-4 space-y-2">
              <p className="text-xs text-sky-900 font-medium">보안 안내</p>
              <ul className="text-xs text-sky-700 space-y-1">
                <li>• 비밀번호는 안전하게 암호화되어 저장됩니다</li>
                <li>• 자동 예약/취소를 위해 룰루랄라 계정 정보가 필요합니다</li>
                <li>• 첫 로그인은 8-10초 정도 소요됩니다</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={isLoggingIn || isLoading}
              className="w-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 disabled:from-slate-400 disabled:to-slate-500 text-white py-4 px-6 rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
            >
              {isLoggingIn || isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>로그인 중... (8-10초 소요)</span>
                </>
              ) : (
                <span>로그인</span>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-white flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-sky-600" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
