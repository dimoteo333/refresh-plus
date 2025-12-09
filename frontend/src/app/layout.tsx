import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Refresh+",
  description: "신한은행 임직원 연성소 예약 앱",
  icons: {
    icon: "/icons/icon-128x128.png",
    apple: "/icons/apple-touch-icon.png"
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Refresh+"
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
