"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { bookingApi } from "@/lib/api";
import { Booking, BookingCreate } from "@/types/booking";
import { useAuth } from "@/contexts/AuthContext";

export function useBookings(status?: string) {
  const { user, isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["bookings", status],
    queryFn: async () => {
      // localStorage에서 토큰 가져오기
      const token = localStorage.getItem("access_token") || "";
      const response = await bookingApi.getHistory(token, { status });
      return response.data as Booking[];
    },
    enabled: isAuthenticated, // 로그인한 경우에만 쿼리 실행
  });
}

export function useCreateBooking() {
  const { user, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (bookingData: BookingCreate) => {
      if (!isAuthenticated) throw new Error("User not authenticated");
      const token = localStorage.getItem("access_token") || "";
      const response = await bookingApi.create(token, bookingData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}
