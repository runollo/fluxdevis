"use client";
import { useEffect, useState } from "react";
import { api, type Offre } from "@/lib/api";

const PLANS = ["100%", "50/50", "50/25/25", "25/25/25/25"];

function eur(v: number) {
  return v.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

export default function SimulateurPage() {
  const [offres, setOffres] = useState<Offre[]>([]);
  const [selectedOffre, setSelectedOffre] = useState<Offre | null>(null);
  const [mode, setMode] = useState("Comptant");
  const [plan, setPlan] = useState("100%");
  const [remiseSetup, setRemiseSetup] = useState(0);
  const [remiseRecurrent, setRemiseRecurrent] = useState(0);
  const [margeAdd, setMargeAdd] = useState(0);
  const [result, setResult] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.offres.list().then(setOffres).catch((e) => setError(e.message));
  }, []);

  const simuler = async () => {
    if (!selectedOffre) return;
    setLoading(true);
    setError("");
    try {
      const r = await api.simulation.run({
        offre_nom: selectedOffre.nom,
        offre_type_site: selectedOffre.type_site,
        prix_achat: selectedOffre.tarif_achat,
        prix_vente_conseille: selectedOffre.tarif_vente_conseille,
        mode_reglement: mode,
        plan_paiement: plan,
        remise_pct_setup: remiseSetup / 100,
        remise_pct_recurrent: remiseRecurrent / 100,
        marge_additionnelle: margeAdd,
      });
      setResult(r);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Simulateur de prix</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulaire */}
        <div className="bg-white border rounded-lg p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Offre</label>
            <select className="w-full border rounded px-3 py-2 text-sm"
              value={selectedOffre?.id || ""}
              onChange={(e) => setSelectedOffre(offres.find((o) => o.id === Number(e.target.value)) || null)}>
              <option value="">Choisir une offre...</option>
              {offres.map((o) => (
                <option key={o.id} value={o.id}>{o.nom} ({o.type_site}) - {eur(Number(o.tarif_vente_conseille))}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Mode</label>
              <select className="w-full border rounded px-3 py-2 text-sm" value={mode} onChange={(e) => setMode(e.target.value)}>
                <option>Comptant</option>
                <option>Leasing</option>
              </select>
            </div>
            {mode === "Comptant" && (
              <div>
                <label className="block text-sm font-medium mb-1">Plan paiement</label>
                <select className="w-full border rounded px-3 py-2 text-sm" value={plan} onChange={(e) => setPlan(e.target.value)}>
                  {PLANS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Remise setup %</label>
              <input type="number" min={0} max={100} value={remiseSetup}
                onChange={(e) => setRemiseSetup(Number(e.target.value))}
                className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Remise recurrent %</label>
              <input type="number" min={0} max={100} value={remiseRecurrent}
                onChange={(e) => setRemiseRecurrent(Number(e.target.value))}
                className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Marge add.</label>
              <input type="number" value={margeAdd}
                onChange={(e) => setMargeAdd(Number(e.target.value))}
                className="w-full border rounded px-3 py-2 text-sm" />
            </div>
          </div>

          <button onClick={simuler} disabled={!selectedOffre || loading}
            className="w-full py-2.5 bg-[#1A355E] text-white rounded font-medium text-sm hover:bg-[#15294a] disabled:opacity-50">
            {loading ? "Calcul..." : "Simuler"}
          </button>
          {error && <p className="text-red-600 text-sm">{error}</p>}
        </div>

        {/* Resultats */}
        <div className="bg-white border rounded-lg p-5">
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
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}</span>
      <span className={bold ? "font-semibold" : ""}>{value}</span>
    </div>
  );
}
