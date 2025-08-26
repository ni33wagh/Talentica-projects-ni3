export interface TimePoint {
  t: string | number;
  count?: number;
  pct?: number;
  seconds?: number;
}

export interface SummaryResponse {
  activity: TimePoint[];
  successRate: TimePoint[];
  buildDurations: TimePoint[];
  status: { success: number; failure: number };
  tests: { pass: number; fail: number };
}

export interface DashboardData extends SummaryResponse {}

