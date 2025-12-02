import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
      <div className="max-w-4xl px-8 text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6">
          Refresh Plus
        </h1>
        <p className="text-2xl text-gray-700 mb-12">
          임직원을 위한 스마트한 호텔/리조트 예약 시스템
        </p>

        <div className="flex gap-4 justify-center">
          <Link
            href="/sign-in"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            로그인
          </Link>
          <Link
            href="/sign-up"
            className="px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition"
          >
            회원가입
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2">포인트 기반 예약</h3>
            <p className="text-gray-600">
              공정한 티켓팅 시스템으로 예약 기회를 균등하게
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2">실시간 알림</h3>
            <p className="text-gray-600">
              예약 결과와 점수 회복을 즉시 알림
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-bold mb-2">AI 챗봇</h3>
            <p className="text-gray-600">
              궁금한 점을 즉시 해결하는 스마트 도우미
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
