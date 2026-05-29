import { serverFetch } from "@/lib/api";
import { genererFactures, changerStatut, definirMiseEnLigne, genererFactureMaintenance, envoyerFacture } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface OptionLigne {
  code: string; nom: string; type_ligne: string; quantite: number;
  prix_setup_ht: string; prix_mensuel_ht: string; inclus: boolean;
}
interface Ligne { designation: string; quantite: number; prix_unitaire_vente: string; }
interface ArticleOffert { designation: string; prix_vente: string; }
interface FactureLien {
  id: number; numero: string; type: string; statut: string; total_ttc: string; date_emission: string;
}
interface Maintenance {
  recurrent_ht: string; recurrent_ttc: string; a_facturer: boolean; leasing: boolean;
  periode_due: { debut: string; fin: string; montant_ttc: string } | null;
}
interface DevisDetail {
  id: number; reference: string; statut: string;
  date_emission: string; date_validite: string; date_mise_en_ligne: string | null;
  maintenance: Maintenance;
  client_raison_sociale: string; client_adresse: string | null;
  client_cp: string | null; client_ville: string | null;
  client_interlocuteur: string | null; client_telephone: string | null;
  client_email: string | null; client_siret: string | null;
  offre_nom: string; offre_type_site: string;
  mode_reglement: string; plan_paiement: string | null;
  prix_vente_final: string; total_prestations_ht: string;
  loyer_mensuel: string | null; duree_financement_mois: number | null;
  commercial: string | null;
  total_ht: string; total_tva: string; total_ttc: string;
  options: OptionLigne[]; lignes: Ligne[]; articles_offerts: ArticleOffert[];
  factures: FactureLien[];
}

const STATUTS = [
  { value: "brouillon", label: "Brouillon" },
  { value: "envoye", label: "Envoye" },
  { value: "accepte", label: "Accepte" },
  { value: "refuse", label: "Refuse" },
  { value: "expire", label: "Expire" },
];
const STATUT_COLORS: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-700", envoye: "bg-blue-100 text-blue-700",
  accepte: "bg-green-100 text-green-700", refuse: "bg-red-100 text-red-700",
  expire: "bg-orange-100 text-orange-700",
};
const STATUT_FACTURE: Record<string, string> = {
  brouillon: "bg-gray-100 text-gray-700", emise: "bg-blue-100 text-blue-700",
  payee: "bg-green-100 text-green-700", en_retard: "bg-red-100 text-red-700",
  annulee: "bg-orange-100 text-orange-700",
};
const TYPE_FACTURE: Record<string, string> = {
  acompte: "Acompte", solde: "Solde", maintenance: "Maintenance",
};

function Info({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-sm text-gray-800">{value}</p>
    </div>
  );
}

