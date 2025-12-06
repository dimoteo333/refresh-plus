"use client";

import { WeekdayAverage } from "@/types/accommodation";
import { useMemo } from "react";

interface WeekdayAverageChartProps {
  weekdayAverages: WeekdayAverage[];
  selectedWeekday?: number;
}

export default function WeekdayAverageChart({
  weekdayAverages,
  selectedWeekday,
}: WeekdayAverageChartProps) {
  // 전체 요일 데이터 (0-6) 생성, 없는 요일은 0으로 채움
  const fullWeekdayData = useMemo(() => {
    const weekdayNames = ["월", "화", "수", "목", "금", "토", "일"];
    const dataMap = new Map(
      weekdayAverages.map((avg) => [avg.weekday, avg])
    );

    return weekdayNames.map((name, index) => {
      const existingData = dataMap.get(index);
      return existingData || {
        weekday: index,
        weekday_name: name,
        avg_score: 0,
        count: 0,
      };
    });
  }, [weekdayAverages]);

  // 최대값 계산 (차트 높이 조정용)
  const maxScore = useMemo(() => {
    const scores = fullWeekdayData.map((d) => d.avg_score);
    return Math.max(...scores, 100); // 최소 100으로 설정
  }, [fullWeekdayData]);

  // 선택된 요일의 평균 점수 가져오기
  const selectedWeekdayData = useMemo(() => {
    if (selectedWeekday === undefined) return null;
    return fullWeekdayData.find((d) => d.weekday === selectedWeekday);
  }, [fullWeekdayData, selectedWeekday]);

  // 전체 평균 점수 계산
  const overallAverage = useMemo(() => {
    const validScores = weekdayAverages.filter((d) => d.count > 0);
    if (validScores.length === 0) return 0;

    const totalScore = validScores.reduce((sum, d) => sum + d.avg_score, 0);
    return totalScore / validScores.length;
  }, [weekdayAverages]);

  // 추천/비추천 문구 생성
  const getRecommendationText = () => {
    if (!selectedWeekdayData || selectedWeekdayData.count === 0) {
      return null;
    }

    const diff = selectedWeekdayData.avg_score - overallAverage;
    const weekdayName = selectedWeekdayData.weekday_name;

    if (diff < -5) {
      return {
        text: `좋아요! ${weekdayName}요일은 최근 3개월 평균 예약 점수(${overallAverage.toFixed(1)}점)보다 낮은 상태에요!`,
        type: "positive" as const,
      };
    } else if (diff > 5) {
      return {
        text: `${weekdayName}요일은 최근 3개월 평균 예약 점수(${overallAverage.toFixed(1)}점)보다 높은 편이에요.`,
        type: "negative" as const,
      };
    } else {
      return {
        text: `${weekdayName}요일은 최근 3개월 평균 예약 점수(${overallAverage.toFixed(1)}점)와 비슷한 수준이에요.`,
        type: "neutral" as const,
      };
    }
  };

  const recommendation = getRecommendationText();

  return (
    <div>
      {/* 바 차트 */}
      <div className="flex items-end justify-between gap-2 h-64 mb-4">
        {fullWeekdayData.map((data) => {
          const isSelected = selectedWeekday === data.weekday;
          const heightPercentage = (data.avg_score / maxScore) * 100;

          return (
            <div key={data.weekday} className="flex-1 flex flex-col items-center">
              {/* 점수 표시 */}
              <div className="mb-2 text-sm font-semibold text-gray-700 min-h-[20px]">
                {data.count > 0 ? `${data.avg_score.toFixed(1)}` : "-"}
              </div>

              {/* 바 */}
              <div className="w-full flex flex-col justify-end" style={{ height: "200px" }}>
                <div
                  className={`
                    w-full rounded-t transition-all
                    ${
                      isSelected
                        ? "bg-blue-600"
                        : data.count > 0
                        ? "bg-gray-300"
                        : "bg-gray-100"
                    }
                    ${isSelected ? "ring-2 ring-blue-400 ring-offset-2" : ""}
                  `}
                  style={{
                    height: data.count > 0 ? `${heightPercentage}%` : "10px",
                  }}
                />
              </div>

              {/* 요일 */}
              <div
                className={`
                  mt-2 text-sm font-medium
                  ${isSelected ? "text-blue-600 font-bold" : "text-gray-600"}
                `}
              >
                {data.weekday_name}
              </div>

              {/* 데이터 개수 */}
              <div className="text-xs text-gray-400 mt-1">
                {data.count > 0 ? `${data.count}회` : ""}
              </div>
            </div>
          );
        })}
      </div>

      {/* 추천/비추천 문구 */}
      {recommendation && (
        <div
          className={`
            p-4 rounded-lg border-l-4
            ${
              recommendation.type === "positive"
                ? "bg-green-50 border-green-500"
                : recommendation.type === "negative"
                ? "bg-yellow-50 border-yellow-500"
                : "bg-blue-50 border-blue-500"
            }
          `}
        >
          <p
            className={`
              text-sm font-medium
              ${
                recommendation.type === "positive"
                  ? "text-green-800"
                  : recommendation.type === "negative"
                  ? "text-yellow-800"
                  : "text-blue-800"
              }
            `}
          >
            {recommendation.text}
          </p>
        </div>
      )}

      {/* 범례 */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        막대 높이는 해당 요일의 평균 당첨 점수를 나타냅니다.
      </div>
    </div>
  );
}
