import type { Metadata } from "next";
import type { ReactNode } from "react";
import { env } from "@/lib/env";
import "./globals.css";

export const metadata: Metadata = {
  title: "PitchGuard",
  description: "AI-assisted preflight review for PR pitches",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: Readonly<RootLayoutProps>) {
  return (
    <html lang="en">
      <body data-api-base-url={env.apiBaseUrl}>{children}</body>
    </html>
  );
}
