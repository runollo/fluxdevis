import { serverFetch } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface DevisRecent {
  id: number; reference: string; client_raison_sociale: string;
  statut: string; total_ttc: string; date_emission: string;
}
interface FactureRecente {
  id: number; numero: string; objet: string;
  statut: string; total_ttc: string; date_emission: string;
}
interface Stats {
  offres_actives: number; options_actives: number; clients: number;
  devis_total: number; devis_acceptes: number;
  factures_total: number; factures_impayees: number;
  montant_devis_ttc: string; montant_factures_ttc: string;
  derniers_devis: DevisRecent[]; dernieres_factures: FactureRecente[];
}

const STATUT_DEVIS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-700", envoye: "bg-blue-100 text-blue-700",
  accepte: "bg-green-100 text-green-700", refuse: "bg-red-100 text-red-700",
  expire: "bg-orange-100 text-orange-700",
};
const STATUT_FACTURE: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-700", emise: "bg-blue-100 text-blue-700",
  payee: "bg-green-100 text-green-700", en_retard: "bg-red-100 text-red-700",
  annulee: "bg-orange-100 text-orange-700",
};

export default async function Dashboard() {
  let s: Stats | null = null;
  try { s = await serverFetch<Stats>("/dashboard/"); } catch {}

  const cards = [
    { label: "Offres actives", value: s?.offres_actives ?? "-", href: "/catalogue", bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-900" },
    { label: "Options catalogue", value: s?.options_actives ?? "-", href: "/catalogue?tab=options", bg: "bg-green-50", border: "border-green-300", text: "text-green-900" },
    { label: "Clients", value: s?.clients ?? "-", href: "/clients", bg: "bg-orange-50", border: "border-orange-300", text: "text-orange-900" },
    { label: "Devis", value: s?.devis_total ?? "-", href: "/devis", bg: "bg-indigo-50", border: "border-indigo-300", text: "text-indigo-900" },
    { label: "Factures", value: s?.factures_total ?? "-", href: "/factures", bg: "bg-purple-50", border: "border-purple-300", text: "text-purple-900" },
    { label: "Montant devis TTC", value: s ? eur(s.montant_devis_ttc) : "-", href: "/devis", bg: "bg-slate-50", border: "border-slate-300", text: "text-slate-900" },
  ];

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Dashboard</h1>

      {!s && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Impossible de charger les statistiques (backend injoignable).
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        {cards.map((card) => (
          <Link key={card.label} href={card.href}
            className={`rounded-lg border p-4 sm:p-5 ${card.bg} ${card.border} transition-transform hover:scale-[1.02]`}>
            <p className="text-xs sm:text-sm text-gray-700 font-medium">{card.label}</p>
            <p className={`text-2xl sm:text-3xl font-bold mt-1 ${card.text}`}>{card.value}</p>
          </Link>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Derniers devis */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">Derniers devis</h2>
            <Link href="/devis" className="text-xs text-blue-600 hover:underline">Tout voir</Link>
          </div>
          {!s || s.derniers_devis.length === 0 ? (
            <p className="text-sm text-gray-400">Aucun devis</p>
          ) : (
            <ul className="divide-y">
              {s.derniers_devis.map(d => (
                <li key={d.id} className="py-2 flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-mono text-xs sm:text-sm font-medium truncate">{d.reference}</p>
                    <p className="text-xs text-gray-500 truncate">{d.client_raison_sociale}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-medium">{eur(d.total_ttc)}</p>
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${STATUT_DEVIS[d.statut] || "bg-gray-100 text-gray-700"}`}>
                      {d.statut}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Dernieres factures */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 sm:p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">Dernieres factures</h2>
            <Link href="/factures" className="text-xs text-blue-600 hover:underline">Tout voir</Link>
          </div>
          {!s || s.dernieres_factures.length === 0 ? (
            <p className="text-sm text-gray-400">Aucune facture</p>
          ) : (
            <ul className="divide-y">
              {s.dernieres_factures.map(f => (
                <li key={f.id} className="py-2 flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-mono text-xs sm:text-sm font-medium truncate">{f.numero}</p>
                    <p className="text-xs text-gray-500 truncate">{f.objet}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-medium">{eur(f.total_ttc)}</p>
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${STATUT_FACTURE[f.statut] || "bg-gray-100 text-gray-700"}`}>
                      {f.statut}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
