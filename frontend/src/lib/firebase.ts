import { initializeApp } from "firebase/app";
import { getMessaging, onMessage, getToken } from "firebase/messaging";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Firebase 초기화
const app = initializeApp(firebaseConfig);

// Firebase Cloud Messaging
let messaging: any = null;
if (typeof window !== "undefined") {
  try {
    messaging = getMessaging(app);
  } catch (e) {
    console.error("Firebase Messaging not available", e);
  }
}

// 푸시 알림 권한 요청 및 토큰 받기
export const requestNotificationPermission = async (): Promise<string | null> => {
  if (!messaging) return null;

  try {
    const permission = await Notification.requestPermission();

    if (permission === "granted") {
      const token = await getToken(messaging, {
        vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
      });
      return token;
    }
  } catch (error) {
    console.error("Failed to get notification permission", error);
  }

  return null;
};

// 포그라운드 메시지 수신
export const setupMessageListener = (callback: (data: any) => void) => {
  if (!messaging) return;

  onMessage(messaging, (payload) => {
    console.log("Message received:", payload);

    // 사용자 정의 콜백
    callback(payload);

    // 기본 알림 표시
    if (Notification.permission === "granted") {
      new Notification(payload.notification?.title || "알림", {
        body: payload.notification?.body,
        icon: payload.notification?.image,
      });
    }
  });
};

export const getMessagingInstance = () => messaging;
