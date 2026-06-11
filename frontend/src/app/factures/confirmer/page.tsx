import { serverFetch } from "@/lib/api";
import { archiverFacture, annulerFacture, supprimerFactureDefinitif, emettreFacture } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface FactureSummary {
  id: number; numero: string; type: string; statut: string; objet: string; total_ttc: string;
}

interface ApercuEmission {
  provisoire: string; numero_prevu: string; compteur: number;
  precedente: string | null; date_emission: string;
}

export default async function ConfirmerFacturePage(
  { searchParams }: { searchParams: Promise<{ id?: string; action?: string; retour?: string; err?: string }> }
) {
  const params = await searchParams;
  const id = params.id;
  const action = params.action === "annuler" ? "annuler"
    : params.action === "definitif" ? "definitif"
    : params.action === "emettre" ? "emettre" : "archiver";
  const retour = params.retour
    || (action === "definitif" ? "/factures?archives=1" : "/factures");

  let f: FactureSummary | null = null;
  if (id) {
    try { f = await serverFetch<FactureSummary>(`/factures/${id}`); } catch {}
  }

  let apercu: ApercuEmission | null = null;
  if (action === "emettre" && id) {
    try { apercu = await serverFetch<ApercuEmission>(`/factures/${id}/apercu-emission`); } catch {}
  }

  if (!id || !f) {
    return (
      <div className="max-w-xl">
        <Link href="/factures" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour aux factures</Link>
        <div className="mt-4 bg-white border rounded-lg p-8 text-center text-gray-400">Facture introuvable</div>
      </div>
    );
  }

  const errMot = params.err === "mot";
  const errMotif = params.err === "motif";
  const errApi = params.err && params.err !== "mot" && params.err !== "motif" ? params.err : null;
  const fort = action === "annuler" || action === "definitif";

  const titre = action === "annuler" ? "Etablir un avoir d'annulation ?"
    : action === "definitif" ? "Supprimer definitivement cette facture ?"
    : action === "emettre" ? "Emettre cette facture (numero legal) ?"
    : "Mettre cette facture a la corbeille ?";

  return (
    <div className="max-w-xl">
      <Link href={retour} className="text-gray-400 hover:text-gray-600 text-sm">&larr; Annuler</Link>

      <div className={`mt-4 bg-white border rounded-lg p-5 ${fort ? "border-red-300" : ""}`}>
        <h1 className="text-lg font-bold text-gray-900 mb-1">{titre}</h1>
        <p className="font-mono text-sm text-[#1A355E]">{f.numero}</p>
        <p className="text-sm text-gray-600 mb-4">{f.objet} — {eur(f.total_ttc)} — statut : {f.statut}</p>

        {errMot && (
          <div className="mb-3 rounded border border-orange-200 bg-orange-50 p-2 text-sm text-orange-700">
            Saisie incorrecte : tapez exactement SUPPRIMER{action === "definitif" ? " et cochez la case." : "."}
          </div>
        )}
        {errMotif && (
          <div className="mb-3 rounded border border-orange-200 bg-orange-50 p-2 text-sm text-orange-700">
            Le motif de l&apos;avoir est obligatoire.
          </div>
        )}
        {errApi && (
          <div className="mb-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">{errApi}</div>
        )}

        {action === "emettre" && (
          <>
            <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800 mb-4">
              La facture en brouillon{" "}
              <strong className="font-mono">{apercu?.provisoire ?? f.numero}</strong> va recevoir
              son numero legal definitif{" "}
              <strong className="font-mono">{apercu?.numero_prevu ?? "…"}</strong>
              {apercu?.precedente
                ? <> , a la suite de <strong className="font-mono">{apercu.precedente}</strong></>
                : <> (1<sup>ere</sup> facture de la serie)</>}.
              <p className="mt-2 text-green-900">
                Une fois emise, ce numero est <strong>fige</strong>{" "}et la facture ne pourra plus
                etre supprimee (seulement annulee par un avoir). Emets bien tes factures dans
                l&apos;ordre chronologique.
              </p>
            </div>
            <form action={emettreFacture} className="flex gap-2">
              <input type="hidden" name="facture_id" value={f.id} />
              <input type="hidden" name="retour" value={retour} />
              <button type="submit" className="px-4 py-2 bg-green-700 text-white rounded text-sm font-medium">
                Emettre {apercu?.numero_prevu ?? ""}
              </button>
              <Link href={retour} className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">Annuler</Link>
            </form>
          </>
        )}

        {action === "archiver" && (
          <>
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600 mb-4">
              La facture (brouillon) sera placee dans la corbeille. Action <strong>reversible</strong>.
            </div>
            <form action={archiverFacture} className="flex gap-2">
              <input type="hidden" name="facture_id" value={f.id} />
              <input type="hidden" name="retour" value={retour} />
              <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
                Confirmer la mise en corbeille
              </button>
              <Link href={retour} className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">Annuler</Link>
            </form>
          </>
        )}

        {action === "annuler" && (
          <>
            <div className="rounded border border-orange-200 bg-orange-50 p-3 text-sm text-orange-700 mb-4">
              Un <strong>avoir</strong> (numero <strong>AV{new Date().getFullYear()}-NNN</strong>, en
              montants negatifs) sera emis pour annuler cette facture. Le numero de la facture
              d&apos;origine est <strong>conserve</strong> (obligation legale) et son statut passe a
              <strong> annulee</strong>. La TVA est regularisee sur la periode courante. Acte comptable engageant.
            </div>
            <form action={annulerFacture} className="space-y-3">
              <input type="hidden" name="facture_id" value={f.id} />
              <input type="hidden" name="retour" value={retour} />
              <div>
                <label className="block text-sm text-gray-600 mb-1">Motif de l&apos;avoir (obligatoire, figure sur le document)</label>
                <input name="motif" autoComplete="off" placeholder="ex. Prestation finalement offerte"
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div className="flex gap-2 pt-1">
                <button type="submit" className="px-4 py-2 bg-orange-600 text-white rounded text-sm font-medium">
                  Etablir l&apos;avoir
                </button>
                <Link href={retour} className="px-4 py-2 border border-gray-300 text-gray-700 rounded text-sm font-medium">Retour</Link>
              </div>
            </form>
          </>
        )}

        {action === "definitif" && (
          <>
            <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700 mb-4">
              <strong>Action irreversible.</strong> La facture sera <strong>definitivement detruite</strong>.
              Seules les factures en brouillon peuvent l&apos;etre ; une facture emise ou annulee est conservee.
            </div>
            <form action={supprimerFactureDefinitif} className="space-y-3">
              <input type="hidden" name="facture_id" value={f.id} />
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
        )}
      </div>
    </div>
  );
}
