"use client";
import { useState } from "react";
import type { Offre } from "@/lib/api";
import { clientFetch } from "@/lib/api";

const PLANS = ["100%", "50/50", "50/25/25", "25/25/25/25"];

function eur(v: number) {
  return v.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

export default function SimulateurClient({ offres }: { offres: Offre[] }) {
  const [selectedOffre, setSelectedOffre] = useState<Offre | null>(null);
  const [mode, setMode] = useState("Comptant");
  const [plan, setPlan] = useState("100%");
  const [remiseSetup, setRemiseSetup] = useState(0);
  const [remiseRecurrent, setRemiseRecurrent] = useState(0);
  const [margeAdd, setMargeAdd] = useState(0);
  const [result, setResult] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const simuler = async () => {
    if (!selectedOffre) return;
    setLoading(true);
    setError("");
    try {
      const r = await clientFetch<Record<string, number>>("/simulation/", {
        method: "POST",
        body: JSON.stringify({
          offre_nom: selectedOffre.nom,
          offre_type_site: selectedOffre.type_site,
          prix_achat: selectedOffre.tarif_achat,
          prix_vente_conseille: selectedOffre.tarif_vente_conseille,
          mode_reglement: mode,
          plan_paiement: plan,
          remise_pct_setup: remiseSetup / 100,
          remise_pct_recurrent: remiseRecurrent / 100,
          marge_additionnelle: margeAdd,
        }),
      });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Simulateur de prix</h1>
      <div className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-2 lg:gap-6">
        <div className="bg-white border rounded-lg p-4 sm:p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Offre</label>
            <select className="w-full border rounded px-3 py-2.5 text-sm"
              value={selectedOffre?.id || ""}
              onChange={(e) => setSelectedOffre(offres.find((o) => o.id === Number(e.target.value)) || null)}>
              <option value="">Choisir une offre...</option>
              {offres.map((o) => (
                <option key={o.id} value={o.id}>{o.nom} - {eur(Number(o.tarif_vente_conseille))}</option>
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
                <span className="font-medium">{eur(Number(selectedOffre.tarif_vente_conseille))}</span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Mode</label>
              <select className="w-full border rounded px-3 py-2.5 text-sm" value={mode} onChange={(e) => setMode(e.target.value)}>
                <option>Comptant</option>
                <option>Leasing</option>
              </select>
            </div>
            {mode === "Comptant" && (
              <div>
                <label className="block text-sm font-medium mb-1">Plan paiement</label>
                <select className="w-full border rounded px-3 py-2.5 text-sm" value={plan} onChange={(e) => setPlan(e.target.value)}>
                  {PLANS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
            )}
          </div>

          <div className="space-y-3 sm:space-y-0 sm:grid sm:grid-cols-3 sm:gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Remise setup %</label>
              <input type="number" inputMode="decimal" min={0} max={100} value={remiseSetup}
                onChange={(e) => setRemiseSetup(Number(e.target.value))}
                className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Remise recurrent %</label>
              <input type="number" inputMode="decimal" min={0} max={100} value={remiseRecurrent}
                onChange={(e) => setRemiseRecurrent(Number(e.target.value))}
                className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Marge add.</label>
              <input type="number" inputMode="decimal" value={margeAdd}
                onChange={(e) => setMargeAdd(Number(e.target.value))}
                className="w-full border rounded px-3 py-2.5 text-sm" />
            </div>
          </div>

          <button onClick={simuler} disabled={!selectedOffre || loading}
            className="w-full py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm hover:bg-[#15294a] disabled:opacity-50 active:scale-[0.98] transition-transform">
            {loading ? "Calcul..." : "Simuler"}
          </button>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        <div className="bg-white border rounded-lg p-4 sm:p-5">
          <h2 className="text-lg font-semibold mb-4">Resultats</h2>
          {!result ? (
            <p className="text-gray-400 text-sm">Selectionnez une offre et lancez la simulation.</p>
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
              {mode === "Comptant" && result.prelevement_1 > 0 && (
                <Section title="Plan de paiement">
                  <Row label="Prelevement 1" value={eur(result.prelevement_1)} />
                  {result.prelevement_2 > 0 && <Row label="Prelevement 2" value={eur(result.prelevement_2)} />}
                  {result.prelevement_3 > 0 && <Row label="Prelevement 3" value={eur(result.prelevement_3)} />}
                  {result.prelevement_4 > 0 && <Row label="Prelevement 4" value={eur(result.prelevement_4)} />}
                </Section>
              )}
              {mode === "Leasing" && result.loyer > 0 && (
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
