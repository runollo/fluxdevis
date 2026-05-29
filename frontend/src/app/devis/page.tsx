import { serverFetch } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface Devis {
  id: number; reference: string; statut: string; date_emission: string;
  client_raison_sociale: string; offre_nom: string; mode_reglement: string; total_ttc: string;
}

const STATUT_COLORS: Record<string, string> = {
  BROUILLON: "bg-gray-100 text-gray-700",
  ENVOYE: "bg-blue-100 text-blue-700",
  ACCEPTE: "bg-green-100 text-green-700",
  REFUSE: "bg-red-100 text-red-700",
  EXPIRE: "bg-orange-100 text-orange-700",
};

export default async function DevisPage() {
  let devisList: Devis[] = [];
  try { devisList = await serverFetch<Devis[]>("/devis/"); } catch {}

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Devis ({devisList.length})</h1>
        <Link href="/simulateur" className="px-4 py-2.5 bg-[#1A355E] text-white rounded text-sm font-medium text-center">
          + Nouveau devis
        </Link>
      </div>

      {devisList.length === 0 ? (
        <div className="bg-white border rounded-lg p-8 text-center">
          <p className="text-gray-400 mb-4">Aucun devis enregistre</p>
          <Link href="/simulateur" className="text-blue-600 hover:underline text-sm">Creer un devis depuis le simulateur</Link>
        </div>
      ) : (
        <>
          {/* Mobile */}
          <div className="sm:hidden space-y-3">
            {devisList.map(d => (
              <div key={d.id} className="bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-mono text-sm font-medium">{d.reference}</p>
                    <p className="text-sm text-gray-600">{d.client_raison_sociale}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[d.statut] || "bg-gray-100 text-gray-700"}`}>
                    {d.statut}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{d.offre_nom}</span>
                  <span className="font-semibold">{eur(d.total_ttc)}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{d.date_emission} - {d.mode_reglement}</p>
              </div>
            ))}
          </div>
          {/* Desktop */}
          <div className="hidden sm:block bg-white rounded-lg border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Reference</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Client</th>
                  <th className="px-4 py-3 font-medium">Offre</th>
                  <th className="px-4 py-3 font-medium">Mode</th>
                  <th className="px-4 py-3 font-medium text-right">Total TTC</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {devisList.map(d => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono font-medium">{d.reference}</td>
                    <td className="px-4 py-3 text-gray-500">{d.date_emission}</td>
                    <td className="px-4 py-3">{d.client_raison_sociale}</td>
                    <td className="px-4 py-3 text-gray-500">{d.offre_nom}</td>
                    <td className="px-4 py-3">{d.mode_reglement}</td>
                    <td className="px-4 py-3 text-right font-medium">{eur(d.total_ttc)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[d.statut] || "bg-gray-100 text-gray-700"}`}>
                        {d.statut}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
