"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wishlistApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export function useWishlist() {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const { data: wishlist = [], isLoading: wishlistLoading } = useQuery({
    queryKey: ["wishlist"],
    queryFn: async () => {
      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.getAll(token);
      return response.data || [];
    },
    enabled: isAuthenticated, // 로그인한 경우에만 쿼리 실행
  });

  const addToWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      if (!isAuthenticated) throw new Error("User not authenticated");
      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.add(token, accommodationId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const removeFromWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      if (!isAuthenticated) throw new Error("User not authenticated");

      // Find the wishlist item ID for this accommodation
      const item = wishlist.find((w: any) => w.accommodation_id === accommodationId);
      if (!item) throw new Error("Wishlist item not found");

      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.remove(token, item.id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  return {
    wishlist,
    addToWishlist: addToWishlistMutation.mutateAsync,
    removeFromWishlist: removeFromWishlistMutation.mutateAsync,
    isLoading: addToWishlistMutation.isPending || removeFromWishlistMutation.isPending || wishlistLoading,
  };
}
