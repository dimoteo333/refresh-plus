"use client";

import { useEffect, useRef, useState } from "react";

interface NaverMapProps {
  address: string;
}

declare global {
  interface Window {
    naver?: any;
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID;

export default function NaverMap({ address }: NaverMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let scriptEl: HTMLScriptElement | null = null;

    if (!address) {
      setError("주소 정보가 없습니다.");
      return () => {
        isMounted = false;
      };
    }

    if (!CLIENT_ID) {
      setError("네이버 지도 Client ID가 설정되지 않았습니다.");
      return () => {
        isMounted = false;
      };
    }

    const loadMap = () => {
      if (!mapRef.current || !window.naver?.maps) return;

      const map = new window.naver.maps.Map(mapRef.current, {
        center: new window.naver.maps.LatLng(37.5665, 126.978),
        zoom: 14,
      });

      window.naver.maps.Service.geocode({ query: address }, (status: any, response: any) => {
        if (!isMounted) return;

        if (status !== window.naver.maps.Service.Status.OK) {
          setError("주소를 변환하지 못했습니다.");
          return;
        }

        const { addresses } = response.v2;
        if (!addresses || !addresses.length) {
          setError("주소 결과가 없습니다.");
          return;
        }

        const { y, x, roadAddress, jibunAddress } = addresses[0];
        const position = new window.naver.maps.LatLng(Number(y), Number(x));
        map.setCenter(position);

        new window.naver.maps.Marker({
          map,
          position,
          title: roadAddress || jibunAddress || address,
        });

        setIsReady(true);
      });
    };

    const handleScriptLoad = () => {
      if (window.naver && window.naver.maps) {
        loadMap();
      }
    };

    if (window.naver && window.naver.maps) {
      loadMap();
    } else {
      const existingScript = document.querySelector<HTMLScriptElement>(
        'script[data-naver-maps="true"]'
      );

      if (existingScript) {
        existingScript.addEventListener("load", handleScriptLoad);
      } else {
        scriptEl = document.createElement("script");
        scriptEl.src = `https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=${CLIENT_ID}&submodules=geocoder`;
        scriptEl.async = true;
        scriptEl.defer = true;
        scriptEl.dataset.naverMaps = "true";
        scriptEl.addEventListener("load", handleScriptLoad);
        scriptEl.onerror = () => setError("네이버 지도 스크립트를 불러오지 못했습니다.");
        document.head.appendChild(scriptEl);
      }
    }

    return () => {
      isMounted = false;

      if (scriptEl) {
        scriptEl.removeEventListener("load", handleScriptLoad);
      } else {
        const existingScript = document.querySelector<HTMLScriptElement>(
          'script[data-naver-maps="true"]'
        );
        existingScript?.removeEventListener("load", handleScriptLoad);
      }
    };
  }, [address]);

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
        {error}
      </div>
    );
  }

  return (
    <div className="relative h-64 w-full overflow-hidden rounded-xl border border-gray-100">
      <div ref={mapRef} className="h-full w-full" />
      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 text-sm text-gray-500">
          지도를 불러오는 중...
        </div>
      )}
    </div>
  );
}
