import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 토큰 갱신 중복 방지 플래그
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// 토큰 갱신 함수
const refreshAccessToken = async (): Promise<string | null> => {
  try {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
      refresh_token: refreshToken,
    });

    const { access_token } = response.data;
    localStorage.setItem("access_token", access_token);

    return access_token;
  } catch (error) {
    // 리프레시 토큰도 만료된 경우
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    return null;
  }
};

// Axios 인스턴스 생성
const createApiClient = (userId?: string): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
    withCredentials: true, // 쿠키 포함
  });

  // 요청 인터셉터 (JWT 토큰 또는 사용자 ID 추가)
  client.interceptors.request.use(
    (config) => {
      // 1. JWT 토큰 우선 (새 시스템)
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("access_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }

      // 2. X-User-ID 헤더 (레거시 시스템 - 하위 호환성)
      if (userId) {
        config.headers["X-User-ID"] = userId;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // 응답 인터셉터 (에러 처리 및 토큰 갱신)
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // 401 에러 처리 (인증 실패)
      if (error.response?.status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          // 이미 토큰 갱신 중이면 큐에 추가
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return client(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const newToken = await refreshAccessToken();

          if (newToken) {
            // 토큰 갱신 성공
            processQueue(null, newToken);

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }

            return client(originalRequest);
          } else {
            // 토큰 갱신 실패 - 로그인 페이지로
            processQueue(new Error("Token refresh failed"), null);

            if (typeof window !== "undefined") {
              const currentPath = window.location.pathname;
              window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
            }

            return Promise.reject(error);
          }
        } catch (refreshError) {
          processQueue(refreshError, null);

          if (typeof window !== "undefined") {
            const currentPath = window.location.pathname;
            window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
          }

          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
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

  getRandom: (limit?: number) =>
    createApiClient().get("/api/accommodations/random", {
      params: { limit: limit || 5 },
    }),

  getPopular: (limit?: number) =>
    createApiClient().get("/api/accommodations/popular", {
      params: { limit: limit || 5 },
    }),

  search: (
    token: string,
    params?: {
      keyword?: string;
      region?: string;
      sort_by?: string;
      sort_order?: "asc" | "desc";
      available_only?: boolean;
      date?: string;
      limit?: number;
    }
  ) =>
    createApiClient(token).get("/api/accommodations/search", {
      params: {
        keyword: params?.keyword,
        region: params?.region,
        sort_by: params?.sort_by,
        sort_order: params?.sort_order,
        available_only: params?.available_only,
        date: params?.date,
        limit: params?.limit || 50,
      },
    }),

  getDetailPage: (id: string) =>
    createApiClient().get(`/api/accommodations/detail/${id}`),

  getRegions: () => createApiClient().get("/api/accommodations/regions"),

  getAiSummary: (id: string) =>
    createApiClient().get(`/api/accommodations/detail/${id}/ai-summary`),

  getDates: (id: string, params?: { start_date?: string; end_date?: string }) =>
    createApiClient().get(`/api/accommodations/${id}/dates`, { params }),
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

  add: (token: string, data: {
    accommodation_id: string;
    desired_date?: string;
    notify_enabled?: boolean;
    notification_type?: string;
    fcm_token?: string;
  }) =>
    createApiClient(token).post("/api/wishlist", data),

  update: (token: string, id: string, data: {
    desired_date?: string;
    notify_enabled?: boolean;
    notification_type?: string;
    fcm_token?: string;
  }) =>
    createApiClient(token).patch(`/api/wishlist/${id}`, data),

  remove: (token: string, id: string) =>
    createApiClient(token).delete(`/api/wishlist/${id}`),

  removeByAccommodation: (token: string, accommodationId: string) =>
    createApiClient(token).delete(`/api/wishlist/accommodation/${accommodationId}`),
};

// 알림 API
export const notificationApi = {
  getPreferences: (token: string) =>
    createApiClient(token).get("/api/notifications/preferences"),

  updatePreferences: (token: string, data: any) =>
    createApiClient(token).put("/api/notifications/preferences", data),
};

// 챗봇 API
export const chatbotApi = {
  chat: (token: string, query: string) =>
    createApiClient(token).post("/api/chatbot/chat", { query }),

  getStats: (token: string) =>
    createApiClient(token).get("/api/chatbot/stats"),
};
