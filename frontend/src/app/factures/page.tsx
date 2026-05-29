import { serverFetch } from "@/lib/api";
import { archiverFacture, annulerFacture, restaurerFacture } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface Facture {
  id: number; numero: string; type: string; statut: string;
  date_emission: string; date_echeance: string; objet: string; total_ttc: string;
}

const STATUT_COLORS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-700",
  emise: "bg-blue-100 text-blue-700",
  payee: "bg-green-100 text-green-700",
  en_retard: "bg-red-100 text-red-700",
  annulee: "bg-orange-100 text-orange-700",
};

const TYPE_LABELS: Record<string, string> = {
  acompte: "Acompte",
  solde: "Solde",
  maintenance: "Maintenance",
};

// Boutons d'action selon le statut, conformes au droit :
// - brouillon  -> suppression (corbeille) possible
// - emise/payee/en_retard -> annulation par avoir uniquement
// - annulee    -> aucune action (document conserve)
function ActionsFacture({ f }: { f: Facture }) {
  if (f.statut === "brouillon") {
    return (
      <form action={archiverFacture} className="inline">
        <input type="hidden" name="facture_id" value={f.id} />
        <input type="hidden" name="retour" value="/factures" />
        <button type="submit" className="ml-3 text-red-600 hover:underline font-medium">Supprimer</button>
      </form>
    );
  }
  if (f.statut === "emise" || f.statut === "payee" || f.statut === "en_retard") {
    return (
      <form action={annulerFacture} className="inline">
        <input type="hidden" name="facture_id" value={f.id} />
        <input type="hidden" name="retour" value="/factures" />
        <button type="submit" className="ml-3 text-orange-600 hover:underline font-medium">Annuler (avoir)</button>
      </form>
    );
  }
  return null;
}

export default async function FacturesPage(
  { searchParams }: { searchParams: Promise<{ archives?: string; suppr_msg?: string }> }
) {
  const params = await searchParams;
  const corbeille = params.archives === "1";

  let factures: Facture[] = [];
  try {
    factures = await serverFetch<Facture[]>(`/factures/${corbeille ? "?archives=true" : ""}`);
  } catch {}

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
          {corbeille ? "Corbeille — factures" : "Factures"} ({factures.length})
        </h1>
        <div className="flex gap-2">
          {corbeille ? (
            <Link href="/factures" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
              Retour aux factures
            </Link>
          ) : (
            <>
              <Link href="/factures?archives=1" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
                Corbeille
              </Link>
              <Link href="/devis" className="px-4 py-2.5 bg-[#1A355E] text-white rounded text-sm font-medium text-center">
                Generer depuis un devis
              </Link>
            </>
          )}
        </div>
      </div>

      {params.suppr_msg && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
          {params.suppr_msg}
        </div>
      )}

      {factures.length === 0 ? (
        <div className="bg-white border rounded-lg p-8 text-center">
          <p className="text-gray-400 mb-4">{corbeille ? "Corbeille vide" : "Aucune facture"}</p>
          {!corbeille && (
            <Link href="/devis" className="text-blue-600 hover:underline text-sm">
              Generer des factures depuis un devis
            </Link>
          )}
        </div>
      ) : (
        <>
          {/* Mobile */}
          <div className="sm:hidden space-y-3">
            {factures.map(f => (
              <div key={f.id} className="bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-mono text-sm font-medium">{f.numero}</p>
                    <p className="text-xs text-gray-500">{TYPE_LABELS[f.type] || f.type}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[f.statut] || "bg-gray-100 text-gray-700"}`}>
                    {f.statut}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{f.objet}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">{f.date_emission}</span>
                  <span className="font-semibold">{eur(f.total_ttc)}</span>
                </div>
                {corbeille ? (
                  <form action={restaurerFacture} className="mt-3">
                    <input type="hidden" name="facture_id" value={f.id} />
                    <button type="submit" className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                      Restaurer
                    </button>
                  </form>
                ) : (
                  <div className="mt-3 flex flex-col gap-2">
                    <a href={`/api/factures/${f.id}/document`} className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                      Telecharger (Word)
                    </a>
                    {f.statut === "brouillon" && (
                      <form action={archiverFacture}>
                        <input type="hidden" name="facture_id" value={f.id} />
                        <input type="hidden" name="retour" value="/factures" />
                        <button type="submit" className="block w-full text-center px-3 py-2 border border-red-300 text-red-600 rounded text-sm font-medium">
                          Supprimer (corbeille)
                        </button>
                      </form>
                    )}
                    {(f.statut === "emise" || f.statut === "payee" || f.statut === "en_retard") && (
                      <form action={annulerFacture}>
                        <input type="hidden" name="facture_id" value={f.id} />
                        <input type="hidden" name="retour" value="/factures" />
                        <button type="submit" className="block w-full text-center px-3 py-2 border border-orange-300 text-orange-600 rounded text-sm font-medium">
                          Annuler (avoir)
                        </button>
                      </form>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
          {/* Desktop */}
          <div className="hidden sm:block bg-white rounded-lg border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Numero</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Objet</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium text-right">Total TTC</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {factures.map(f => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono font-medium">{f.numero}</td>
                    <td className="px-4 py-3">{TYPE_LABELS[f.type] || f.type}</td>
                    <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{f.objet}</td>
                    <td className="px-4 py-3 text-gray-500">{f.date_emission}</td>
                    <td className="px-4 py-3 text-right font-medium">{eur(f.total_ttc)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[f.statut] || "bg-gray-100 text-gray-700"}`}>
                        {f.statut}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {corbeille ? (
                        <form action={restaurerFacture} className="inline">
                          <input type="hidden" name="facture_id" value={f.id} />
                          <button type="submit" className="text-[#1A355E] hover:underline font-medium">Restaurer</button>
                        </form>
                      ) : (
                        <>
                          <a href={`/api/factures/${f.id}/document`} className="text-[#1A355E] hover:underline font-medium">
                            Telecharger
                          </a>
                          <ActionsFacture f={f} />
                        </>
                      )}
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
