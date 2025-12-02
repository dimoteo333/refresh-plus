export type BookingStatus = "pending" | "won" | "lost" | "completed" | "cancelled";

export interface Booking {
  id: string;
  user_id: string;
  accommodation_id: string;
  check_in: string;
  check_out: string;
  guests: number;
  status: BookingStatus;
  points_deducted: number;
  winning_score_at_time?: number;
  confirmation_number?: string;
  created_at: string;
}

export interface BookingCreate {
  accommodation_id: string;
  check_in: string;
  check_out: string;
  guests: number;
}
