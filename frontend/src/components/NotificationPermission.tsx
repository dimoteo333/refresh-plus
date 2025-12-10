"use client";

export default function NotificationPermission() {
  const requestPermission = async () => {
    if (!("Notification" in window)) {
      alert("이 브라우저는 알림을 지원하지 않습니다.");
      return;
    }

    const permission = await Notification.requestPermission();

    if (permission === "granted") {
      console.log("✅ 알림 허용");
    } else {
      console.log("❌ 알림 거부");
    }
  };

  return <button onClick={requestPermission}>알림 허용</button>;
}
