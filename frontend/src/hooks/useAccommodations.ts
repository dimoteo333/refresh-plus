"use client";

import { useQuery } from "@tanstack/react-query";
import { accommodationApi } from "@/lib/api";
import { Accommodation, ScoreBasedRecommendation } from "@/types/accommodation";
import { useAuth } from "@/contexts/AuthContext";

interface UseAccommodationsParams {
  region?: string;
  sortBy?: "popularity" | "price" | "rating";
  page?: number;
  limit?: number;
}

export function useAccommodations(params?: UseAccommodationsParams) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["accommodations", params],
    queryFn: async () => {
      const token = localStorage.getItem("access_token") || "";
      const response = await accommodationApi.getAll(token, params);
      return response.data as Accommodation[];
    },
    enabled: isAuthenticated, // 로그인한 경우에만 쿼리 실행
  });
}

export function useAccommodationDetail(accommodationId: string) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["accommodation", accommodationId],
    queryFn: async () => {
      const token = localStorage.getItem("access_token") || "";
      const response = await accommodationApi.getDetail(token, accommodationId);
      return response.data as Accommodation;
    },
    enabled: !!accommodationId && isAuthenticated, // 숙소 ID와 사용자 모두 있을 때만 실행
  });
}

export function useScoreBasedRecommendations(limit?: number) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["score-based-recommendations", limit],
    queryFn: async () => {
      const response = await accommodationApi.getScoreBasedRecommendations(limit);
      return response.data as ScoreBasedRecommendation[];
    },
    enabled: isAuthenticated, // 로그인한 경우에만 쿼리 실행
  });
}
