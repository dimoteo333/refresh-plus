export interface Accommodation {
  id: string;
  name: string;
  description?: string;
  region: string;
  price: number;
  capacity?: number;
  images?: string[];
  amenities?: string[];
  rating: number;
  can_book_with_current_score: boolean;
  avg_winning_score_4weeks: number;
  availability: number;
  my_score?: number;
  can_book?: boolean;
  past_bookings?: number;
  win_rate?: number;
}

export interface RandomAccommodation {
  id: string;
  name: string;
  region: string;
  first_image?: string;
}

export interface PopularAccommodation {
  id: string;
  name: string;
  region: string;
  first_image?: string;
  date: string;
  applicants: number;
  score: number;
}

export interface SearchAccommodation {
  id: string;
  name: string;
  region: string;
  accommodation_type?: string;
  first_image?: string;
  avg_score?: number;
  is_wishlisted: boolean;
  notify_enabled: boolean;
}

export interface AccommodationFilters {
  region?: string;
  sort_by?: "popularity" | "price" | "rating";
  page?: number;
  limit?: number;
}

export interface AvailableDate {
  date: string;
  score: number;
  applicants: number;
  status: string;
  weekday: number;
}

export interface WeekdayAverage {
  weekday: number;
  weekday_name: string;
  avg_score: number;
  count: number;
}

export interface AccommodationDetail {
  id: string;
  name: string;
  region: string;
  address?: string;
  contact?: string;
  website?: string;
  accommodation_type?: string;
  capacity: number;
  images: string[];
  available_dates: AvailableDate[];
  weekday_averages: WeekdayAverage[];
  is_wishlisted?: boolean;
}
