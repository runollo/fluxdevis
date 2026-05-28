import { serverFetch, serverPost, type Offre } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

const PLANS = ["100%", "50/50", "50/25/25", "25/25/25/25"];

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
  let error = "";
  let result: SimResult | null = null;

  try {
    offres = await serverFetch<Offre[]>("/offres/");
  } catch (e) {
    error = String(e);
  }

  // Si on a des params de simulation, lancer le calcul
  const offreId = params.offre_id;
  const selectedOffre = offreId ? offres.find(o => o.id === Number(offreId)) : null;
  const mode = params.mode || "Comptant";
  const plan = params.plan || "100%";
  const remiseSetup = params.remise_setup || "0";
  const remiseRecurrent = params.remise_recurrent || "0";
  const margeAdd = params.marge_add || "0";

  if (selectedOffre && params.simuler) {
    try {
      result = await serverPost<SimResult>("/simulation/", {
        offre_nom: selectedOffre.nom,
        offre_type_site: selectedOffre.type_site,
        prix_achat: String(selectedOffre.tarif_achat),
        prix_vente_conseille: String(selectedOffre.tarif_vente_conseille),
        mode_reglement: mode,
        plan_paiement: plan,
        remise_pct_setup: String(Number(remiseSetup) / 100),
        remise_pct_recurrent: String(Number(remiseRecurrent) / 100),
        marge_additionnelle: margeAdd,
      });
    } catch (e) {
      error = String(e);
    }
  }

  if (error && !offres.length) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Simulateur de prix</h1>
      <div className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-2 lg:gap-6">
        {/* Formulaire */}
        <form method="GET" action="/simulateur" className="bg-white border rounded-lg p-4 sm:p-5 space-y-4">
          <input type="hidden" name="simuler" value="1" />

          <div>
            <label className="block text-sm font-medium mb-1">Offre</label>
            <select name="offre_id" defaultValue={offreId || ""} required
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="">Choisir une offre...</option>
              {offres.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.nom} - {eur(o.tarif_vente_conseille)}
                </option>
              ))}
            </select>
          </div>

          {selectedOffre && (
            <div className="bg-gray-50 rounded-lg p-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Type</span>
                <span className="font-medium">{selectedOffre.type_site}</span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-gray-500">Prix catalogue</span>
                <span className="font-medium">{eur(selectedOffre.tarif_vente_conseille)}</span>
              </div>
            </div>
          )}

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

          <div className="space-y-3 sm:space-y-0 sm:grid sm:grid-cols-3 sm:gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Remise setup %</label>
              <input name="remise_setup" type="number" inputMode="decimal" min={0} max={100}
                defaultValue={remiseSetup} className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Remise recurrent %</label>
              <input name="remise_recurrent" type="number" inputMode="decimal" min={0} max={100}
                defaultValue={remiseRecurrent} className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Marge add.</label>
              <input name="marge_add" type="number" inputMode="decimal"
                defaultValue={margeAdd} className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
          </div>

          <button type="submit"
            className="w-full py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            Simuler
          </button>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </form>

        {/* Resultats */}
        <div className="bg-white border rounded-lg p-4 sm:p-5">
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
