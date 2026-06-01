import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Act — Assistant documentaire | Inseil IA",
  description:
    "Explorez le Règlement européen 2024/1689 sur l'IA. Réponses sourcées, articles et pages cités, refus explicite quand le règlement ne couvre pas votre cas. Réalisé par Inseil IA.",
  openGraph: {
    title: "AI Act — Assistant documentaire | Inseil IA",
    description:
      "Posez vos questions sur le Règlement européen 2024/1689. Réponses sourcées avec citations et refus explicites. Cadrage documentaire pour DAF, DSI, RH et Conformité.",
    type: "website",
    locale: "fr_FR",
    siteName: "Inseil IA",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Act — Assistant documentaire | Inseil IA",
    description:
      "Explorez le Règlement européen 2024/1689 avec des réponses sourcées et l'honnêteté de dire « je ne sais pas ».",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
