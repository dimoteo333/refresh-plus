"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { bookingApi } from "@/lib/api";
import { Booking, BookingCreate } from "@/types/booking";

// TODO: 실제 인증 시스템 구현 후 사용자 ID 가져오기
const getUserId = () => "test-user-id";

export function useBookings(status?: string) {
  const userId = getUserId();

  return useQuery({
    queryKey: ["bookings", status],
    queryFn: async () => {
      const response = await bookingApi.getHistory(userId, { status });
      return response.data as Booking[];
    },
  });
}

export function useCreateBooking() {
  const userId = getUserId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (bookingData: BookingCreate) => {
      const response = await bookingApi.create(userId, bookingData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}
