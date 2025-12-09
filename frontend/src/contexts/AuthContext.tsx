"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

interface User {
  id: string;
  name: string;
  lulu_lala_user_id: string;
  points: number;
  available_nights: number;
  is_verified: boolean;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const queryClient = useQueryClient();

  // 앱 시작 시 사용자 정보 확인
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsLoading(false);
        return;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        console.log("Auth check successful, user:", data.user);
      } else {
        // 토큰이 만료되었거나 유효하지 않음
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        // 쿠키도 삭제
        document.cookie = "access_token=; path=/; max-age=0";
        document.cookie = "refresh_token=; path=/; max-age=0";
        setUser(null);
        console.log("Auth check failed, clearing tokens");
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include", // 쿠키 포함
          body: JSON.stringify({ username, password }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "로그인에 실패했습니다");
      }

      const data = await response.json();

      // 토큰 저장 (localStorage + 쿠키)
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      // 쿠키에도 저장 (미들웨어에서 확인용)
      document.cookie = `access_token=${data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}`; // 7일
      document.cookie = `refresh_token=${data.refresh_token}; path=/; max-age=${30 * 24 * 60 * 60}`; // 30일

      // 사용자 정보 설정
      setUser(data.user);
      console.log("Login successful, user:", data.user);

      // 모든 쿼리 무효화하여 최신 데이터 가져오기
      queryClient.invalidateQueries();
      console.log("All queries invalidated after login");

      return data;
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (token) {
        // 서버에 로그아웃 요청
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          credentials: "include",
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // 로컬 상태 정리
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      // 쿠키도 삭제
      document.cookie = "access_token=; path=/; max-age=0";
      document.cookie = "refresh_token=; path=/; max-age=0";

      setUser(null);

      // 모든 쿼리 캐시 클리어
      queryClient.clear();
      console.log("All queries cleared after logout");

      router.push("/");
    }
  };

  const refreshUser = async () => {
    console.log("Refreshing user data...");
    await checkAuth();
    // 사용자 정보 갱신 후 관련 쿼리 무효화
    queryClient.invalidateQueries({ queryKey: ["bookings"] });
    queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    queryClient.invalidateQueries({ queryKey: ["accommodations"] });
    console.log("User data refreshed, related queries invalidated");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
