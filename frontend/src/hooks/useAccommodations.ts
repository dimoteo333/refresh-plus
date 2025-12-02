"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { accommodationApi } from "@/lib/api";
import { Accommodation } from "@/types/accommodation";

interface UseAccommodationsParams {
  region?: string;
  sortBy?: "popularity" | "price" | "rating";
  page?: number;
  limit?: number;
}

export function useAccommodations(params?: UseAccommodationsParams) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["accommodations", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await accommodationApi.getAll(token, params);
      return response.data as Accommodation[];
    },
  });
}

export function useAccommodationDetail(accommodationId: string) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["accommodation", accommodationId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await accommodationApi.getDetail(token, accommodationId);
      return response.data as Accommodation;
    },
    enabled: !!accommodationId,
  });
}
