"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { bookingApi } from "@/lib/api";
import { Booking, BookingCreate } from "@/types/booking";

export function useBookings(status?: string) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["bookings", status],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await bookingApi.getHistory(token, { status });
      return response.data as Booking[];
    },
  });
}

export function useCreateBooking() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (bookingData: BookingCreate) => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await bookingApi.create(token, bookingData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}
