"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { wishlistApi } from "@/lib/api";

export function useWishlist() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { data: wishlist = [] } = useQuery({
    queryKey: ["wishlist"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await wishlistApi.getAll(token);
      return response.data || [];
    },
  });

  const addToWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      const response = await wishlistApi.add(token, accommodationId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const removeFromWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No token");

      // Find the wishlist item ID for this accommodation
      const item = wishlist.find((w: any) => w.accommodation_id === accommodationId);
      if (!item) throw new Error("Wishlist item not found");

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
    isLoading: addToWishlistMutation.isPending || removeFromWishlistMutation.isPending,
  };
}
