import { serverFetch } from "@/lib/api";
import { modifierFacture } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

interface FactureSummary {
  id: number; numero: string; type: string; statut: string;
  date_emission: string; date_echeance: string; objet: string; total_ttc: string;
}
interface HistoriqueLigne {
  id: number; champ: string; ancienne_valeur: string | null; nouvelle_valeur: string | null;
  motif: string | null; auteur: string | null; cree_le: string | null;
}

const LIBELLE_CHAMP: Record<string, string> = {
  numero: "Numero de facture",
  date_emission: "Date d'emission",
  date_echeance: "Date d'echeance",
};
function libelleChamp(c: string): string {
  if (c.startsWith("echeance[")) return `Echeance ${c}`;
  return LIBELLE_CHAMP[c] || c;
}

export default async function EditerFacturePage(
  { searchParams }: { searchParams: Promise<{ id?: string; retour?: string; suppr_msg?: string }> }
) {
  const params = await searchParams;
  const id = params.id;
  const retour = params.retour || "/factures";

  let f: FactureSummary | null = null;
  let historique: HistoriqueLigne[] = [];
  if (id) {
    try { f = await serverFetch<FactureSummary>(`/factures/${id}`); } catch {}
    try { historique = await serverFetch<HistoriqueLigne[]>(`/factures/${id}/historique`); } catch {}
  }

  if (!f) {
    return (
      <div>
        <Link href={retour} className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <div className="mt-4 bg-white border rounded-lg p-8 text-center text-gray-400">Facture introuvable</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-5">
        <Link href={retour} className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <div>
          <h1 className="text-lg sm:text-xl font-bold text-gray-900 font-mono">{f.numero}</h1>
          <p className="text-sm text-gray-500">{f.objet}</p>
        </div>
      </div>

      {params.suppr_msg && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {params.suppr_msg}
        </div>
      )}

      <div className="bg-white border rounded-lg p-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Numero & dates</h2>
        {f.statut !== "brouillon" && (
          <div className="mb-3 rounded border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
            Cette facture est deja emise. La modification reste possible mais sera
            enregistree dans l&apos;historique ci-dessous.
          </div>
        )}
        <form action={modifierFacture} className="space-y-3">
          <input type="hidden" name="facture_id" value={f.id} />
          <input type="hidden" name="retour" value={retour} />
          <div>
            <label className="block text-xs text-gray-400 mb-1">Numero de facture</label>
            <input name="numero" defaultValue={f.numero} required
              className="w-full border rounded px-3 py-2 text-sm font-mono" />
          </div>
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Date d&apos;emission</label>
              <input type="date" name="date_emission" defaultValue={f.date_emission}
                className="border rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Date d&apos;echeance</label>
              <input type="date" name="date_echeance" defaultValue={f.date_echeance}
                className="border rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Motif (facultatif)</label>
            <input name="motif" placeholder="ex. regularisation"
              className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
            Enregistrer
          </button>
        </form>
      </div>

      {historique.length > 0 && (
        <div className="bg-white border rounded-lg p-4 mt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">
            Historique des modifications ({historique.length})
          </h2>
          <ul className="divide-y text-sm">
            {historique.map(h => (
              <li key={h.id} className="py-2">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium text-gray-800">{libelleChamp(h.champ)}</span>
                  <span className="text-gray-400 line-through">{h.ancienne_valeur ?? "(vide)"}</span>
                  <span className="text-gray-400">&rarr;</span>
                  <span className="text-gray-800">{h.nouvelle_valeur ?? "(vide)"}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {h.cree_le ? new Date(h.cree_le).toLocaleString("fr-FR") : ""}
                  {h.motif ? ` — ${h.motif}` : ""}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
