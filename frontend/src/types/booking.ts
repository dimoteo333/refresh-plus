export type BookingStatus = "pending" | "won" | "lost" | "completed" | "cancelled";

export interface AccommodationBasic {
  id: string;
  name: string;
  region?: string;
  first_image?: string;
}

export interface Booking {
  id: string;
  user_id: string;
  accommodation_id?: string;
  accommodation_name?: string;
  accommodation?: AccommodationBasic;
  check_in?: string;
  check_out?: string;
  guests: number;
  status: BookingStatus;
  points_deducted: number;
  winning_score_at_time?: number;
  confirmation_number?: string;
  is_from_crawler?: boolean;
  created_at: string;
}

export interface BookingCreate {
  accommodation_id: string;
  check_in: string;
  check_out: string;
  guests: number;
}

export interface DirectReservationCreate {
  accommodation_id: string;
  check_in_date: string;
  phone_number: string;
}

export interface DirectReservationResponse {
  success: boolean;
  booking_id: string;
  message: string;
}
