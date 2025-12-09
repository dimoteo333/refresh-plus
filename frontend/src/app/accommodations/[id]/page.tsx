"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { accommodationApi } from "@/lib/api";
import { ArrowLeft, Building2, Globe, Heart, MapPin, Phone, Sparkles, Users } from "lucide-react";
import { AccommodationDetail, AvailableDate } from "@/types/accommodation";
import AccommodationImageCarousel from "@/components/accommodation/AccommodationImageCarousel";
import AvailableDatePicker from "@/components/accommodation/AvailableDatePicker";
import WeekdayAverageChart from "@/components/accommodation/WeekdayAverageChart";
import BottomNav from "@/components/layout/BottomNav";
import { Badge } from "@/components/ui/badge";
import { useWishlist } from "@/hooks/useWishlist";
import { useAuth } from "@/contexts/AuthContext";

export default function AccommodationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { isAuthenticated } = useAuth();
  const { addToWishlist, removeFromWishlist, isWishlisted: checkWishlisted, isLoading: wishlistLoading } = useWishlist();

  const [accommodation, setAccommodation] = useState<AccommodationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<AvailableDate | null>(null);
  const [aiSummary, setAiSummary] = useState<string[] | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const showPriorityNotice = !!(selectedDate && selectedDate.applicants >= 1 && selectedDate.score === 0);

  useEffect(() => {
    const fetchAccommodation = async () => {
      try {
        setLoading(true);
        const response = await accommodationApi.getDetailPage(id);
        setAccommodation(response.data);

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

  const handleToggleWishlist = async () => {
    if (!isAuthenticated) {
      alert("로그인이 필요합니다.");
      router.push("/login");
      return;
    }

    try {
      if (checkWishlisted(id)) {
        await removeFromWishlist(id);
      } else {
        await addToWishlist({
          accommodation_id: id,
          desired_date: selectedDate?.date,
          notify_enabled: true,
        });
      }
    } catch (err: any) {
      console.error("Failed to toggle wishlist:", err);
      alert(err.response?.data?.detail || "즐겨찾기 처리 중 오류가 발생했습니다.");
    }
  };

  useEffect(() => {
    const fetchAiSummary = async () => {
      if (!id) return;
      try {
        setAiLoading(true);
        const response = await accommodationApi.getAiSummary(id);
        setAiSummary(response.data || null);
      } catch (err) {
        console.warn("AI 요약 불러오기 실패:", err);
      } finally {
        setAiLoading(false);
      }
    };

    fetchAiSummary();
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
            onClick={handleToggleWishlist}
            aria-label="즐겨찾기"
            disabled={wishlistLoading}
            className={`rounded-full p-2 backdrop-blur transition ${
              checkWishlisted(id) ? "bg-red-500/80 text-white" : "bg-black/40 text-white hover:bg-black/60"
            } ${wishlistLoading ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <Heart className={`h-5 w-5 ${checkWishlisted(id) ? "fill-current" : ""}`} />
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

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* 헤더 섹션 */}
        <section className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex flex-col gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 leading-tight">{accommodation.name}</h1>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start">
              {accommodation.address && (
                <div className="flex min-w-[240px] flex-1 items-start gap-3">
                  <div className="rounded-2xl bg-sky-50 p-2 text-sky-600">
                    <MapPin className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-500">주소</p>
                    <p className="text-base text-gray-900 leading-relaxed">{accommodation.address}</p>
                  </div>
                </div>
              )}

              {accommodation.contact && (
                <div className="flex min-w-[200px] flex-1 items-start gap-3">
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
            </div>
          </div>
        </section>

        {/* AI 요약 */}
        {(aiLoading || (aiSummary && aiSummary.length > 0)) && (
          <section
            aria-live="polite"
            className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-5 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="rounded-full bg-indigo-100 p-2 text-indigo-700">
                <Sparkles className="h-4 w-4" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">
                AI 3줄 요약 {aiLoading && <span className="text-xs text-indigo-500">(로딩중)</span>}
              </h2>
            </div>
            {aiSummary && aiSummary.length > 0 ? (
              <ul className="space-y-2 text-sm text-gray-800 leading-relaxed">
                {aiSummary.map((line, idx) => (
                  <li key={`ai-summary-${idx}`} className="flex gap-2">
                    <span className="text-indigo-500">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-600">요약을 준비하고 있습니다...</p>
            )}
          </section>
        )}

        {/* 숙소 정보 아이콘 그리드 */}
        <section className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-gray-900">숙소 정보</h2>
              <p className="text-sm text-gray-500">타입과 수용 인원을 한눈에 확인하세요.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-6 sm:grid-cols-2">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-slate-900/90 p-3 text-white shadow-sm">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600">숙소 타입</p>
                <p className="text-lg font-bold text-gray-900">
                  {accommodation.accommodation_type || "정보 없음"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-slate-900/90 p-3 text-white shadow-sm">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600">수용 인원</p>
                <p className="text-lg font-bold text-gray-900">
                  {accommodation.capacity ? `${accommodation.capacity}명` : "정보 없음"}
                </p>
              </div>
            </div>
          </div>
        </section>

        {accommodation.summary && accommodation.summary.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">숙소 특징</h2>
            <div className="flex flex-wrap gap-2">
              {accommodation.summary.map((item, index) => (
                <Badge key={`${accommodation.id}-feature-${index}`} className="bg-sky-100 text-sky-800 hover:bg-sky-100">
                  {item}
                </Badge>
              ))}
            </div>
          </section>
        )}

        {/* 예약 가능 날짜 */}
        {accommodation.available_dates && accommodation.available_dates.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">예약 가능 날짜</h2>
            <AvailableDatePicker
              dates={accommodation.available_dates}
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
            />
          </section>
        )}

        {/* 요일별 평균 점수 바 차트 */}
        {accommodation.weekday_averages && accommodation.weekday_averages.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">요일별 평균 당첨 점수</h2>
            <p className="text-sm text-gray-600 mb-4">최근 3개월간 마감된 예약의 요일별 평균 당첨 점수입니다.</p>
            <WeekdayAverageChart
              weekdayAverages={accommodation.weekday_averages}
              selectedWeekday={selectedDate?.weekday}
              selectedDate={selectedDate}
            />
          </section>
        )}
      </div>

      {showPriorityNotice && (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
          <div className="rounded-xl bg-amber-50 border border-amber-100 px-4 py-3 text-sm text-amber-900 leading-relaxed">
            금융소비자보호 내부통제 업무지침 제 7조 소비자보호그룹 직원에 대한 우대 4항 2호에 따라 해당 우대자가 신청한 경우
            '0점'으로 표기되며 우선 배정 됩니다.
          </div>
        </div>
      )}

      {accommodation.website && (
        <footer className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
          <a
            href={accommodation.website}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition"
          >
            <Globe className="h-4 w-4" />
            공식 웹사이트 바로가기
          </a>
        </footer>
      )}

      <BottomNav activeHref="/search" />
    </div>
  );
}
