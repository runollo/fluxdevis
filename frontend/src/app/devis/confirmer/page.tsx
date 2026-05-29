import { serverFetch } from "@/lib/api";
import { archiverDevis, supprimerDevisDefinitif } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface DevisSummary {
  id: number; reference: string; statut: string;
  client_raison_sociale: string; offre_nom: string; total_ttc: string;
}

export default async function ConfirmerDevisPage(
  { searchParams }: { searchParams: Promise<{ id?: string; mode?: string; retour?: string; err?: string }> }
) {
  const params = await searchParams;
  const id = params.id;
  const definitif = params.mode === "definitif";
  const retour = params.retour || (definitif ? "/devis?archives=1" : "/devis");

  let d: DevisSummary | null = null;
  if (id) {
    try { d = await serverFetch<DevisSummary>(`/devis/${id}`); } catch {}
  }

  if (!id || !d) {
    return (
      <div className="max-w-xl">
        <Link href="/devis" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour aux devis</Link>
        <div className="mt-4 bg-white border rounded-lg p-8 text-center text-gray-400">Devis introuvable</div>
      </div>
    );
  }

  const errMot = params.err === "mot";
  const errApi = params.err && params.err !== "mot" ? params.err : null;

  return (
    <div className="max-w-xl">
      <Link href={retour} className="text-gray-400 hover:text-gray-600 text-sm">&larr; Annuler</Link>

      <div className={`mt-4 bg-white border rounded-lg p-5 ${definitif ? "border-red-300" : ""}`}>
        <h1 className="text-lg font-bold text-gray-900 mb-1">
          {definitif ? "Supprimer definitivement ce devis ?" : "Mettre ce devis a la corbeille ?"}
        </h1>
        <p className="font-mono text-sm text-[#1A355E]">{d.reference}</p>
        <p className="text-sm text-gray-600 mb-4">{d.client_raison_sociale} — {d.offre_nom} — {eur(d.total_ttc)}</p>

        {definitif ? (
          <>
            <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700 mb-4">
              <strong>Action irreversible.</strong> Le devis et ses brouillons de factures seront
              <strong> definitivement detruits</strong> (aucune restauration possible). Les factures
              deja emises ou annulees, conservees legalement, bloquent cette suppression.
            </div>
            {errMot && (
              <div className="mb-3 rounded border border-orange-200 bg-orange-50 p-2 text-sm text-orange-700">
                Saisie incorrecte : tapez exactement SUPPRIMER et cochez la case.
              </div>
            )}
            {errApi && (
              <div className="mb-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">{errApi}</div>
            )}
            <form action={supprimerDevisDefinitif} className="space-y-3">
              <input type="hidden" name="devis_id" value={d.id} />
              <div>
                <label className="block text-sm text-gray-600 mb-1">Tapez <strong>SUPPRIMER</strong> pour confirmer</label>
                <input name="confirmation" autoComplete="off" className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" name="comprends" value="1" />
                Je comprends que cette suppression est definitive et irreversible.
              </label>
              <div className="flex gap-2 pt-1">
                <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded text-sm font-medium">
                  Supprimer definitivement
                </button>
                <Link href={retour} className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">Annuler</Link>
              </div>
            </form>
          </>
        ) : (
          <>
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600 mb-4">
              Le devis sera place dans la corbeille. Action <strong>reversible</strong> : vous pourrez le restaurer.
            </div>
            <form action={archiverDevis} className="flex gap-2">
              <input type="hidden" name="devis_id" value={d.id} />
              <input type="hidden" name="retour" value="/devis" />
              <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
                Confirmer la mise en corbeille
              </button>
              <Link href={retour} className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">Annuler</Link>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
