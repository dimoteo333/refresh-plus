"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { accommodationApi } from "@/lib/api";
import { ArrowLeft, Globe, Heart, MapPin, Phone } from "lucide-react";
import { AccommodationDetail, AvailableDate } from "@/types/accommodation";
import AccommodationImageCarousel from "@/components/accommodation/AccommodationImageCarousel";
import AvailableDatePicker from "@/components/accommodation/AvailableDatePicker";
import WeekdayAverageChart from "@/components/accommodation/WeekdayAverageChart";
import BottomNav from "@/components/layout/BottomNav";
import { Badge } from "@/components/ui/badge";
import NaverMap from "@/components/accommodation/NaverMap";

export default function AccommodationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [accommodation, setAccommodation] = useState<AccommodationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<AvailableDate | null>(null);
  const [isWishlisted, setIsWishlisted] = useState(false);

  useEffect(() => {
    const fetchAccommodation = async () => {
      try {
        setLoading(true);
        const response = await accommodationApi.getDetailPage(id);
        setAccommodation(response.data);
        if (typeof response.data.is_wishlisted === "boolean") {
          setIsWishlisted(response.data.is_wishlisted);
        }

        // 첫 번째 예약 가능 날짜를 자동으로 선택
        if (response.data.available_dates && response.data.available_dates.length > 0) {
          setSelectedDate(response.data.available_dates[0]);
        }
      } catch (err: any) {
        console.error("Failed to fetch accommodation detail:", err);
        setError(err.response?.data?.detail || "숙소 정보를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchAccommodation();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">숙소 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !accommodation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error || "숙소를 찾을 수 없습니다."}</p>
          <button
            onClick={() => router.push("/")}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      <div className="relative">
        <AccommodationImageCarousel images={accommodation.images} />
        <div className="absolute inset-x-0 top-0 flex items-center justify-between px-4 py-4">
          <button
            type="button"
            onClick={() => router.back()}
            aria-label="뒤로 가기"
            className="rounded-full bg-black/40 p-2 text-white backdrop-blur hover:bg-black/60"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <button
            type="button"
            onClick={() => setIsWishlisted((prev) => !prev)}
            aria-label="즐겨찾기"
            className={`rounded-full p-2 backdrop-blur transition ${
              isWishlisted ? "bg-red-500/80 text-white" : "bg-black/40 text-white hover:bg-black/60"
            }`}
          >
            <Heart className={`h-5 w-5 ${isWishlisted ? "fill-current" : ""}`} />
          </button>
        </div>
        {accommodation.region && (
          <div className="absolute left-4 bottom-4">
            <Badge className="flex items-center gap-1 bg-black/60 px-3 py-1.5 text-white hover:bg-black/70">
              <MapPin className="h-4 w-4" />
              {accommodation.region}
            </Badge>
          </div>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 기본 정보 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">{accommodation.name}</h1>

          <div className="space-y-5">
            {accommodation.address && (
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-sky-50 p-2 text-sky-600">
                  <MapPin className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-500">주소</p>
                  <p className="text-base text-gray-900">{accommodation.address}</p>
                </div>
              </div>
            )}

            {accommodation.contact && (
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-sky-50 p-2 text-sky-600">
                  <Phone className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-500">연락처</p>
                  <a
                    href={`tel:${accommodation.contact}`}
                    className="text-base font-medium text-gray-900 hover:text-blue-600"
                  >
                    {accommodation.contact}
                  </a>
                </div>
              </div>
            )}

            {accommodation.website && (
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-sky-50 p-2 text-sky-600">
                  <Globe className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-500">웹사이트</p>
                  <a
                    href={accommodation.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-base font-medium text-blue-600 hover:underline"
                  >
                    {accommodation.website}
                  </a>
                </div>
              </div>
            )}
          </div>

          {accommodation.address && (
            <div className="mt-6">
              <NaverMap address={accommodation.address} />
            </div>
          )}

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
              <p className="text-sm font-semibold text-gray-500">숙소 타입</p>
              <p className="mt-2 text-lg font-bold text-gray-900">
                {accommodation.accommodation_type || "정보 없음"}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
              <p className="text-sm font-semibold text-gray-500">수용 인원</p>
              <p className="mt-2 text-lg font-bold text-gray-900">
                {accommodation.capacity ? `${accommodation.capacity}명` : "정보 없음"}
              </p>
            </div>
          </div>

          {accommodation.summary && accommodation.summary.length > 0 && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">숙소 특징</h2>
              <div className="flex flex-wrap gap-2">
                {accommodation.summary.map((item, index) => (
                  <Badge
                    key={`${accommodation.id}-feature-${index}`}
                    className="bg-sky-100 text-sky-800 hover:bg-sky-100"
                  >
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 예약 가능 날짜 */}
        {accommodation.available_dates && accommodation.available_dates.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">예약 가능 날짜</h2>
            <AvailableDatePicker
              dates={accommodation.available_dates}
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
            />
          </div>
        )}

        {/* 요일별 평균 점수 바 차트 */}
        {accommodation.weekday_averages && accommodation.weekday_averages.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">요일별 평균 당첨 점수</h2>
            <p className="text-sm text-gray-600 mb-4">
              최근 3개월간 마감된 예약의 요일별 평균 당첨 점수입니다.
            </p>
            <WeekdayAverageChart
              weekdayAverages={accommodation.weekday_averages}
              selectedWeekday={selectedDate?.weekday}
            />
          </div>
        )}
      </div>

      <BottomNav activeHref="/search" />
    </div>
  );
}
