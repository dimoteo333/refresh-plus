"use client";

import { useBookings } from "@/hooks/useBookings";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

export default function BookingsPage() {
  const { data: bookings, isLoading } = useBookings();

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "won":
        return "success";
      case "lost":
        return "danger";
      case "pending":
        return "warning";
      case "completed":
        return "default";
      default:
        return "secondary";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "won":
        return "당첨";
      case "lost":
        return "낙첨";
      case "pending":
        return "대기 중";
      case "completed":
        return "완료";
      case "cancelled":
        return "취소됨";
      default:
        return status;
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">예약 현황</h1>
        <p className="text-gray-600">내 예약 이력을 확인하세요</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      ) : bookings && bookings.length > 0 ? (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <Card key={booking.id}>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg">예약 #{booking.id}</CardTitle>
                  <Badge variant={getStatusBadgeVariant(booking.status)}>
                    {getStatusText(booking.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">체크인</p>
                    <p className="font-semibold">{formatDate(booking.check_in)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">체크아웃</p>
                    <p className="font-semibold">{formatDate(booking.check_out)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">인원</p>
                    <p className="font-semibold">{booking.guests}명</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">차감 포인트</p>
                    <p className="font-semibold">{booking.points_deducted}점</p>
                  </div>
                  {booking.confirmation_number && (
                    <div className="col-span-2">
                      <p className="text-sm text-gray-600">확인 번호</p>
                      <p className="font-mono font-semibold">{booking.confirmation_number}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600">아직 예약 내역이 없습니다.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
