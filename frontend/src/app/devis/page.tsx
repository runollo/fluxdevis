import { serverFetch } from "@/lib/api";
import { genererFactures, archiverDevis, restaurerDevis } from "@/lib/actions";
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
  brouillon: "bg-gray-100 text-gray-700",
  envoye: "bg-blue-100 text-blue-700",
  accepte: "bg-green-100 text-green-700",
  refuse: "bg-red-100 text-red-700",
  expire: "bg-orange-100 text-orange-700",
};

const PAR_PAGE = 25;

export default async function DevisPage(
  { searchParams }: { searchParams: Promise<{ archives?: string; suppr_msg?: string; q?: string; skip?: string }> }
) {
  const params = await searchParams;
  const corbeille = params.archives === "1";
  const q = (params.q || "").trim();
  const skip = Math.max(Number(params.skip) || 0, 0);

  const qs = new URLSearchParams();
  if (corbeille) qs.set("archives", "true");
  if (q) qs.set("q", q);
  qs.set("skip", String(skip));
  qs.set("limit", String(PAR_PAGE));

  let devisList: Devis[] = [];
  try {
    devisList = await serverFetch<Devis[]>(`/devis/?${qs.toString()}`);
  } catch {}

  // Conserve archives/q dans les liens de pagination
  const lienPage = (nouveauSkip: number) => {
    const p = new URLSearchParams();
    if (corbeille) p.set("archives", "1");
    if (q) p.set("q", q);
    if (nouveauSkip > 0) p.set("skip", String(nouveauSkip));
    const s = p.toString();
    return `/devis${s ? `?${s}` : ""}`;
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
          {corbeille ? "Corbeille — devis" : "Devis"} ({devisList.length})
        </h1>
        <div className="flex gap-2">
          {corbeille ? (
            <Link href="/devis" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
              Retour aux devis
            </Link>
          ) : (
            <>
              <a href={`/api/devis/export.xlsx${q ? `?q=${encodeURIComponent(q)}` : ""}`} className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
                Export Excel
              </a>
              <Link href="/devis?archives=1" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
                Corbeille
              </Link>
              <Link href="/simulateur" className="px-4 py-2.5 bg-[#1A355E] text-white rounded text-sm font-medium text-center">
                + Nouveau devis
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

      {/* Recherche */}
      <form method="GET" className="mb-4 flex gap-2">
        {corbeille && <input type="hidden" name="archives" value="1" />}
        <input
          type="search" name="q" defaultValue={q}
          placeholder="Rechercher (reference, client, offre)..."
          className="flex-1 border rounded px-3 py-2 text-sm"
        />
        <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">Rechercher</button>
        {q && <Link href={lienPage(0)} className="px-4 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">Effacer</Link>}
      </form>

      {devisList.length === 0 ? (
        <div className="bg-white border rounded-lg p-8 text-center">
          <p className="text-gray-400 mb-4">{corbeille ? "Corbeille vide" : "Aucun devis enregistre"}</p>
          {!corbeille && (
            <Link href="/simulateur" className="text-blue-600 hover:underline text-sm">Creer un devis depuis le simulateur</Link>
          )}
        </div>
      ) : (
        <>
          {/* Mobile */}
          <div className="sm:hidden space-y-3">
            {devisList.map(d => (
              <div key={d.id} className="bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <Link href={`/devis/detail?id=${d.id}`} className="font-mono text-sm font-medium text-[#1A355E] hover:underline">{d.reference}</Link>
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
                <div className="mt-3 flex flex-col gap-2">
                  {corbeille ? (
                    <form action={restaurerDevis}>
                      <input type="hidden" name="devis_id" value={d.id} />
                      <button type="submit" className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                        Restaurer
                      </button>
                    </form>
                  ) : (
                    <>
                      <a href={`/api/devis/${d.id}/document`} className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                        Telecharger le devis (Word)
                      </a>
                      <form action={genererFactures}>
                        <input type="hidden" name="devis_id" value={d.id} />
                        <input type="hidden" name="retour" value="/devis" />
                        <button type="submit" className="block w-full text-center px-3 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
                          Generer les factures
                        </button>
                      </form>
                      <form action={archiverDevis}>
                        <input type="hidden" name="devis_id" value={d.id} />
                        <input type="hidden" name="retour" value="/devis" />
                        <button type="submit" className="block w-full text-center px-3 py-2 border border-red-300 text-red-600 rounded text-sm font-medium">
                          Supprimer (corbeille)
                        </button>
                      </form>
                    </>
                  )}
                </div>
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
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {devisList.map(d => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono font-medium">
                      <Link href={`/devis/detail?id=${d.id}`} className="text-[#1A355E] hover:underline">{d.reference}</Link>
                    </td>
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
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {corbeille ? (
                        <form action={restaurerDevis} className="inline">
                          <input type="hidden" name="devis_id" value={d.id} />
                          <button type="submit" className="text-[#1A355E] hover:underline font-medium">Restaurer</button>
                        </form>
                      ) : (
                        <>
                          <a href={`/api/devis/${d.id}/document`} className="text-[#1A355E] hover:underline font-medium">
                            Devis
                          </a>
                          <form action={genererFactures} className="inline">
                            <input type="hidden" name="devis_id" value={d.id} />
                            <input type="hidden" name="retour" value="/devis" />
                            <button type="submit" className="ml-3 text-[#1A355E] hover:underline font-medium">
                              Factures
                            </button>
                          </form>
                          <form action={archiverDevis} className="inline">
                            <input type="hidden" name="devis_id" value={d.id} />
                            <input type="hidden" name="retour" value="/devis" />
                            <button type="submit" className="ml-3 text-red-600 hover:underline font-medium">
                              Supprimer
                            </button>
                          </form>
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

      {/* Pagination */}
      {(skip > 0 || devisList.length === PAR_PAGE) && (
        <div className="mt-4 flex items-center justify-between text-sm">
          {skip > 0 ? (
            <Link href={lienPage(Math.max(skip - PAR_PAGE, 0))} className="px-4 py-2 border border-gray-300 rounded font-medium">&larr; Precedent</Link>
          ) : <span />}
          <span className="text-gray-400">Page {Math.floor(skip / PAR_PAGE) + 1}</span>
          {devisList.length === PAR_PAGE ? (
            <Link href={lienPage(skip + PAR_PAGE)} className="px-4 py-2 border border-gray-300 rounded font-medium">Suivant &rarr;</Link>
          ) : <span />}
        </div>
      )}
    </div>
  );
}
