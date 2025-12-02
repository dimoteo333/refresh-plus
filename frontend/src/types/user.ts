export interface User {
  id: string;
  email: string;
  name: string;
  current_points: number;
  max_points: number;
  total_bookings: number;
  successful_bookings: number;
  tier: "silver" | "gold" | "platinum";
  created_at: string;
}

export interface ScoreRecoverySchedule {
  current_score: number;
  max_score: number;
  recovery_per_period: number;
  recovery_period_hours: number;
  next_recovery: string;
}
