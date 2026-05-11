import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dentistry Automation — Voice AI Platform",
  description: "AI-powered voice platform for dental clinics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}