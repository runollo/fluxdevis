import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  // Autorise l'acces au JS client (hydratation React) depuis le reseau local.
  // Sans ceci, Next.js dev bloque les scripts pour les origines non-localhost,
  // ce qui figeait toute interactivite quand on ouvrait l'app via 192.168.1.30.
  allowedDevOrigins: ["192.168.1.30"],
  experimental: {
    // Les pieces jointes (devis/contrat signe) transitent par une Server Action.
    // La limite par defaut des Server Actions est 1 Mo : on l'aligne sur la limite
    // backend (25 Mo) pour permettre l'upload de PDF/scans volumineux.
    serverActions: {
      bodySizeLimit: "25mb",
    },
  },
};

export default nextConfig;
