export interface Notification {
  id: string;
  title: string;
  body: string;
  data?: any;
  timestamp: number;
}

export interface NotificationPreferences {
  push_enabled: boolean;
  push_on_booking_result: boolean;
  push_on_wishlist_bookable: boolean;
  push_on_score_recovery: boolean;
  kakao_enabled: boolean;
}
