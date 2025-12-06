"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wishlistApi } from "@/lib/api";

// TODO: 실제 인증 시스템 구현 후 사용자 ID 가져오기
const getUserId = () => "test-user-id";

export function useWishlist() {
  const queryClient = useQueryClient();
  const userId = getUserId();

  const { data: wishlist = [] } = useQuery({
    queryKey: ["wishlist"],
    queryFn: async () => {
      const response = await wishlistApi.getAll(userId);
      return response.data || [];
    },
  });

  const addToWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      const response = await wishlistApi.add(userId, accommodationId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const removeFromWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      // Find the wishlist item ID for this accommodation
      const item = wishlist.find((w: any) => w.accommodation_id === accommodationId);
      if (!item) throw new Error("Wishlist item not found");

      const response = await wishlistApi.remove(userId, item.id);
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
    isLoading: addToWishlistMutation.isPending || removeFromWishlistMutation.isPending,
  };
}
