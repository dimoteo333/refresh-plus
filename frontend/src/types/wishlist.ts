export interface Wishlist {
  id: string;
  user_id: string;
  accommodation_id: string;
  desired_date?: string; // ISO date string (YYYY-MM-DD)
  is_active: boolean;
  notify_enabled: boolean;
  notification_type?: "ios_webview" | "android_fcm" | "kakao";
  fcm_token?: string;
  created_at: string;
  updated_at: string;
}

export interface WishlistCreate {
  accommodation_id: string;
  desired_date?: string; // ISO date string (YYYY-MM-DD)
  notify_enabled?: boolean;
  notification_type?: "ios_webview" | "android_fcm" | "kakao";
  fcm_token?: string;
}

export interface WishlistUpdate {
  desired_date?: string;
  notify_enabled?: boolean;
  notification_type?: "ios_webview" | "android_fcm" | "kakao";
  fcm_token?: string;
}

export interface WishlistWithAccommodation extends Wishlist {
  accommodation?: {
    id: string;
    name: string;
    region: string;
    first_image?: string;
    avg_score?: number;
  };
}
