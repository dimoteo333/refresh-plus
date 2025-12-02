import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Axios 인스턴스 생성
const createApiClient = (token?: string): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // 요청 인터셉터 (토큰 추가)
  client.interceptors.request.use(
    (config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 응답 인터셉터 (에러 처리)
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        // 인증 오류 - 로그인 페이지로 이동
        if (typeof window !== 'undefined') {
          window.location.href = "/sign-in";
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

// 숙소 관련 API
export const accommodationApi = {
  getAll: (token: string, params?: any) =>
    createApiClient(token).get("/api/accommodations", { params }),

  getDetail: (token: string, id: string) =>
    createApiClient(token).get(`/api/accommodations/${id}`),
};

// 예약 관련 API
export const bookingApi = {
  create: (token: string, data: any) =>
    createApiClient(token).post("/api/bookings", data),

  getHistory: (token: string, params?: any) =>
    createApiClient(token).get("/api/bookings", { params }),

  getDetail: (token: string, id: string) =>
    createApiClient(token).get(`/api/bookings/${id}`),
};

// 사용자 API
export const userApi = {
  getMe: (token: string) =>
    createApiClient(token).get("/api/users/me"),

  getScoreRecovery: (token: string) =>
    createApiClient(token).get("/api/users/me/score-recovery-schedule"),
};

// 찜하기 API
export const wishlistApi = {
  getAll: (token: string) =>
    createApiClient(token).get("/api/wishlist"),

  add: (token: string, accommodationId: string) =>
    createApiClient(token).post("/api/wishlist", {
      accommodation_id: accommodationId,
      notify_when_bookable: true,
    }),

  remove: (token: string, id: string) =>
    createApiClient(token).delete(`/api/wishlist/${id}`),
};

// 알림 API
export const notificationApi = {
  getPreferences: (token: string) =>
    createApiClient(token).get("/api/notifications/preferences"),

  updatePreferences: (token: string, data: any) =>
    createApiClient(token).put("/api/notifications/preferences", data),
};
