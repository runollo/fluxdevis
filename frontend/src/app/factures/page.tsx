import { serverFetch } from "@/lib/api";
import { restaurerFacture, envoyerFacture, marquerPayee, marquerImpayee, relancerFacture } from "@/lib/actions";
import Link from "next/link";
import EnvoiGroupe from "./EnvoiGroupe";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

interface Facture {
  id: number; numero: string; type: string; statut: string;
  date_emission: string; date_echeance: string; objet: string; total_ttc: string;
  devis_id?: number | null; client_id?: number | null; client?: string | null;
  projet_ref?: string | null; projet_nom?: string | null;
  nb_envois?: number; dernier_envoi?: string | null; dernier_envoi_mode?: string | null;
  a_relancer?: boolean; jours_retard?: number | null;
}

// Date+heure d'un envoi, en heure de Paris (independant du fuseau serveur).
function envoiLabel(iso: string, mode?: string | null): string {
  const d = new Date(iso).toLocaleString("fr-FR", {
    timeZone: "Europe/Paris", day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
  const m = mode === "expediteur" ? "a vous (transfert)" : "au client";
  return `${d} (${m})`;
}
interface ClientOpt { id: number; raison_sociale: string; }
interface ProjetOpt { id: number; reference: string; offre_nom?: string }

// Statuts proposes au filtre (libelles metier alignes sur les statuts reels).
const STATUT_FILTRES: { value: string; label: string }[] = [
  { value: "", label: "Tous les statuts" },
  { value: "brouillon", label: "Brouillon (provisoire)" },
  { value: "emise", label: "À encaisser (émise)" },
  { value: "en_retard", label: "En retard" },
  { value: "payee", label: "Payée" },
  { value: "annulee", label: "Annulée" },
];
const TYPE_FILTRES: { value: string; label: string }[] = [
  { value: "", label: "Tous les types" },
  { value: "acompte", label: "Acompte" },
  { value: "solde", label: "Solde" },
  { value: "maintenance", label: "Maintenance" },
];

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
  avoir: "Avoir",
};

// Boutons d'action selon le statut, conformes au droit :
// - brouillon  -> suppression (corbeille) possible
// - emise/payee/en_retard -> annulation par avoir uniquement
// - annulee    -> aucune action (document conserve)
function ActionsFacture({ f }: { f: Facture }) {
  if (f.statut === "brouillon") {
    return (
      <Link href={`/factures/confirmer?id=${f.id}&action=archiver`} className="ml-3 text-red-600 hover:underline font-medium">Supprimer</Link>
    );
  }
  if (f.type !== "avoir" && (f.statut === "emise" || f.statut === "payee" || f.statut === "en_retard")) {
    return (
      <Link href={`/factures/confirmer?id=${f.id}&action=annuler`} className="ml-3 text-orange-600 hover:underline font-medium">Annuler (avoir)</Link>
    );
  }
  return null;
}

const PAR_PAGE = 25;

export default async function FacturesPage(
  { searchParams }: { searchParams: Promise<{ archives?: string; suppr_msg?: string; q?: string; skip?: string; envoye?: string; client?: string; projet?: string; statut?: string; type?: string; a_relancer?: string }> }
) {
  const params = await searchParams;
  const aRelancer = params.a_relancer === "1";
  const corbeille = params.archives === "1";
  const q = (params.q || "").trim();
  const clientId = (params.client || "").trim();
  const projet = (params.projet || "").trim();
  const statut = (params.statut || "").trim();
  const type = (params.type || "").trim();
  const skip = Math.max(Number(params.skip) || 0, 0);

  const qs = new URLSearchParams();
  if (corbeille) qs.set("archives", "true");
  if (q) qs.set("q", q);
  if (clientId) qs.set("client_id", clientId);
  if (projet) qs.set("devis_id", projet);
  if (statut) qs.set("statut", statut);
  if (type) qs.set("type", type);
  if (aRelancer) qs.set("a_relancer", "true");
  qs.set("skip", String(skip));
  qs.set("limit", String(PAR_PAGE));

  let factures: Facture[] = [];
  try {
    factures = await serverFetch<Facture[]>(`/factures/?${qs.toString()}`);
  } catch {}

  // Garde-fou : l'envoi direct au client n'est propose que s'il est active dans Parametres.
  let envoiClientActif = false;
  try { envoiClientActif = (await serverFetch<{ envoi_client_actif: boolean }>("/parametres/")).envoi_client_actif; } catch {}

  // Donnees des filtres : tous les clients ; et, si un client est choisi, ses
  // projets (devis) pour le second menu deroulant.
  let clients: ClientOpt[] = [];
  try { clients = await serverFetch<ClientOpt[]>(`/clients/?limit=200`); } catch {}
  let projets: ProjetOpt[] = [];
  if (clientId) {
    try { projets = await serverFetch<ProjetOpt[]>(`/devis/?client_id=${clientId}&limit=200`); } catch {}
  }

  // Conserve tous les filtres actifs dans les liens de pagination.
  const baseParams = () => {
    const p = new URLSearchParams();
    if (corbeille) p.set("archives", "1");
    if (q) p.set("q", q);
    if (clientId) p.set("client", clientId);
    if (projet) p.set("projet", projet);
    if (statut) p.set("statut", statut);
    if (type) p.set("type", type);
    return p;
  };
  const lienPage = (nouveauSkip: number) => {
    const p = baseParams();
    if (nouveauSkip > 0) p.set("skip", String(nouveauSkip));
    const s = p.toString();
    return `/factures${s ? `?${s}` : ""}`;
  };
  const filtresActifs = !!(clientId || projet || statut || type || q);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
          {corbeille ? "Corbeille — factures" : aRelancer ? "Factures a relancer" : "Factures"} ({factures.length})
        </h1>
        <div className="flex flex-wrap gap-2">
          {corbeille ? (
            <Link href="/factures" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
              Retour aux factures
            </Link>
          ) : (
            <>
              {aRelancer ? (
                <Link href="/factures" className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
                  Toutes les factures
                </Link>
              ) : (
                <Link href="/factures?a_relancer=1" className="px-4 py-2.5 border border-amber-300 bg-amber-50 text-amber-800 rounded text-sm font-medium text-center">
                  A relancer
                </Link>
              )}
              <EnvoiGroupe factures={factures} envoiClientActif={envoiClientActif} />
              <a href={`/api/factures/export.xlsx${q ? `?q=${encodeURIComponent(q)}` : ""}`} className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded text-sm font-medium text-center">
                Export Excel
              </a>
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

      {params.envoye === "1" && (
        <div className="mb-4 rounded border border-green-200 bg-green-50 text-green-700 px-4 py-3 text-sm">
          Facture envoyee par email au client.
        </div>
      )}
      {params.envoye === "moi" && (
        <div className="mb-4 rounded border border-green-200 bg-green-50 text-green-700 px-4 py-3 text-sm">
          Facture envoyee sur votre adresse (a transferer).
        </div>
      )}
      {params.envoye === "relance" && (
        <div className="mb-4 rounded border border-green-200 bg-green-50 text-green-700 px-4 py-3 text-sm">
          Relance envoyee au client.
        </div>
      )}

      {/* Recherche + filtres (masques en corbeille) */}
      {corbeille ? (
        <form method="GET" className="mb-4 flex gap-2">
          <input type="hidden" name="archives" value="1" />
          <input type="search" name="q" defaultValue={q} placeholder="Rechercher (numero, objet)..."
            className="flex-1 border rounded px-3 py-2 text-sm" />
          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">Rechercher</button>
        </form>
      ) : (
        <form method="GET" className="mb-4 flex flex-wrap items-end gap-2">
          <div className="grow min-w-[180px]">
            <label className="block text-xs text-gray-400 mb-0.5">Recherche</label>
            <input type="search" name="q" defaultValue={q} placeholder="Numero, objet..."
              className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Client</label>
            <select name="client" defaultValue={clientId} className="border rounded px-2 py-2 text-sm">
              <option value="">Tous les clients</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.raison_sociale}</option>)}
            </select>
          </div>
          {clientId && (
            <div>
              <label className="block text-xs text-gray-400 mb-0.5">Projet (devis)</label>
              <select name="projet" defaultValue={projet} className="border rounded px-2 py-2 text-sm">
                <option value="">Tous les projets</option>
                {projets.map(p => <option key={p.id} value={p.id}>{p.reference}{p.offre_nom ? ` — ${p.offre_nom}` : ""}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Statut</label>
            <select name="statut" defaultValue={statut} className="border rounded px-2 py-2 text-sm">
              {STATUT_FILTRES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Type</label>
            <select name="type" defaultValue={type} className="border rounded px-2 py-2 text-sm">
              {TYPE_FILTRES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">Filtrer</button>
          {filtresActifs && <Link href="/factures" className="px-4 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">Effacer</Link>}
        </form>
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
                    {f.statut === "brouillon" ? (
                      <p className="font-mono text-sm font-medium text-gray-400">{f.numero} <span className="text-[10px]">(provisoire)</span></p>
                    ) : (
                      <p className="font-mono text-sm font-medium">{f.numero}</p>
                    )}
                    <p className="text-xs text-gray-500">{TYPE_LABELS[f.type] || f.type}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[f.statut] || "bg-gray-100 text-gray-700"}`}>
                      {f.statut}
                    </span>
                    {f.a_relancer && (
                      <p className="mt-1"><span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-100 text-red-700">A relancer{f.jours_retard ? ` (${f.jours_retard}j)` : ""}</span></p>
                    )}
                  </div>
                </div>
                {f.client && <p className="text-sm font-medium text-gray-800">{f.client}</p>}
                {f.projet_ref && (
                  <p className="text-[11px] text-gray-400 mb-1">
                    Projet : {f.devis_id ? <Link href={`/devis/detail?id=${f.devis_id}`} className="font-mono hover:underline">{f.projet_ref}</Link> : f.projet_ref}
                    {f.projet_nom ? ` · ${f.projet_nom}` : ""}
                  </p>
                )}
                <p className="text-sm text-gray-600 mb-2">{f.objet}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">{f.date_emission}</span>
                  <span className="font-semibold">{eur(f.total_ttc)}</span>
                </div>
                {corbeille ? (
                  <div className="mt-3 flex flex-col gap-2">
                    <form action={restaurerFacture}>
                      <input type="hidden" name="facture_id" value={f.id} />
                      <button type="submit" className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                        Restaurer
                      </button>
                    </form>
                    <Link href={`/factures/confirmer?id=${f.id}&action=definitif`} className="block w-full text-center px-3 py-2 border border-red-300 text-red-600 rounded text-sm font-medium">
                      Supprimer definitivement
                    </Link>
                  </div>
                ) : (
                  <div className="mt-3 flex flex-col gap-2">
                    {f.statut === "brouillon" && (
                      <Link href={`/factures/confirmer?id=${f.id}&action=emettre`}
                        className="block w-full text-center px-3 py-2 bg-green-700 text-white rounded text-sm font-medium">
                        Émettre (n° légal)
                      </Link>
                    )}
                    <a href={`/api/factures/${f.id}/document`} className="block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium">
                      Telecharger (PDF)
                    </a>
                    <form action={envoyerFacture}>
                      <input type="hidden" name="facture_id" value={f.id} />
                      <input type="hidden" name="retour" value="/factures" />
                      <details>
                        <summary className="cursor-pointer block w-full text-center px-3 py-2 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium list-none">
                          Envoyer par email&hellip;
                        </summary>
                        {f.dernier_envoi && (
                          <p className="mt-1 text-[11px] text-amber-700">
                            Deja envoyee le {envoiLabel(f.dernier_envoi, f.dernier_envoi_mode)}{f.nb_envois && f.nb_envois > 1 ? ` — ${f.nb_envois} envois` : ""}. Renvoyer ?
                          </p>
                        )}
                        <div className="mt-1 flex gap-2">
                          {envoiClientActif && (
                            <button type="submit" name="mode" value="client" className="flex-1 text-center px-3 py-2 bg-green-700 text-white rounded text-sm font-medium">
                              Au client{f.client ? ` (${f.client})` : ""}
                            </button>
                          )}
                          <button type="submit" name="mode" value="expediteur" className="flex-1 text-center px-3 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">
                            A moi
                          </button>
                        </div>
                      </details>
                    </form>
                    {f.a_relancer && (
                      <form action={relancerFacture}>
                        <input type="hidden" name="facture_id" value={f.id} />
                        <input type="hidden" name="retour" value={aRelancer ? "/factures?a_relancer=1" : "/factures"} />
                        <details>
                          <summary className="cursor-pointer block w-full text-center px-3 py-2 border border-red-300 text-red-600 rounded text-sm font-medium list-none">
                            Relancer le client&hellip;
                          </summary>
                          <div className="mt-1 flex gap-2">
                            {envoiClientActif && (
                              <button type="submit" name="mode" value="client" className="flex-1 text-center px-3 py-2 bg-red-600 text-white rounded text-sm font-medium">Au client</button>
                            )}
                            <button type="submit" name="mode" value="expediteur" className="flex-1 text-center px-3 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">A moi</button>
                          </div>
                        </details>
                      </form>
                    )}
                    {(f.statut === "emise" || f.statut === "en_retard") && (
                      <form action={marquerPayee}>
                        <input type="hidden" name="facture_id" value={f.id} />
                        <input type="hidden" name="retour" value={aRelancer ? "/factures?a_relancer=1" : "/factures"} />
                        <button type="submit" className="block w-full text-center px-3 py-2 border border-green-600 text-green-700 rounded text-sm font-medium">Marquer payee</button>
                      </form>
                    )}
                    {f.statut === "payee" && (
                      <form action={marquerImpayee}>
                        <input type="hidden" name="facture_id" value={f.id} />
                        <input type="hidden" name="retour" value="/factures" />
                        <button type="submit" className="block w-full text-center px-3 py-2 border border-gray-300 text-gray-500 rounded text-sm font-medium">Marquer impayee</button>
                      </form>
                    )}
                    {f.statut === "brouillon" && (
                      <Link href={`/factures/confirmer?id=${f.id}&action=archiver`} className="block w-full text-center px-3 py-2 border border-red-300 text-red-600 rounded text-sm font-medium">
                        Supprimer (corbeille)
                      </Link>
                    )}
                    {f.type !== "avoir" && (f.statut === "emise" || f.statut === "payee" || f.statut === "en_retard") && (
                      <Link href={`/factures/confirmer?id=${f.id}&action=annuler`} className="block w-full text-center px-3 py-2 border border-orange-300 text-orange-600 rounded text-sm font-medium">
                        Annuler (avoir)
                      </Link>
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
                  <th className="px-4 py-3 font-medium">Client</th>
                  <th className="px-4 py-3 font-medium">Projet</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium text-right">Total TTC</th>
                  <th className="px-4 py-3 font-medium">Statut</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {factures.map(f => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono font-medium align-top">
                      {f.statut === "brouillon" ? (
                        <span className="text-gray-400">{f.numero} <span className="text-[10px]">(provisoire)</span></span>
                      ) : f.numero}
                      <p className="text-[11px] text-gray-600 font-sans max-w-[220px] truncate">{f.objet}</p>
                    </td>
                    <td className="px-4 py-3 align-top">{f.client || "—"}</td>
                    <td className="px-4 py-3 align-top">
                      {f.projet_ref ? (
                        <>
                          {f.devis_id ? <Link href={`/devis/detail?id=${f.devis_id}`} className="font-mono text-[#1A355E] hover:underline">{f.projet_ref}</Link> : <span className="font-mono">{f.projet_ref}</span>}
                          {f.projet_nom && <p className="text-[11px] text-gray-400 max-w-[180px] truncate">{f.projet_nom}</p>}
                        </>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 align-top">{TYPE_LABELS[f.type] || f.type}</td>
                    <td className="px-4 py-3 text-gray-500 align-top">{f.date_emission}</td>
                    <td className="px-4 py-3 text-right font-medium">{eur(f.total_ttc)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUT_COLORS[f.statut] || "bg-gray-100 text-gray-700"}`}>
                        {f.statut}
                      </span>
                      {f.a_relancer && (
                        <p className="mt-1"><span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-100 text-red-700">A relancer{f.jours_retard ? ` (${f.jours_retard}j)` : ""}</span></p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap align-top">
                      {!corbeille && (f.statut === "emise" || f.statut === "en_retard") && (
                        <form action={marquerPayee} className="inline">
                          <input type="hidden" name="facture_id" value={f.id} />
                          <input type="hidden" name="retour" value={aRelancer ? "/factures?a_relancer=1" : "/factures"} />
                          <button type="submit" className="mr-3 text-green-700 hover:underline font-medium">Payee</button>
                        </form>
                      )}
                      {!corbeille && f.statut === "payee" && (
                        <form action={marquerImpayee} className="inline">
                          <input type="hidden" name="facture_id" value={f.id} />
                          <input type="hidden" name="retour" value="/factures" />
                          <button type="submit" className="mr-3 text-gray-500 hover:underline text-xs">impayee</button>
                        </form>
                      )}
                      {!corbeille && f.a_relancer && (
                        <form action={relancerFacture} className="inline">
                          <input type="hidden" name="facture_id" value={f.id} />
                          <input type="hidden" name="retour" value={aRelancer ? "/factures?a_relancer=1" : "/factures"} />
                          <details className="inline-block align-middle mr-3">
                            <summary className="cursor-pointer text-red-600 hover:underline font-medium list-none">Relancer</summary>
                            <span className="ml-2 inline-flex gap-2">
                              {envoiClientActif && (
                                <button type="submit" name="mode" value="client" className="bg-red-600 text-white px-2 py-0.5 rounded text-xs">au client</button>
                              )}
                              <button type="submit" name="mode" value="expediteur" className="border border-gray-300 text-gray-600 px-2 py-0.5 rounded text-xs">a moi</button>
                            </span>
                          </details>
                        </form>
                      )}
                      {corbeille ? (
                        <>
                          <form action={restaurerFacture} className="inline">
                            <input type="hidden" name="facture_id" value={f.id} />
                            <button type="submit" className="text-[#1A355E] hover:underline font-medium">Restaurer</button>
                          </form>
                          <Link href={`/factures/confirmer?id=${f.id}&action=definitif`} className="ml-3 text-red-600 hover:underline font-medium">Supprimer def.</Link>
                        </>
                      ) : (
                        <>
                          {f.statut === "brouillon" && (
                            <Link href={`/factures/confirmer?id=${f.id}&action=emettre`}
                              className="mr-3 inline-block bg-green-700 text-white px-2 py-1 rounded text-xs font-medium">Émettre (n° légal)</Link>
                          )}
                          <a href={`/api/factures/${f.id}/document`} className="text-[#1A355E] hover:underline font-medium">
                            Telecharger
                          </a>
                          <form action={envoyerFacture} className="inline">
                            <input type="hidden" name="facture_id" value={f.id} />
                            <input type="hidden" name="retour" value="/factures" />
                            <details className="inline-block align-middle ml-3">
                              <summary className={`cursor-pointer hover:underline font-medium list-none ${f.dernier_envoi ? "text-amber-700" : "text-[#1A355E]"}`}>
                                Envoyer{f.dernier_envoi ? " *" : ""}
                              </summary>
                              <div className="mt-1">
                                {f.dernier_envoi && (
                                  <p className="text-[11px] text-amber-700 mb-1">Deja envoyee le {envoiLabel(f.dernier_envoi, f.dernier_envoi_mode)}{f.nb_envois && f.nb_envois > 1 ? ` — ${f.nb_envois} envois` : ""}. Renvoyer ?</p>
                                )}
                                <span className="inline-flex gap-2">
                                  {envoiClientActif && (
                                    <button type="submit" name="mode" value="client" className="bg-green-700 text-white px-2 py-0.5 rounded text-xs">au client</button>
                                  )}
                                  <button type="submit" name="mode" value="expediteur" className="border border-gray-300 text-gray-600 px-2 py-0.5 rounded text-xs">a moi</button>
                                </span>
                              </div>
                            </details>
                          </form>
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

      {/* Pagination */}
      {(skip > 0 || factures.length === PAR_PAGE) && (
        <div className="mt-4 flex items-center justify-between text-sm">
          {skip > 0 ? (
            <Link href={lienPage(Math.max(skip - PAR_PAGE, 0))} className="px-4 py-2 border border-gray-300 rounded font-medium">&larr; Precedent</Link>
          ) : <span />}
          <span className="text-gray-400">Page {Math.floor(skip / PAR_PAGE) + 1}</span>
          {factures.length === PAR_PAGE ? (
            <Link href={lienPage(skip + PAR_PAGE)} className="px-4 py-2 border border-gray-300 rounded font-medium">Suivant &rarr;</Link>
          ) : <span />}
        </div>
      )}
    </div>
  );
}
