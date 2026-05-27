"use client";
import { useEffect, useState } from "react";
import { api, type Offre, type Option } from "@/lib/api";

function eur(v: number) { return Number(v).toLocaleString("fr-FR") + " \u20ac"; }

export default function CataloguePage() {
  const [offres, setOffres] = useState<Offre[]>([]);
  const [options, setOptions] = useState<Option[]>([]);
  const [tab, setTab] = useState<"offres" | "options">("offres");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.offres.list(), api.options.list()])
      .then(([o, opt]) => { setOffres(o); setOptions(opt); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500 p-4">Chargement...</p>;
  if (error) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold mb-4">Catalogue</h1>
      <div className="flex gap-2 mb-4">
        {(["offres", "options"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 sm:flex-none px-4 py-2.5 rounded text-sm font-medium transition-colors ${tab === t ? "bg-[#1A355E] text-white" : "bg-white border text-gray-700 hover:bg-gray-50"}`}>
            {t === "offres" ? `Offres (${offres.length})` : `Options (${options.length})`}
          </button>
        ))}
      </div>

      {tab === "offres" ? (
        <>
          {/* Mobile : cards */}
          <div className="sm:hidden space-y-3">
            {offres.map((o) => (
              <div key={o.id} className="bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-sm leading-tight">{o.nom}</h3>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded ml-2 shrink-0">{o.type_site}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  <div className="text-gray-500">Achat</div><div className="text-right">{eur(o.tarif_achat)}</div>
                  <div className="text-gray-500">Vente</div><div className="text-right font-medium">{eur(o.tarif_vente_conseille)}</div>
                  <div className="text-gray-500">Marge</div><div className="text-right">{(Number(o.taux_marge) * 100).toFixed(0)} %</div>
                  <div className="text-gray-500">Pages</div><div className="text-right">{o.pages}</div>
                  <div className="text-gray-500">Heures</div><div className="text-right">{o.heures} h</div>
                </div>
              </div>
            ))}
          </div>
          {/* Desktop : tableau */}
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <>
          {/* Mobile : cards */}
          <div className="sm:hidden space-y-3">
            {options.map((o) => (
              <div key={o.id} className="bg-white border rounded-lg p-4">
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
                    {Number(o.vente_setup) > 0 && <span className="mr-3">{Number(o.vente_setup).toFixed(0)} \u20ac setup</span>}
                    {Number(o.vente_mensuel) > 0 && <span className="font-medium">{Number(o.vente_mensuel).toFixed(0)} \u20ac/m</span>}
                    {Number(o.vente_setup) === 0 && Number(o.vente_mensuel) === 0 && <span className="text-gray-400">-</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* Desktop : tableau */}
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
