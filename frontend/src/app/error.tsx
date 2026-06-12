"use client";

// Page d'erreur (error boundary Next.js). Capture les crashs de rendu d'un
// segment et propose de reessayer, au lieu d'un ecran technique brut.
// NB Next 16 : la fonction de reprise est `unstable_retry` (pas `reset`).

export default function Error({ unstable_retry }: { error: Error & { digest?: string }; unstable_retry: () => void }) {
  return (
    <div className="max-w-lg mx-auto mt-8 rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <h1 className="text-lg font-semibold text-red-800 mb-2">Une erreur est survenue</h1>
      <p className="text-sm text-red-700 mb-4">
        La page n&apos;a pas pu s&apos;afficher correctement. Le service est peut-etre
        momentanement indisponible.
      </p>
      <div className="flex justify-center gap-2">
        <button type="button" onClick={() => unstable_retry()}
          className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
          Reessayer
        </button>
        <a href="/" className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">
          Retour a l&apos;accueil
        </a>
      </div>
    </div>
  );
}
