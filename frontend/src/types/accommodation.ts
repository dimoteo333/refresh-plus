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

export interface AccommodationFilters {
  region?: string;
  sort_by?: "popularity" | "price" | "rating";
  page?: number;
  limit?: number;
}
