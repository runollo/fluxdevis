import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FluxDevis",
  description: "Gestion devis et factures FluXweb",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${geist.variable} h-full`} style={{ colorScheme: "light" }}>
      <body className="h-full bg-gray-50 text-gray-900 antialiased">
        <Sidebar />
        {/* pt-14 sur mobile pour compenser le header fixe, lg:pl-56 pour la sidebar desktop */}
        <main className="min-h-full pt-14 lg:pt-0 lg:pl-56">
          <div className="p-4 sm:p-6">{children}</div>
        </main>
      </body>
    </html>
  );
}