export default async function DevisDetailPage({ searchParams }: { searchParams: Promise<{ id?: string; erreur?: string; maint_erreur?: string; suppr_msg?: string; envoye?: string }> }) {
  const params = await searchParams;
  const id = params.id;
  let d: DevisDetail | null = null;
  if (id) {
    try { d = await serverFetch<DevisDetail>(`/devis/${id}/detail`); } catch {}
  }

  if (!d) {
    return (
      <div>
        <Link href="/devis" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour aux devis</Link>
        <div className="mt-4 bg-white border rounded-lg p-8 text-center text-gray-400">Devis introuvable</div>
      </div>
    );
  }

  const optionsPayantes = d.options.filter(o => !o.inclus && (Number(o.prix_setup_ht) > 0 || Number(o.prix_mensuel_ht) > 0));
  const optionsIncluses = d.options.filter(o => o.inclus || (Number(o.prix_setup_ht) === 0 && Number(o.prix_mensuel_ht) === 0));

  return (
    <div className="max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <Link href="/devis" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 font-mono">{d.reference}</h1>
            <p className="text-sm text-gray-500">{d.client_raison_sociale}</p>
          </div>
        </div>
        <span className={`self-start px-3 py-1 rounded text-sm font-medium ${STATUT_COLORS[d.statut] || "bg-gray-100 text-gray-700"}`}>
          {d.statut}
        </span>
      </div>

      {params.erreur && (
        <div className="mb-4 rounded-lg border border-orange-200 bg-orange-50 p-3 text-sm text-orange-700">
          Les factures existent deja pour ce devis (voir la section Factures ci-dessous).
        </div>
      )}

      {params.suppr_msg && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {params.suppr_msg}
        </div>
      )}

      {params.envoye === "1" && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          Facture envoyee par email au client.
        </div>
      )}

      {/* Actions */}
      <div className="bg-white border rounded-lg p-4 mb-4 flex flex-col sm:flex-row sm:items-end gap-4">
        <form action={changerStatut} className="flex items-end gap-2">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Statut</label>
            <input type="hidden" name="devis_id" value={d.id} />
            <select name="statut" defaultValue={d.statut} className="border rounded px-3 py-2 text-sm">
              {STATUTS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
            Mettre a jour
          </button>
        </form>
        <div className="flex-1" />
        <a href={`/api/devis/${d.id}/document`}
          className="px-4 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium text-center">
          Telecharger le devis (Word)
        </a>
        {d.factures.length === 0 && (
          <form action={genererFactures}>
            <input type="hidden" name="devis_id" value={d.id} />
            <input type="hidden" name="retour" value={`/devis/detail?id=${d.id}`} />
            <button type="submit" className="w-full px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
              Generer les factures
            </button>
          </form>
        )}
        <Link href={`/devis/confirmer?id=${d.id}&retour=${encodeURIComponent(`/devis/detail?id=${d.id}`)}`}
          className="w-full px-4 py-2 border border-red-300 text-red-600 rounded text-sm font-medium text-center">
          Supprimer ce devis
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Client */}
        <div className="bg-white border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Client</h2>
          <div className="space-y-2">
            <Info label="Raison sociale" value={d.client_raison_sociale} />
            <Info label="Interlocuteur" value={d.client_interlocuteur} />
            <Info label="Adresse" value={[d.client_adresse, [d.client_cp, d.client_ville].filter(Boolean).join(" ")].filter(Boolean).join(", ")} />
            <Info label="Telephone" value={d.client_telephone} />
            <Info label="Email" value={d.client_email} />
            <Info label="SIRET" value={d.client_siret} />
          </div>
        </div>

        {/* Devis */}
        <div className="bg-white border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Devis</h2>
          <div className="grid grid-cols-2 gap-2">
            <Info label="Offre" value={`${d.offre_nom} (${d.offre_type_site})`} />
            <Info label="Mode de reglement" value={d.mode_reglement} />
            <Info label="Plan de paiement" value={d.plan_paiement} />
            <Info label="Date d'emission" value={d.date_emission} />
            <Info label="Valable jusqu'au" value={d.date_validite} />
            <Info label="Commercial" value={d.commercial} />
            {d.mode_reglement === "Leasing" && d.loyer_mensuel && (
              <Info label="Loyer mensuel" value={`${eur(d.loyer_mensuel)} / mois (${d.duree_financement_mois} mois)`} />
            )}
          </div>
        </div>
      </div>

      {/* Prestations / options */}
      {(optionsPayantes.length > 0 || d.lignes.length > 0) && (
        <div className="bg-white border rounded-lg p-4 mt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Prestations et options</h2>
          <table className="w-full text-sm">
            <thead className="text-left text-gray-400 text-xs">
              <tr><th className="py-1">Designation</th><th className="py-1 text-center">Qte</th><th className="py-1 text-right">Setup HT</th><th className="py-1 text-right">Mensuel HT</th></tr>
            </thead>
            <tbody className="divide-y">
              <tr><td className="py-1.5">{d.offre_nom}</td><td className="text-center">1</td><td className="text-right">{eur(d.prix_vente_final)}</td><td className="text-right">-</td></tr>
              {d.lignes.map((lg, i) => (
                <tr key={`l${i}`}><td className="py-1.5">{lg.designation}</td><td className="text-center">{lg.quantite}</td><td className="text-right">{eur(lg.prix_unitaire_vente)}</td><td className="text-right">-</td></tr>
              ))}
              {optionsPayantes.map((o, i) => (
                <tr key={`o${i}`}><td className="py-1.5">{o.nom}</td><td className="text-center">{o.quantite}</td><td className="text-right">{Number(o.prix_setup_ht) > 0 ? eur(o.prix_setup_ht) : "-"}</td><td className="text-right">{Number(o.prix_mensuel_ht) > 0 ? eur(o.prix_mensuel_ht) : "-"}</td></tr>
              ))}
            </tbody>
          </table>
          {optionsIncluses.length > 0 && (
            <p className="text-xs text-gray-400 mt-2">Inclus : {optionsIncluses.map(o => o.nom).join(", ")}</p>
          )}
        </div>
      )}

      {/* Articles offerts */}
      {d.articles_offerts.length > 0 && (
        <div className="bg-white border rounded-lg p-4 mt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Articles offerts</h2>
          <ul className="text-sm space-y-1">
            {d.articles_offerts.map((a, i) => (
              <li key={i} className="flex justify-between"><span>{a.designation}</span><span className="text-green-700">{eur(a.prix_vente)} - Offert</span></li>
            ))}
          </ul>
        </div>
      )}

      {/* Totaux */}
      <div className="bg-white border rounded-lg p-4 mt-4 max-w-sm ml-auto">
        <div className="flex justify-between text-sm py-1"><span className="text-gray-500">Total HT</span><span>{eur(d.total_ht)}</span></div>
        <div className="flex justify-between text-sm py-1"><span className="text-gray-500">TVA 20 %</span><span>{eur(d.total_tva)}</span></div>
        <div className="flex justify-between text-base font-bold py-1 border-t mt-1 pt-2"><span>Total TTC</span><span>{eur(d.total_ttc)}</span></div>
      </div>

      {/* Mise en ligne & maintenance (recurrent) */}
      {Number(d.maintenance.recurrent_ttc) > 0 && (
        <div className="bg-white border rounded-lg p-4 mt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Maintenance (recurrent)</h2>

          {params.maint_erreur && (
            <div className="mb-3 rounded border border-orange-200 bg-orange-50 p-2 text-sm text-orange-700">
              Generation impossible : periode pas encore commencee, deja facturee, ou date de mise en ligne manquante.
            </div>
          )}

          <p className="text-sm mb-3">
            Abonnement mensuel : <span className="font-semibold">{eur(d.maintenance.recurrent_ttc)} TTC / mois</span>
            <span className="text-gray-400"> ({eur(d.maintenance.recurrent_ht)} HT)</span>
          </p>

          {d.maintenance.leasing ? (
            <p className="text-sm text-gray-500 italic">
              Mode leasing : la maintenance est geree par le leaser (facturation a venir).
            </p>
          ) : (
            <div className="space-y-3">
              {/* Date de mise en ligne */}
              <form action={definirMiseEnLigne} className="flex flex-wrap items-end gap-2">
                <input type="hidden" name="devis_id" value={d.id} />
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Date de mise en ligne du site</label>
                  <input type="date" name="date_mise_en_ligne" defaultValue={d.date_mise_en_ligne ?? ""}
                    className="border rounded px-3 py-2 text-sm" />
                </div>
                <button type="submit" className="px-4 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                  Enregistrer
                </button>
              </form>

              {!d.date_mise_en_ligne ? (
                <p className="text-sm text-gray-500">
                  Renseignez la date de mise en ligne pour activer la facturation de la maintenance.
                </p>
              ) : d.maintenance.a_facturer && d.maintenance.periode_due ? (
                <div className="flex flex-wrap items-center gap-3 rounded border border-green-200 bg-green-50 p-3">
                  <p className="text-sm text-green-800">
                    Periode a facturer : <span className="font-medium">{d.maintenance.periode_due.debut} au {d.maintenance.periode_due.fin}</span>
                    {" "}- {eur(d.maintenance.periode_due.montant_ttc)} TTC
                  </p>
                  <form action={genererFactureMaintenance}>
                    <input type="hidden" name="devis_id" value={d.id} />
                    <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
                      Generer la facture de maintenance
                    </button>
                  </form>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  Maintenance a jour : la prochaine periode n&apos;a pas encore commence.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Factures liees */}
      <div className="bg-white border rounded-lg p-4 mt-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Factures ({d.factures.length})</h2>
        {d.factures.length === 0 ? (
          <p className="text-sm text-gray-400">Aucune facture generee. Utilisez le bouton &laquo; Generer les factures &raquo; ci-dessus.</p>
        ) : (
          <ul className="divide-y">
            {d.factures.map(f => (
              <li key={f.id} className="py-2 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-mono text-sm truncate">{f.numero}</p>
                  <p className="text-xs text-gray-400">{TYPE_FACTURE[f.type] || f.type}</p>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${STATUT_FACTURE[f.statut] || "bg-gray-100 text-gray-700"}`}>{f.statut}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-sm font-medium">{eur(f.total_ttc)}</span>
                  <a href={`/api/factures/${f.id}/document`} className="text-[#1A355E] hover:underline text-sm font-medium">Telecharger</a>
                  <form action={envoyerFacture} className="inline">
                    <input type="hidden" name="facture_id" value={f.id} />
                    <input type="hidden" name="retour" value={`/devis/detail?id=${d.id}`} />
                    <button type="submit" className="text-[#1A355E] hover:underline text-sm font-medium">Envoyer</button>
                  </form>
                  {f.statut === "brouillon" && (
                    <Link href={`/factures/confirmer?id=${f.id}&action=archiver&retour=${encodeURIComponent(`/devis/detail?id=${d.id}`)}`}
                      className="text-red-600 hover:underline text-sm font-medium">Supprimer</Link>
                  )}
                  {(f.statut === "emise" || f.statut === "payee" || f.statut === "en_retard") && (
                    <Link href={`/factures/confirmer?id=${f.id}&action=annuler&retour=${encodeURIComponent(`/devis/detail?id=${d.id}`)}`}
                      className="text-orange-600 hover:underline text-sm font-medium">Annuler</Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
