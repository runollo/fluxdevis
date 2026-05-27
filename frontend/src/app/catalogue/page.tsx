"use client";
import { useEffect, useState } from "react";
import { api, type Offre, type Option } from "@/lib/api";

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

  if (loading) return <p className="text-gray-500">Chargement...</p>;
  if (error) return <p className="text-red-600">Erreur : {error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Catalogue</h1>
      <div className="flex gap-2 mb-4">
        {(["offres", "options"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${tab === t ? "bg-[#1A355E] text-white" : "bg-white border text-gray-700 hover:bg-gray-50"}`}>
            {t === "offres" ? `Offres (${offres.length})` : `Options (${options.length})`}
          </button>
        ))}
      </div>

      {tab === "offres" ? (
        <div className="bg-white rounded-lg border overflow-hidden">
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
                  <td className="px-4 py-3 text-right">{Number(o.tarif_achat).toLocaleString("fr-FR")} &euro;</td>
                  <td className="px-4 py-3 text-right">{Number(o.tarif_vente_conseille).toLocaleString("fr-FR")} &euro;</td>
                  <td className="px-4 py-3 text-right">{(Number(o.taux_marge) * 100).toFixed(0)} %</td>
                  <td className="px-4 py-3 text-right">{o.pages}</td>
                  <td className="px-4 py-3 text-right">{o.heures} h</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
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
      )}
    </div>
  );
}
