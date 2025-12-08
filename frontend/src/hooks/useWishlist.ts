"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wishlistApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Wishlist, WishlistCreate, WishlistUpdate } from "@/types/wishlist";

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
    mutationFn: async (data: WishlistCreate) => {
      if (!isAuthenticated) throw new Error("User not authenticated");
      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.add(token, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      queryClient.invalidateQueries({ queryKey: ["accommodations"] });
    },
  });

  const updateWishlistMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: WishlistUpdate }) => {
      if (!isAuthenticated) throw new Error("User not authenticated");
      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.update(token, id, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const removeFromWishlistMutation = useMutation({
    mutationFn: async (accommodationId: string) => {
      if (!isAuthenticated) throw new Error("User not authenticated");

      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.removeByAccommodation(token, accommodationId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      queryClient.invalidateQueries({ queryKey: ["accommodations"] });
    },
  });

  const removeByIdMutation = useMutation({
    mutationFn: async (wishlistId: string) => {
      if (!isAuthenticated) throw new Error("User not authenticated");

      const token = localStorage.getItem("access_token") || "";
      const response = await wishlistApi.remove(token, wishlistId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      queryClient.invalidateQueries({ queryKey: ["accommodations"] });
    },
  });

  const isWishlisted = (accommodationId: string) => {
    return wishlist.some((w: Wishlist) => w.accommodation_id === accommodationId && w.is_active);
  };

  return {
    wishlist,
    addToWishlist: addToWishlistMutation.mutateAsync,
    updateWishlist: updateWishlistMutation.mutateAsync,
    removeFromWishlist: removeFromWishlistMutation.mutateAsync,
    removeById: removeByIdMutation.mutateAsync,
    isWishlisted,
    isLoading: addToWishlistMutation.isPending || removeFromWishlistMutation.isPending || removeByIdMutation.isPending || wishlistLoading,
  };
}
