"use client";

import { useQuery } from "@tanstack/react-query";
import { accommodationApi } from "@/lib/api";
import { Accommodation } from "@/types/accommodation";

// TODO: 실제 인증 시스템 구현 후 사용자 ID 가져오기
const getUserId = () => "test-user-id";

interface UseAccommodationsParams {
  region?: string;
  sortBy?: "popularity" | "price" | "rating";
  page?: number;
  limit?: number;
}

export function useAccommodations(params?: UseAccommodationsParams) {
  const userId = getUserId();

  return useQuery({
    queryKey: ["accommodations", params],
    queryFn: async () => {
      const response = await accommodationApi.getAll(userId, params);
      return response.data as Accommodation[];
    },
  });
}

export function useAccommodationDetail(accommodationId: string) {
  const userId = getUserId();

  return useQuery({
    queryKey: ["accommodation", accommodationId],
    queryFn: async () => {
      const response = await accommodationApi.getDetail(userId, accommodationId);
      return response.data as Accommodation;
    },
    enabled: !!accommodationId,
  });
}
