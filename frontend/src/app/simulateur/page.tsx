import { serverFetch, serverPost, type Offre, type Client } from "@/lib/api";
import { runSimulation, saveDevis } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}
function N(v: string | undefined) { return Number(v || 0); }

const PLANS = ["100%", "50/50", "33/33/33", "50/25/25", "25/25/25/25"];
const DUREES = ["8 T (2 ans)", "12 T (3 ans)", "16 T (4 ans)", "20 T (5 ans)", "28 T (7 ans)"];

interface OptS {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: string; vente_mensuel: string; setup_achat: string; mensuel_achat: string;
  statut: string; commentaire: string | null;
}

// Ligne du recapitulatif du devis (panier) affichee dans les resultats.
interface RecapLigne {
  nom: string;
  detail?: string;   // ex "2 x 95,00 EUR"
  montant: number;   // total de la ligne (brut)
  recurrent: boolean; // true => /mois (abonnement)
  inclus: boolean;    // option incluse dans l'offre (0 EUR)
  offert: boolean;    // ligne offerte (deduite du total)
}

type Result = Record<string, string>;

export default async function SimulateurPage({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const p = await searchParams;

  let offres: Offre[] = [];
  let clients: Client[] = [];
  let options: OptS[] = [];
  let error = "";
  let result: Result | null = null;

  try { offres = await serverFetch<Offre[]>("/offres/"); } catch (e) { error = String(e); }
  try { clients = await serverFetch<Client[]>("/clients/"); } catch {}

  const offreId = p.offre_id || "";
  const offre = offreId ? offres.find(o => String(o.id) === offreId) : null;
  const mode = p.mode || "Comptant";
  const plan = p.plan || "100%";

  if (offre) {
    try { options = await serverFetch<OptS[]>(`/offres/${offre.id}/options`); } catch (e) { error = String(e); }
  }

  if (p.result) {
    try { result = JSON.parse(decodeURIComponent(p.result)); } catch {}
  }

  const packs = options.filter(o => o.type_ligne === "PACK");
  const others = options.filter(o => o.type_ligne !== "PACK");
  const cats = new Map<string, OptS[]>();
  for (const o of others) { if (!cats.has(o.categorie)) cats.set(o.categorie, []); cats.get(o.categorie)!.push(o); }

  // Articles offerts : reconstruits depuis l'etat URL (options/prestations cochees "Offrir").
  // est_setup = false => recurrent (mensuel), exceptionnel => garde-fou.
  const articlesOfferts: Array<{ designation: string; prix_achat: string; prix_vente: string; est_setup: boolean }> = [];
  for (const o of others) {
    const qty = o.statut === "Inclus" ? 1 : Number(p[`opt_${o.id}`] || "0");
    if (qty > 0 && p[`offrir_${o.id}`] === "1") {
      const est_setup = o.type_ligne === "OPTION_SETUP";
      articlesOfferts.push({
        designation: o.nom,
        prix_achat: String(Number(est_setup ? o.setup_achat : o.mensuel_achat) * qty),
        prix_vente: String(Number(est_setup ? o.vente_setup : o.vente_mensuel) * qty),
        est_setup,
      });
    }
  }
  for (const pk of packs) {
    if (p.pack_id === String(pk.id) && p[`offrir_${pk.id}`] === "1") {
      articlesOfferts.push({
        designation: pk.nom,
        prix_achat: String(Number(pk.mensuel_achat)),
        prix_vente: String(Number(pk.vente_mensuel)),
        est_setup: false,
      });
    }
  }
  for (let i = 1; i <= 3; i++) {
    const nom = p[`presta_${i}_nom`];
    const qty = Number(p[`presta_${i}_qty`] || "0");
    const pv = Number(p[`presta_${i}_vente`] || "0");
    if (nom && qty > 0 && pv > 0 && p[`offrir_presta_${i}`] === "1") {
      articlesOfferts.push({
        designation: nom,
        prix_achat: String(Number(p[`presta_${i}_achat`] || "0") * qty),
        prix_vente: String(pv * qty),
        est_setup: true,
      });
    }
  }
  const offertsRecurrent = articlesOfferts.filter(a => !a.est_setup);

  // Recapitulatif du devis (panier) : reconstruit ligne par ligne depuis l'etat URL,
  // pour que l'utilisateur voie exactement ce qui est dans le devis sans remonter
  // dans la liste des options. Les lignes offertes sont marquees (barrees + "Offert").
  const recap: RecapLigne[] = [];
  if (offre) {
    recap.push({
      nom: offre.nom, montant: Number(offre.tarif_vente_conseille),
      recurrent: false, inclus: false, offert: false,
    });
  }
  for (let i = 1; i <= 3; i++) {
    const nom = p[`presta_${i}_nom`];
    const qty = N(p[`presta_${i}_qty`]);
    const pv = N(p[`presta_${i}_vente`]);
    if (nom && qty > 0 && pv > 0) {
      recap.push({
        nom, detail: qty > 1 ? `${qty} x ${eur(pv)}` : undefined, montant: qty * pv,
        recurrent: false, inclus: false, offert: p[`offrir_presta_${i}`] === "1",
      });
    }
  }
  for (const o of others) {
    const incl = o.statut === "Inclus";
    const qty = incl ? 1 : N(p[`opt_${o.id}`]);
    if (qty <= 0) continue;
    const est_setup = o.type_ligne === "OPTION_SETUP";
    const pu = Number(est_setup ? o.vente_setup : o.vente_mensuel);
    recap.push({
      nom: o.nom, detail: qty > 1 ? `${qty} x ${eur(pu)}` : undefined, montant: pu * qty,
      recurrent: !est_setup, inclus: incl, offert: p[`offrir_${o.id}`] === "1",
    });
  }
  for (const pk of packs) {
    if (p.pack_id === String(pk.id)) {
      recap.push({
        nom: pk.nom, montant: Number(pk.vente_mensuel),
        recurrent: true, inclus: false, offert: p[`offrir_${pk.id}`] === "1",
      });
    }
  }
  const recapSetup = recap.filter(l => !l.recurrent);
  const recapRecurrent = recap.filter(l => l.recurrent);

  if (error && !offres.length) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  // Si pas d'offre selectionnee : formulaire de selection
  if (!offre) {
    return (
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Simulateur de prix</h1>
        <form method="GET" action="/simulateur" className="bg-white border rounded-lg p-4 sm:p-6 max-w-lg space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Choisissez une offre</label>
            <select name="offre_id" required className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="">-- Selectionnez --</option>
              {offres.map(o => (
                <option key={o.id} value={o.id}>{o.nom} ({o.type_site}) - {eur(o.tarif_vente_conseille)}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="w-full py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            Charger les options
          </button>
        </form>
      </div>
    );
  }

  // Offre selectionnee : formulaire complet
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Simulateur de prix</h1>
        <Link href="/simulateur" className="px-3 py-2 text-sm text-gray-500 border rounded hover:bg-gray-50">
          Changer d&apos;offre
        </Link>
      </div>

      {/* Info offre */}
      <div className="bg-[#1A355E] text-white rounded-lg p-4 mb-4">
        <h2 className="font-semibold">{offre.nom}</h2>
        <div className="flex gap-4 text-sm mt-1 text-white/70">
          <span>{offre.type_site}</span>
          <span>{eur(offre.tarif_vente_conseille)} HT</span>
          <span>{offre.pages} pages</span>
          <span>{offre.heures} h</span>
        </div>
      </div>

      <form action={runSimulation} className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-5 lg:gap-6">
        <div className="lg:col-span-3 space-y-4">
          <input type="hidden" name="offre_id" value={offre.id} />

          {/* Mode + Remises */}
          <div className="bg-white border rounded-lg p-4 space-y-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Mode et remises</h2>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium mb-1">Mode</label>
                <select name="mode" defaultValue={mode} className="w-full border rounded px-3 py-2.5 text-sm">
                  <option>Comptant</option><option>Leasing</option></select></div>
              <div><label className="block text-sm font-medium mb-1">Plan paiement</label>
                <select name="plan" defaultValue={plan} className="w-full border rounded px-3 py-2.5 text-sm">
                  {PLANS.map(v => <option key={v}>{v}</option>)}</select></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><label className="block text-sm font-medium mb-1">Remise setup %</label>
                <input name="remise_setup" type="number" inputMode="decimal" min={0} max={100} defaultValue={p.remise_setup || "0"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Remise recur. %</label>
                <input name="remise_recurrent" type="number" inputMode="decimal" min={0} max={100} defaultValue={p.remise_recurrent || "0"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Marge add.</label>
                <input name="marge_add" type="number" inputMode="decimal" defaultValue={p.marge_add || "0"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
            </div>
          </div>

          {/* Leasing */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Parametres leasing</h2>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium mb-1">Duree</label>
                <select name="duree_financement" defaultValue={p.duree_financement || ""} className="w-full border rounded px-3 py-2.5 text-sm">
                  <option value="">-</option>{DUREES.map(d => <option key={d}>{d}</option>)}</select></div>
              <div><label className="block text-sm font-medium mb-1">Coeff. Locam</label>
                <input name="coefficient_locam" type="number" inputMode="decimal" step="0.01" defaultValue={p.coefficient_locam || "3.20"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">% Maintenance</label>
                <input name="pct_maintenance" type="number" inputMode="decimal" min={0} max={100} defaultValue={p.pct_maintenance || "30"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Garantie web</label>
                <input name="garantie_web" type="number" inputMode="decimal" step="0.01" defaultValue={p.garantie_web || "10"} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
            </div>
          </div>

          {/* Prestations sur mesure */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Prestations sur mesure</h2>
            {[1, 2, 3].map(i => {
              const presObert = p[`offrir_presta_${i}`] === "1";
              const presRempli = !!p[`presta_${i}_nom`];
              return (
              <div key={i} className="space-y-1">
                <div className="grid grid-cols-4 gap-2">
                  <div className="col-span-4 sm:col-span-1">
                    <input name={`presta_${i}_nom`} placeholder={`Prestation ${i}`} defaultValue={p[`presta_${i}_nom`] || ""} className="w-full border rounded px-3 py-2 text-sm" /></div>
                  <input name={`presta_${i}_qty`} type="number" inputMode="numeric" placeholder="Qte" min={0} defaultValue={p[`presta_${i}_qty`] || "0"} className="w-full border rounded px-3 py-2 text-sm" />
                  <input name={`presta_${i}_achat`} type="number" inputMode="decimal" step="0.01" placeholder="PU achat" defaultValue={p[`presta_${i}_achat`] || ""} className="w-full border rounded px-3 py-2 text-sm" />
                  <input name={`presta_${i}_vente`} type="number" inputMode="decimal" step="0.01" placeholder="PU vente" defaultValue={p[`presta_${i}_vente`] || ""} className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                {presRempli && (
                  <label className="flex items-center gap-1 text-xs text-amber-600 cursor-pointer" title="Offrir cette prestation (one-shot)">
                    <input type="checkbox" name={`offrir_presta_${i}`} value="1" defaultChecked={presObert} className="accent-amber-500" />
                    Offrir cette prestation
                  </label>
                )}
              </div>);
            })}
          </div>

          {/* Pack maintenance */}
          {packs.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-3">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Pack maintenance</h2>
              <div className="space-y-2">
                <label className={`flex items-center gap-3 p-2 rounded cursor-pointer ${!p.pack_id ? "bg-gray-50" : "hover:bg-gray-50"}`}>
                  <input type="radio" name="pack_id" value="" defaultChecked={!p.pack_id} className="accent-[#1A355E]" />
                  <span className="text-sm text-gray-500">Aucun pack</span></label>
                {packs.map(pk => {
                  const sel = p.pack_id === String(pk.id);
                  const offert = p[`offrir_${pk.id}`] === "1";
                  return (
                    <div key={pk.id} className={`flex items-center justify-between gap-3 p-2 rounded ${sel ? "bg-blue-50 border border-blue-200" : "hover:bg-gray-50"}`}>
                      <label className="flex items-center gap-3 cursor-pointer flex-1 min-w-0">
                        <input type="radio" name="pack_id" value={pk.id} defaultChecked={sel} className="accent-[#1A355E]" />
                        <div><span className={`text-sm font-medium ${sel ? "text-blue-900" : ""}`}>{pk.nom}</span>
                          {offert && <span className="ml-2 text-xs text-red-600 font-medium">Offert</span>}
                          {pk.commentaire && <p className="text-xs text-gray-400">{pk.commentaire}</p>}</div>
                      </label>
                      <div className="flex items-center gap-3 shrink-0">
                        {sel && (
                          <label className="flex items-center gap-1 text-xs text-red-600 cursor-pointer"
                            title="Offrir le pack en RECURRENT (mensuel) — exceptionnel">
                            <input type="checkbox" name={`offrir_${pk.id}`} value="1" defaultChecked={offert} className="accent-red-600" />
                            Offrir (recur.)
                          </label>
                        )}
                        <span className="text-sm font-medium">{eur(pk.vente_mensuel)}/mois</span>
                      </div>
                    </div>);
                })}
              </div>
            </div>
          )}

          {/* Options */}
          {others.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Options ({others.length})</h2>
              {Array.from(cats.entries()).map(([cat, opts]) => (
                <div key={cat}>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{cat}</h3>
                  <div className="space-y-1">
                    {opts.map(o => {
                      const incl = o.statut === "Inclus";
                      const savedQty = p[`opt_${o.id}`] || "0";
                      const sel = Number(savedQty) > 0;
                      const recurrent = o.type_ligne !== "OPTION_SETUP";
                      const offert = p[`offrir_${o.id}`] === "1";
                      const prix = o.type_ligne === "OPTION_SETUP" ? o.vente_setup : o.vente_mensuel;
                      const u = o.type_ligne === "OPTION_SETUP" ? "" : "/mois";
                      const bg = incl ? "bg-green-50" : sel ? "bg-blue-50 border border-blue-200" : "";
                      return (
                        <div key={o.id} className={`flex items-center justify-between gap-2 p-2 rounded text-sm ${bg}`}>
                          <div className="flex-1 min-w-0">
                            <span className={incl ? "text-green-800" : sel ? "text-blue-900 font-medium" : ""}>{o.nom}</span>
                            {incl && <span className="ml-2 text-xs text-green-600 font-medium">Inclus</span>}
                            {offert && <span className={`ml-2 text-xs font-medium ${recurrent ? "text-red-600" : "text-amber-600"}`}>Offert</span>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {/* Case "Offrir" : visible une fois l'option selectionnee (apres un Simuler) */}
                            {sel && !incl && (
                              <label className={`flex items-center gap-1 text-xs cursor-pointer ${recurrent ? "text-red-600" : "text-gray-500"}`}
                                title={recurrent ? "Offrir en RECURRENT (mensuel) — exceptionnel" : "Offrir (one-shot)"}>
                                <input type="checkbox" name={`offrir_${o.id}`} value="1" defaultChecked={offert}
                                  className={recurrent ? "accent-red-600" : "accent-amber-500"} />
                                Offrir{recurrent ? " (recur.)" : ""}
                              </label>
                            )}
                            <span className="text-xs text-gray-400">{N(prix) > 0 ? `${eur(prix)}${u}` : ""}</span>
                            {incl ? (
                              <input type="hidden" name={`opt_${o.id}`} value="1" />
                            ) : (
                              <select name={`opt_${o.id}`} defaultValue={savedQty}
                                className={`w-16 border rounded px-2 py-1 text-sm text-center ${sel ? "border-blue-300 bg-blue-50 font-medium" : ""}`}>
                                {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
                              </select>
                            )}
                          </div>
                        </div>);
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Boutons */}
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">Simuler</button>
            <Link href="/simulateur" className="px-6 py-3 bg-gray-100 text-gray-600 rounded-lg text-sm text-center">Reset</Link>
          </div>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        {/* Resultats */}
        <div className="lg:col-span-2">
          <div className="bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4">
            <h2 className="text-lg font-semibold mb-4">Resultats</h2>
            {!result ? <p className="text-gray-400 text-sm">Cliquez Simuler pour voir les resultats.</p> : (
              <div className="space-y-3 text-sm">
                {recap.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Recapitulatif du devis</h3>
                    {recapSetup.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-[11px] font-semibold text-gray-400 uppercase">Prestation initiale (one-shot)</p>
                        {recapSetup.map((l, i) => <LigneRecap key={`s${i}`} l={l} />)}
                      </div>
                    )}
                    {recapRecurrent.length > 0 && (
                      <div className="space-y-1 mt-3">
                        <p className="text-[11px] font-semibold text-gray-400 uppercase">Abonnement mensuel</p>
                        {recapRecurrent.map((l, i) => <LigneRecap key={`r${i}`} l={l} />)}
                      </div>
                    )}
                  </div>
                )}
                <Sec t="Totaux nets">
                  <R l="Setup affiche HT" v={eur(result.prix_setup_affiche)} b />
                  <R l="Setup TTC" v={eur(result.total_setup_ttc)} b />
                  {N(result.prix_mensuel_affiche) > 0 && <R l="Mensuel affiche HT" v={eur(result.prix_mensuel_affiche)} />}
                  {N(result.total_mensuel_ttc) > 0 && <R l="Mensuel TTC" v={eur(result.total_mensuel_ttc)} />}
                </Sec>
                <Sec t="Remises"><R l="Remise setup" v={eur(result.remise_eur_setup)} /><R l="Remise recurrent" v={eur(result.remise_eur_recurrent)} /></Sec>
                <Sec t="Marge"><R l="Marge" v={eur(result.marge)} /><R l="Marge totale" v={eur(result.marge_totale)} b /></Sec>
                {mode === "Comptant" && N(result.prelevement_1) > 0 && (
                  <Sec t="Plan de paiement (TTC)">
                    <R l="Prelevement 1" v={eur(result.prelevement_1)} />
                    {N(result.prelevement_2) > 0 && <R l="Prelevement 2" v={eur(result.prelevement_2)} />}
                    {N(result.prelevement_3) > 0 && <R l="Prelevement 3" v={eur(result.prelevement_3)} />}
                    {N(result.prelevement_4) > 0 && <R l="Prelevement 4" v={eur(result.prelevement_4)} />}
                    {N(result.recurrent_mensuel) > 0 && <R l="Recurrent mensuel" v={eur(result.recurrent_mensuel)} />}
                  </Sec>)}
                {mode === "Leasing" && N(result.loyer) > 0 && (
                  <Sec t="Leasing">
                    <R l="Montant finance" v={eur(result.montant_finance)} />
                    <R l="Loyer" v={eur(result.loyer)} />
                    <R l="Loyer client HT" v={eur(result.loyer_client_ht)} b />
                  </Sec>)}
                {offertsRecurrent.length > 0 && (
                  <div className="border-2 border-red-300 bg-red-50 rounded-lg p-3">
                    <p className="text-sm font-semibold text-red-700">Attention : vous offrez du RECURRENT (mensuel)</p>
                    <p className="text-xs text-red-600 mt-1">
                      {offertsRecurrent.map(a => a.designation).join(", ")} — soit {eur(offertsRecurrent.reduce((s, a) => s + Number(a.prix_vente), 0))}/mois deduits du revenu recurrent. C&apos;est exceptionnel : verifiez que c&apos;est intentionnel.
                    </p>
                  </div>)}
              </div>
            )}
          </div>

          {/* Enregistrer le devis */}
          {result && (
            <div className="bg-white border-2 border-green-200 rounded-lg p-4 mt-4">
              <h2 className="text-sm font-semibold text-green-800 uppercase mb-3">Enregistrer ce devis</h2>
              <form action={saveDevis}>
                <input type="hidden" name="offre_id" value={offre.id} />
                <input type="hidden" name="mode" value={mode} />
                <input type="hidden" name="plan" value={plan} />
                <input type="hidden" name="remise_setup" value={p.remise_setup || "0"} />
                <input type="hidden" name="remise_recurrent" value={p.remise_recurrent || "0"} />
                <input type="hidden" name="marge_add" value={p.marge_add || "0"} />
                <input type="hidden" name="result_json" value={JSON.stringify(result)} />
                <input type="hidden" name="options_json" value={JSON.stringify(
                  options.filter(o => o.statut === "Inclus" || Number(p[`opt_${o.id}`] || "0") > 0 || (o.type_ligne === "PACK" && p.pack_id === String(o.id)))
                    .map(o => ({
                      option_id: o.id, code: o.code, nom: o.nom, type_ligne: o.type_ligne,
                      quantite: o.statut === "Inclus" ? 1 : (o.type_ligne === "PACK" ? 1 : Number(p[`opt_${o.id}`] || "0")),
                      statut: o.statut,
                      prix_vente_setup: o.vente_setup, prix_vente_mensuel: o.vente_mensuel,
                    }))
                )} />
                <input type="hidden" name="articles_offerts_json" value={JSON.stringify(articlesOfferts)} />
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-1">Client</label>
                  <select name="client_id" required className="w-full border rounded px-3 py-2.5 text-sm">
                    <option value="">-- Choisir le client --</option>
                    {clients.map(c => (
                      <option key={c.id} value={c.id}>{c.raison_sociale}{c.ville ? ` (${c.ville})` : ""}</option>
                    ))}
                  </select>
                </div>
                {offertsRecurrent.length > 0 && (
                  <label className="flex items-start gap-2 mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 cursor-pointer">
                    <input type="checkbox" name="confirme_recurrent" value="1" required className="mt-0.5 accent-red-600" />
                    <span>Je confirme offrir du RECURRENT (mensuel) : {offertsRecurrent.map(a => a.designation).join(", ")}.</span>
                  </label>
                )}
                <button type="submit" className="w-full py-3 bg-green-700 text-white rounded-lg font-medium text-sm">
                  Enregistrer le devis
                </button>
              </form>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

function Sec({ t, children }: { t: string; children: React.ReactNode }) {
  return (<div className="border-t pt-3"><h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{t}</h3><div className="space-y-1.5">{children}</div></div>);
}
function R({ l, v, b }: { l: string; v: string; b?: boolean }) {
  return (<div className="flex justify-between gap-2"><span className="text-gray-600">{l}</span><span className={`text-right shrink-0 ${b ? "font-semibold" : ""}`}>{v}</span></div>);
}
function LigneRecap({ l }: { l: RecapLigne }) {
  return (
    <div className="flex justify-between gap-2 items-baseline">
      <span className="text-gray-700 min-w-0">
        {l.nom}
        {l.detail && <span className="text-gray-400 text-xs"> ({l.detail})</span>}
        {l.inclus && <span className="ml-1 text-xs text-green-600 font-medium">Inclus</span>}
        {l.offert && <span className={`ml-1 text-xs font-medium ${l.recurrent ? "text-red-600" : "text-amber-600"}`}>Offert</span>}
      </span>
      <span className={`text-right shrink-0 ${l.offert ? "line-through text-gray-400" : l.inclus ? "text-green-600" : ""}`}>
        {l.inclus ? "compris" : `${eur(l.montant)}${l.recurrent ? "/mois" : ""}`}
      </span>
    </div>
  );
}
