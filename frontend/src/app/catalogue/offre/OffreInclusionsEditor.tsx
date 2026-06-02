"use client";

// Editeur des OPTIONS INCLUSES d'office dans une offre. Une option cochee apparait
// avec le statut "Inclus" dans le simulateur (comprise sans surcout). Le reglage
// n'impacte que le catalogue : les devis deja emis gardent leurs prix figes.
// Persiste via PUT /offres/{id}/inclusions (remplacement complet de la liste).

import { useMemo, useState } from "react";
import { saveInclusions } from "@/lib/actions";
import type { OptionStatut } from "@/lib/api";

function eur(v: number) {
  return v.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

export default function OffreInclusionsEditor(
  { offreId, options }: { offreId: number; options: OptionStatut[] }
) {
  const [inclus, setInclus] = useState<Set<number>>(
    () => new Set(options.filter((o) => o.statut === "Inclus").map((o) => o.id))
  );

  const toggle = (id: number) =>
    setInclus((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });

  // Grouper par categorie, en respectant l'ordre d'apparition.
  const groupes = useMemo(() => {
    const map = new Map<string, OptionStatut[]>();
    for (const o of options) {
      if (!map.has(o.categorie)) map.set(o.categorie, []);
      map.get(o.categorie)!.push(o);
    }
    return Array.from(map.entries());
  }, [options]);

  return (
    <div className="max-w-2xl mt-6 bg-white border rounded-lg p-4 sm:p-6">
      <div className="flex items-baseline justify-between gap-3 mb-1">
        <h2 className="text-sm font-semibold text-gray-500 uppercase">Options incluses</h2>
        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
          {inclus.size} incluse(s)
        </span>
      </div>
      <p className="text-xs text-gray-400 mb-4">
        Cochez les options comprises d&apos;office dans cette offre (statut &laquo; Inclus &raquo;
        dans le simulateur). Sans surcout pour le client.
      </p>

      <form action={saveInclusions}>
        <input type="hidden" name="id" value={offreId} />
        <input type="hidden" name="option_ids_json" value={JSON.stringify(Array.from(inclus))} />

        <div className="space-y-4 max-h-[28rem] overflow-y-auto pr-1">
          {groupes.map(([cat, opts]) => (
            <div key={cat}>
              <p className="text-xs font-semibold text-gray-500 mb-1">{cat}</p>
              <div className="space-y-1">
                {opts.map((o) => {
                  const prix = o.vente_setup > 0
                    ? `${eur(o.vente_setup)}`
                    : o.vente_mensuel > 0 ? `${eur(o.vente_mensuel)}/mois` : "";
                  return (
                    <label key={o.id}
                      className="flex items-start gap-2 text-sm py-1 px-2 rounded hover:bg-gray-50 cursor-pointer">
                      <input type="checkbox" checked={inclus.has(o.id)} onChange={() => toggle(o.id)}
                        className="mt-1 accent-[#1A355E]" />
                      <span className="flex-1 min-w-0">
                        <span className="text-gray-800">{o.nom}</span>
                        {o.type_ligne === "PACK" && (
                          <span className="ml-1 text-[10px] px-1 py-0.5 rounded bg-amber-100 text-amber-700">pack</span>
                        )}
                        {prix && <span className="text-gray-400"> — {prix}</span>}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3 pt-4 border-t mt-4">
          <button type="submit"
            className="px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            Enregistrer les options incluses
          </button>
        </div>
      </form>
    </div>
  );
}
