import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 보호가 필요한 경로들
const PROTECTED_ROUTES = ["/wishlist", "/my", "/bookings", "/chat"];

// 로그인한 사용자가 접근하면 안 되는 경로들
const AUTH_ROUTES = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 토큰 확인 (쿠키에서만 확인 - 서버 사이드)
  const accessToken = request.cookies.get("access_token")?.value;

  // 보호된 경로 체크
  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // 인증 경로 체크 (로그인 페이지 등)
  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route));

  // 비로그인 상태에서 보호된 경로 접근 시
  if (isProtectedRoute && !accessToken) {
    const redirectUrl = new URL("/login", request.url);
    redirectUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // 로그인 상태에서 로그인 페이지 접근 시
  if (isAuthRoute && accessToken) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

// 미들웨어가 실행될 경로 설정
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
