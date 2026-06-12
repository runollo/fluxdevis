"use client";

// Message de feedback ephemere (succes / erreur / info). Remplace les bandeaux
// statiques pilotes par query param : s'efface automatiquement apres quelques
// secondes, peut etre ferme a la main, et RETIRE le(s) param(s) de l'URL pour ne
// pas reapparaitre au rafraichissement. Le message est calcule cote serveur par
// la page (selon le param) et passe en prop ; ce composant ne gere que l'UX.

import { useEffect, useState } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";

type Props = {
  message: string;
  type?: "success" | "error" | "info";
  /** Nom du/des query param(s) de feedback a retirer de l'URL a la fermeture. */
  param: string | string[];
  /** Duree avant disparition automatique (ms). 0 = pas d'auto-fermeture. */
  duree?: number;
};

const STYLES: Record<string, string> = {
  success: "border-green-200 bg-green-50 text-green-800",
  error: "border-red-200 bg-red-50 text-red-700",
  info: "border-blue-200 bg-blue-50 text-blue-800",
};

export default function Flash({ message, type = "success", param, duree = 5000 }: Props) {
  const [visible, setVisible] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function close() {
    setVisible(false);
    const params = new URLSearchParams(Array.from(searchParams.entries()));
    (Array.isArray(param) ? param : [param]).forEach(p => params.delete(p));
    const qs = params.toString();
    router.replace(pathname + (qs ? `?${qs}` : ""), { scroll: false });
  }

  useEffect(() => {
    if (!duree) return;
    const t = setTimeout(close, duree);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!visible) return null;
  return (
    <div
      role="status"
      className={`mb-4 flex items-start justify-between gap-3 rounded border px-4 py-3 text-sm ${STYLES[type]}`}
    >
      <span>{message}</span>
      <button type="button" onClick={close} aria-label="Fermer le message"
        className="shrink-0 text-lg leading-none opacity-60 hover:opacity-100">
        &times;
      </button>
    </div>
  );
}
