import { serverFetch, type Offre } from "@/lib/api";
import { runSimulation } from "@/lib/actions";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

const PLANS = ["100%", "50/50", "50/25/25", "25/25/25/25"];
const DUREES = ["8 T (2 ans)", "12 T (3 ans)", "16 T (4 ans)", "20 T (5 ans)", "28 T (7 ans)"];

interface OptionWithStatut {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: string; vente_mensuel: string; setup_achat: string; mensuel_achat: string;
  statut: string; commentaire: string | null; ordre: number;
}

interface SimResult {
  prix_vente_final: string; prix_setup_affiche: string; prix_mensuel_affiche: string;
  total_setup_ht: string; total_setup_tva: string; total_setup_ttc: string;
  total_mensuel_ht: string; total_mensuel_tva: string; total_mensuel_ttc: string;
  total_prestations_vente: string; total_options_setup_vente: string;
  total_pack_maintenance_vente: string; total_options_recurrent_vente: string;
  remise_eur_setup: string; remise_eur_recurrent: string;
  marge: string; marge_totale: string;
  montant_finance: string; loyer: string; loyer_client_ht: string;
  prelevement_1: string; prelevement_2: string; prelevement_3: string; prelevement_4: string;
  recurrent_mensuel: string;
}

export default async function SimulateurPage({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const params = await searchParams;

  let offres: Offre[] = [];
  let options: OptionWithStatut[] = [];
  let error = "";

  try {
    offres = await serverFetch<Offre[]>("/offres/");
  } catch (e) {
    error = String(e);
  }

  const offreId = params.offre_id;
  const selectedOffre = offreId ? offres.find(o => o.id === Number(offreId)) : null;
  const mode = params.mode || "Comptant";
  const plan = params.plan || "100%";

  // Charger les options si une offre est selectionnee
  if (selectedOffre) {
    try {
      options = await serverFetch<OptionWithStatut[]>(`/offres/${selectedOffre.id}/options`);
    } catch (e) {
      error = String(e);
    }
  }

  // Resultat de simulation (encode dans l'URL par la Server Action)
  let result: SimResult | null = null;
  if (params.result) {
    try {
      result = JSON.parse(decodeURIComponent(params.result));
    } catch { /* ignore */ }
  }

  // Grouper les options par categorie
  const categories = new Map<string, OptionWithStatut[]>();
  for (const opt of options) {
    const cat = opt.categorie;
    if (!categories.has(cat)) categories.set(cat, []);
    categories.get(cat)!.push(opt);
  }

  // Separer packs maintenance des autres options
  const packs = options.filter(o => o.type_ligne === "PACK");
  const otherOptions = options.filter(o => o.type_ligne !== "PACK");
  const otherCategories = new Map<string, OptionWithStatut[]>();
  for (const opt of otherOptions) {
    const cat = opt.categorie;
    if (!otherCategories.has(cat)) otherCategories.set(cat, []);
    otherCategories.get(cat)!.push(opt);
  }

  if (error && !offres.length) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Simulateur de prix</h1>

      <form action={runSimulation} className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-5 lg:gap-6">
        {/* Colonne gauche : formulaire (3/5) */}
        <div className="lg:col-span-3 space-y-4">

          {/* Section 1 : Offre + Mode */}
          <div className="bg-white border rounded-lg p-4 space-y-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Offre et mode</h2>
            <div>
              <label className="block text-sm font-medium mb-1">Offre</label>
              <select name="offre_id" defaultValue={offreId || ""} required
                className="w-full border rounded px-3 py-2.5 text-sm">
                <option value="">Choisir une offre...</option>
                {offres.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.nom} ({o.type_site}) - {eur(o.tarif_vente_conseille)}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Mode</label>
                <select name="mode" defaultValue={mode} className="w-full border rounded px-3 py-2.5 text-sm">
                  <option>Comptant</option>
                  <option>Leasing</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Plan paiement</label>
                <select name="plan" defaultValue={plan} className="w-full border rounded px-3 py-2.5 text-sm">
                  {PLANS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Remise setup %</label>
                <input name="remise_setup" type="number" inputMode="decimal" min={0} max={100}
                  defaultValue={params.remise_setup || "0"} className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Remise recurrent %</label>
                <input name="remise_recurrent" type="number" inputMode="decimal" min={0} max={100}
                  defaultValue={params.remise_recurrent || "0"} className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Marge add.</label>
                <input name="marge_add" type="number" inputMode="decimal"
                  defaultValue={params.marge_add || "0"} className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
            </div>
          </div>

          {/* Section 2 : Leasing */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Parametres leasing</h2>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Duree financement</label>
                <select name="duree_financement" defaultValue="" className="w-full border rounded px-3 py-2.5 text-sm">
                  <option value="">-</option>
                  {DUREES.map((d) => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Coefficient Locam</label>
                <input name="coefficient_locam" type="number" inputMode="decimal" step="0.01"
                  defaultValue="3.20" className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">% Maintenance Locam</label>
                <input name="pct_maintenance" type="number" inputMode="decimal" min={0} max={100}
                  defaultValue="30" className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Garantie web (EUR/mois)</label>
                <input name="garantie_web" type="number" inputMode="decimal" step="0.01"
                  defaultValue="10" className="w-full border rounded px-3 py-2.5 text-sm" />
              </div>
            </div>
          </div>

          {/* Section 3 : Prestations sur mesure */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Prestations sur mesure</h2>
            {[1, 2, 3].map((i) => (
              <div key={i} className="grid grid-cols-4 gap-2">
                <div className="col-span-4 sm:col-span-1">
                  <input name={`presta_${i}_nom`} placeholder={`Prestation ${i}`}
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <input name={`presta_${i}_qty`} type="number" inputMode="numeric" placeholder="Qte" min={0}
                    defaultValue="0" className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <input name={`presta_${i}_achat`} type="number" inputMode="decimal" step="0.01" placeholder="PU achat"
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <input name={`presta_${i}_vente`} type="number" inputMode="decimal" step="0.01" placeholder="PU vente"
                    className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              </div>
            ))}
          </div>

          {/* Section 4 : Pack maintenance */}
          {packs.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-3">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Pack maintenance</h2>
              <p className="text-xs text-gray-400">Selectionnez un seul pack (ou aucun).</p>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                  <input type="radio" name="pack_id" value="" defaultChecked className="accent-[#1A355E]" />
                  <span className="text-sm text-gray-500">Aucun pack</span>
                </label>
                {packs.map((p) => (
                  <label key={p.id} className="flex items-center justify-between gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                    <div className="flex items-center gap-3">
                      <input type="radio" name="pack_id" value={p.id} className="accent-[#1A355E]" />
                      <div>
                        <span className="text-sm font-medium">{p.nom}</span>
                        {p.commentaire && <p className="text-xs text-gray-400">{p.commentaire}</p>}
                      </div>
                    </div>
                    <span className="text-sm font-medium shrink-0">{eur(p.vente_mensuel)}/mois</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Section 5 : Options */}
          {otherOptions.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Options</h2>
              {Array.from(otherCategories.entries()).map(([cat, opts]) => (
                <div key={cat}>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{cat}</h3>
                  <div className="space-y-1">
                    {opts.map((o) => {
                      const isInclus = o.statut === "Inclus";
                      const prix = o.type_ligne === "OPTION_SETUP" ? o.vente_setup : o.vente_mensuel;
                      const unite = o.type_ligne === "OPTION_SETUP" ? "" : "/mois";
                      return (
                        <div key={o.id} className={`flex items-center justify-between gap-2 p-2 rounded text-sm ${isInclus ? "bg-green-50" : ""}`}>
                          <div className="flex-1 min-w-0">
                            <span className={isInclus ? "text-green-800" : ""}>{o.nom}</span>
                            {isInclus && <span className="ml-2 text-xs text-green-600 font-medium">Inclus</span>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-xs text-gray-400">{Number(prix) > 0 ? `${eur(prix)}${unite}` : ""}</span>
                            {isInclus ? (
                              <input type="hidden" name={`opt_${o.id}`} value="1" />
                            ) : (
                              <select name={`opt_${o.id}`} defaultValue="0"
                                className="w-16 border rounded px-2 py-1 text-sm text-center">
                                {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
                              </select>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Bouton simuler */}
          <button type="submit"
            className="w-full py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            Simuler
          </button>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        {/* Colonne droite : resultats (2/5) */}
        <div className="lg:col-span-2">
          <div className="bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4">
            <h2 className="text-lg font-semibold mb-4">Resultats</h2>
            {!result ? (
              <p className="text-gray-400 text-sm">Selectionnez une offre et cliquez Simuler.</p>
            ) : (
              <div className="space-y-3 text-sm">
                <Section title="Prix">
                  <Row label="Prix vente final HT" value={eur(result.prix_vente_final)} bold />
                  <Row label="Setup affiche HT" value={eur(result.prix_setup_affiche)} />
                  <Row label="Mensuel affiche HT" value={eur(result.prix_mensuel_affiche)} />
                </Section>
                <Section title="Totaux TTC">
                  <Row label="Setup TTC" value={eur(result.total_setup_ttc)} bold />
                  <Row label="Mensuel TTC" value={eur(result.total_mensuel_ttc)} />
                </Section>
                {(Number(result.total_prestations_vente) > 0 || Number(result.total_options_setup_vente) > 0) && (
                  <Section title="Detail">
                    {Number(result.total_prestations_vente) > 0 && <Row label="Prestations sur mesure" value={eur(result.total_prestations_vente)} />}
                    {Number(result.total_options_setup_vente) > 0 && <Row label="Options setup" value={eur(result.total_options_setup_vente)} />}
                    {Number(result.total_pack_maintenance_vente) > 0 && <Row label="Pack maintenance" value={eur(result.total_pack_maintenance_vente)} />}
                    {Number(result.total_options_recurrent_vente) > 0 && <Row label="Options recurrentes" value={eur(result.total_options_recurrent_vente)} />}
                  </Section>
                )}
                <Section title="Remises">
                  <Row label="Remise setup" value={eur(result.remise_eur_setup)} />
                  <Row label="Remise recurrent" value={eur(result.remise_eur_recurrent)} />
                </Section>
                <Section title="Marge">
                  <Row label="Marge" value={eur(result.marge)} />
                  <Row label="Marge totale" value={eur(result.marge_totale)} bold />
                </Section>
                {mode === "Comptant" && Number(result.prelevement_1) > 0 && (
                  <Section title="Plan de paiement">
                    <Row label="Prelevement 1" value={eur(result.prelevement_1)} />
                    {Number(result.prelevement_2) > 0 && <Row label="Prelevement 2" value={eur(result.prelevement_2)} />}
                    {Number(result.prelevement_3) > 0 && <Row label="Prelevement 3" value={eur(result.prelevement_3)} />}
                    {Number(result.prelevement_4) > 0 && <Row label="Prelevement 4" value={eur(result.prelevement_4)} />}
                    {Number(result.recurrent_mensuel) > 0 && <Row label="Recurrent mensuel" value={eur(result.recurrent_mensuel)} />}
                  </Section>
                )}
                {mode === "Leasing" && Number(result.loyer) > 0 && (
                  <Section title="Leasing">
                    <Row label="Montant finance" value={eur(result.montant_finance)} />
                    <Row label="Loyer" value={eur(result.loyer)} />
                    <Row label="Loyer client HT" value={eur(result.loyer_client_ht)} bold />
                  </Section>
                )}
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t pt-3">
      <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{title}</h3>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-gray-600">{label}</span>
      <span className={`text-right shrink-0 ${bold ? "font-semibold" : ""}`}>{value}</span>
    </div>
  );
}
