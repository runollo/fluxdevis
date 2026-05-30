import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  // Autorise l'acces au JS client (hydratation React) depuis le reseau local.
  // Sans ceci, Next.js dev bloque les scripts pour les origines non-localhost,
  // ce qui figeait toute interactivite quand on ouvrait l'app via 192.168.1.30.
  allowedDevOrigins: ["192.168.1.30"],
};

export default nextConfig;
