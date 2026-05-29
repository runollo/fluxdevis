import { serverFetch, type Offre, type Option } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number) { return Number(v).toLocaleString("fr-FR") + " \u20ac"; }

export default async function CataloguePage({ searchParams }: { searchParams: Promise<{ tab?: string; q?: string }> }) {
  const params = await searchParams;
  const tab = params.tab === "options" ? "options" : "offres";
  const q = (params.q || "").trim();
  const qParam = q ? `?q=${encodeURIComponent(q)}` : "";

  let offres: Offre[] = [];
  let options: Option[] = [];
  let error = "";

  try {
    if (tab === "offres") {
      offres = await serverFetch<Offre[]>(`/offres/${qParam}`);
    } else {
      options = await serverFetch<Option[]>(`/options/${qParam}`);
    }
  } catch (e) {
    error = String(e);
  }

  if (error) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Catalogue</h1>
        <Link href={tab === "offres" ? "/catalogue/offre" : "/catalogue/option"}
          className="px-4 py-2.5 bg-[#1A355E] text-white rounded text-sm font-medium text-center">
          + {tab === "offres" ? "Nouvelle offre" : "Nouvelle option"}
        </Link>
      </div>
      <div className="flex gap-2 mb-4">
        <Link href="/catalogue"
          className={`flex-1 sm:flex-none px-4 py-2.5 rounded text-sm font-medium text-center transition-colors ${tab === "offres" ? "bg-[#1A355E] text-white" : "bg-white border text-gray-700"}`}>
          Offres
        </Link>
        <Link href="/catalogue?tab=options"
          className={`flex-1 sm:flex-none px-4 py-2.5 rounded text-sm font-medium text-center transition-colors ${tab === "options" ? "bg-[#1A355E] text-white" : "bg-white border text-gray-700"}`}>
          Options
        </Link>
      </div>

      {/* Recherche (sur l'onglet courant) */}
      <form method="GET" className="mb-4 flex gap-2">
        {tab === "options" && <input type="hidden" name="tab" value="options" />}
        <input
          type="search" name="q" defaultValue={q}
          placeholder={tab === "offres" ? "Rechercher une offre..." : "Rechercher une option (nom, code, categorie)..."}
          className="flex-1 border rounded px-3 py-2 text-sm"
        />
        <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">Rechercher</button>
        {q && <Link href={tab === "options" ? "/catalogue?tab=options" : "/catalogue"} className="px-4 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">Effacer</Link>}
      </form>

      {tab === "offres" ? (
        <>
          {/* Mobile */}
          <div className="sm:hidden space-y-3">
            {offres.map((o) => (
              <Link key={o.id} href={`/catalogue/offre?id=${o.id}`} className="block bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-sm leading-tight">{o.nom}</h3>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded ml-2 shrink-0">{o.type_site}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  <div className="text-gray-500">Achat</div><div className="text-right">{eur(o.tarif_achat)}</div>
                  <div className="text-gray-500">Vente</div><div className="text-right font-medium">{eur(o.tarif_vente_conseille)}</div>
                  <div className="text-gray-500">Marge</div><div className="text-right">{(Number(o.taux_marge) * 100).toFixed(0)} %</div>
                  <div className="text-gray-500">Pages</div><div className="text-right">{o.pages}</div>
                </div>
              </Link>
            ))}
          </div>
          {/* Desktop */}
          <div className="hidden sm:block bg-white rounded-lg border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Nom</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium text-right">Achat</th>
                  <th className="px-4 py-3 font-medium text-right">Vente</th>
                  <th className="px-4 py-3 font-medium text-right">Marge</th>
                  <th className="px-4 py-3 font-medium text-right">Pages</th>
                  <th className="px-4 py-3 font-medium text-right">Heures</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {offres.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{o.nom}</td>
                    <td className="px-4 py-3 text-gray-500">{o.type_site}</td>
                    <td className="px-4 py-3 text-right">{eur(o.tarif_achat)}</td>
                    <td className="px-4 py-3 text-right">{eur(o.tarif_vente_conseille)}</td>
                    <td className="px-4 py-3 text-right">{(Number(o.taux_marge) * 100).toFixed(0)} %</td>
                    <td className="px-4 py-3 text-right">{o.pages}</td>
                    <td className="px-4 py-3 text-right">{o.heures} h</td>
                    <td className="px-4 py-3 text-right"><Link href={`/catalogue/offre?id=${o.id}`} className="text-blue-600 hover:underline text-xs">Modifier</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <>
          {/* Mobile */}
          <div className="sm:hidden space-y-3">
            {options.map((o) => (
              <Link key={o.id} href={`/catalogue/option?id=${o.id}`} className="block bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-medium text-sm">{o.nom}</h3>
                    <p className="text-xs text-gray-400 font-mono">{o.code}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium shrink-0 ml-2 ${o.type_ligne === "PACK" ? "bg-purple-100 text-purple-700" : o.type_ligne === "OPTION_RECURRENT" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>
                    {o.type_ligne.replace("OPTION_", "")}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{o.categorie}</span>
                  <div className="text-right">
                    {Number(o.vente_setup) > 0 && <span className="mr-3">{Number(o.vente_setup).toFixed(0)} &euro; setup</span>}
                    {Number(o.vente_mensuel) > 0 && <span className="font-medium">{Number(o.vente_mensuel).toFixed(0)} &euro;/m</span>}
                    {Number(o.vente_setup) === 0 && Number(o.vente_mensuel) === 0 && <span className="text-gray-400">-</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {/* Desktop */}
          <div className="hidden sm:block bg-white rounded-lg border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium">Code</th>
                  <th className="px-4 py-3 font-medium">Nom</th>
                  <th className="px-4 py-3 font-medium">Cat.</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium text-right">Setup</th>
                  <th className="px-4 py-3 font-medium text-right">Mensuel</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {options.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">{o.code}</td>
                    <td className="px-4 py-3">{o.nom}</td>
                    <td className="px-4 py-3 text-gray-500">{o.categorie}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${o.type_ligne === "PACK" ? "bg-purple-100 text-purple-700" : o.type_ligne === "OPTION_RECURRENT" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>
                        {o.type_ligne.replace("OPTION_", "")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">{Number(o.vente_setup) > 0 ? `${Number(o.vente_setup).toFixed(2)} \u20ac` : "-"}</td>
                    <td className="px-4 py-3 text-right">{Number(o.vente_mensuel) > 0 ? `${Number(o.vente_mensuel).toFixed(2)} \u20ac/m` : "-"}</td>
                    <td className="px-4 py-3 text-right"><Link href={`/catalogue/option?id=${o.id}`} className="text-blue-600 hover:underline text-xs">Modifier</Link></td>
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
