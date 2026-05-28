"use client";
import { useState } from "react";
import type { Offre } from "@/lib/api";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}
function N(v: string) { return Number(v); }

const PLANS = ["100%", "50/50", "50/25/25", "25/25/25/25"];
const DUREES = ["8 T (2 ans)", "12 T (3 ans)", "16 T (4 ans)", "20 T (5 ans)", "28 T (7 ans)"];

interface OptS {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: string; vente_mensuel: string; setup_achat: string; mensuel_achat: string;
  statut: string; commentaire: string | null;
}

type Result = Record<string, string>;

export default function SimulateurForm({ offres, optionsByOffre }: {
  offres: Offre[]; optionsByOffre: Record<string, OptS[]>;
}) {
  const [offreId, setOffreId] = useState("");
  const [mode, setMode] = useState("Comptant");
  const [plan, setPlan] = useState("100%");
  const [remSetup, setRemSetup] = useState("0");
  const [remRecur, setRemRecur] = useState("0");
  const [margeAdd, setMargeAdd] = useState("0");
  const [duree, setDuree] = useState("");
  const [coeff, setCoeff] = useState("3.20");
  const [pctMaint, setPctMaint] = useState("30");
  const [garantie, setGarantie] = useState("10");
  const [prestas, setPrestas] = useState([
    { nom: "", qty: "0", achat: "", vente: "" },
    { nom: "", qty: "0", achat: "", vente: "" },
    { nom: "", qty: "0", achat: "", vente: "" },
  ]);
  const [optQty, setOptQty] = useState<Record<number, number>>({});
  const [packId, setPackId] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const offre = offreId ? offres.find(o => o.id === Number(offreId)) : null;
  const allKeys = Object.keys(optionsByOffre);
  const options = offreId ? (optionsByOffre[offreId] || []) : [];
  const packs = options.filter(o => o.type_ligne === "PACK");
  const others = options.filter(o => o.type_ligne !== "PACK");
  const cats = new Map<string, OptS[]>();
  for (const o of others) { if (!cats.has(o.categorie)) cats.set(o.categorie, []); cats.get(o.categorie)!.push(o); }

  const qty = (id: number) => optQty[id] || 0;
  const setQ = (id: number, v: number) => setOptQty(p => ({ ...p, [id]: v }));
  const updPresta = (i: number, f: string, v: string) => setPrestas(p => p.map((x, j) => j === i ? { ...x, [f]: v } : x));

  const reset = () => {
    setOffreId(""); setMode("Comptant"); setPlan("100%");
    setRemSetup("0"); setRemRecur("0"); setMargeAdd("0");
    setDuree(""); setCoeff("3.20"); setPctMaint("30"); setGarantie("10");
    setPrestas([{ nom: "", qty: "0", achat: "", vente: "" }, { nom: "", qty: "0", achat: "", vente: "" }, { nom: "", qty: "0", achat: "", vente: "" }]);
    setOptQty({}); setPackId(""); setResult(null); setError("");
  };

  const simuler = async () => {
    if (!offre) return;
    setLoading(true); setError("");
    const sels: Array<Record<string, unknown>> = [];
    for (const o of options) {
      const q = o.type_ligne === "PACK" ? (String(o.id) === packId ? 1 : 0) : qty(o.id);
      if (q > 0 || o.statut === "Inclus") {
        sels.push({
          option_id: o.id, code: o.code, nom: o.nom, type_ligne: o.type_ligne,
          quantite: o.statut === "Inclus" ? 1 : q, statut: o.statut,
          prix_achat_setup: o.setup_achat, prix_vente_setup: o.vente_setup,
          prix_achat_mensuel: o.mensuel_achat, prix_vente_mensuel: o.vente_mensuel,
        });
      }
    }
    const ps = prestas.filter(p => p.nom && Number(p.qty) > 0 && Number(p.vente) > 0)
      .map(p => ({ designation: p.nom, quantite: Number(p.qty), prix_unitaire_achat: p.achat || "0", prix_unitaire_vente: p.vente }));
    const body: Record<string, unknown> = {
      offre_nom: offre.nom, offre_type_site: offre.type_site,
      prix_achat: String(offre.tarif_achat), prix_vente_conseille: String(offre.tarif_vente_conseille),
      mode_reglement: mode, plan_paiement: plan,
      remise_pct_setup: String(Number(remSetup) / 100), remise_pct_recurrent: String(Number(remRecur) / 100),
      marge_additionnelle: margeAdd, selections: sels, prestations: ps,
    };
    if (mode === "Leasing") {
      body.duree_financement = duree; body.coefficient_locam = coeff;
      body.pct_maintenance_locam = String(Number(pctMaint) / 100); body.garantie_web = garantie;
    }
    try {
      const res = await fetch("/api/simulation/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      setResult(await res.json());
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Simulateur de prix</h1>
        {(result || offreId) && <button type="button" onClick={reset} className="px-3 py-2 text-sm text-gray-500 border rounded hover:bg-gray-50">Reinitialiser</button>}
      </div>

      <div className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-5 lg:gap-6">
        <div className="lg:col-span-3 space-y-4">

          {/* Offre + Mode */}
          <div className="bg-white border rounded-lg p-4 space-y-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Offre et mode</h2>
            <select value={offreId} onChange={e => { setOffreId(e.target.value); setOptQty({}); setPackId(""); setResult(null); }}
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="">Choisir une offre...</option>
              {offres.map(o => <option key={o.id} value={o.id}>{o.nom} ({o.type_site}) - {eur(o.tarif_vente_conseille)}</option>)}
            </select>
            {offre && (
              <div className="bg-gray-50 rounded-lg p-3 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Type</span><span className="font-medium">{offre.type_site}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-500">Prix catalogue</span><span className="font-medium">{eur(offre.tarif_vente_conseille)}</span></div>
                <div className="flex justify-between mt-1"><span className="text-gray-500">Options chargees</span><span className="font-medium">{options.length} (cles: {allKeys.join(",")})</span></div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-sm font-medium mb-1">Mode</label>
                <select value={mode} onChange={e => setMode(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm">
                  <option>Comptant</option><option>Leasing</option></select></div>
              <div><label className="block text-sm font-medium mb-1">Plan paiement</label>
                <select value={plan} onChange={e => setPlan(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm">
                  {PLANS.map(v => <option key={v}>{v}</option>)}</select></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><label className="block text-sm font-medium mb-1">Remise setup %</label>
                <input type="number" inputMode="decimal" min={0} max={100} value={remSetup} onChange={e => setRemSetup(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Remise recur. %</label>
                <input type="number" inputMode="decimal" min={0} max={100} value={remRecur} onChange={e => setRemRecur(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Marge add.</label>
                <input type="number" inputMode="decimal" value={margeAdd} onChange={e => setMargeAdd(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
            </div>
          </div>

          {/* Leasing (visible seulement en mode Leasing) */}
          {mode === "Leasing" && (
            <div className="bg-white border rounded-lg p-4 space-y-3">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Parametres leasing</h2>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium mb-1">Duree</label>
                  <select value={duree} onChange={e => setDuree(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm">
                    <option value="">-</option>{DUREES.map(d => <option key={d}>{d}</option>)}</select></div>
                <div><label className="block text-sm font-medium mb-1">Coeff. Locam</label>
                  <input type="number" inputMode="decimal" step="0.01" value={coeff} onChange={e => setCoeff(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
                <div><label className="block text-sm font-medium mb-1">% Maintenance</label>
                  <input type="number" inputMode="decimal" min={0} max={100} value={pctMaint} onChange={e => setPctMaint(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
                <div><label className="block text-sm font-medium mb-1">Garantie web</label>
                  <input type="number" inputMode="decimal" step="0.01" value={garantie} onChange={e => setGarantie(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              </div>
            </div>
          )}

          {/* Prestations sur mesure */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Prestations sur mesure</h2>
            {prestas.map((pr, i) => (
              <div key={i} className="grid grid-cols-4 gap-2">
                <div className="col-span-4 sm:col-span-1">
                  <input placeholder={`Prestation ${i + 1}`} value={pr.nom} onChange={e => updPresta(i, "nom", e.target.value)} className="w-full border rounded px-3 py-2 text-sm" /></div>
                <input type="number" inputMode="numeric" placeholder="Qte" min={0} value={pr.qty} onChange={e => updPresta(i, "qty", e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
                <input type="number" inputMode="decimal" step="0.01" placeholder="PU achat" value={pr.achat} onChange={e => updPresta(i, "achat", e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
                <input type="number" inputMode="decimal" step="0.01" placeholder="PU vente" value={pr.vente} onChange={e => updPresta(i, "vente", e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
            ))}
          </div>

          {/* Pack maintenance */}
          {packs.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-3">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Pack maintenance</h2>
              <div className="space-y-2">
                <label className={`flex items-center gap-3 p-2 rounded cursor-pointer ${!packId ? "bg-gray-50" : "hover:bg-gray-50"}`}>
                  <input type="radio" name="pack" checked={!packId} onChange={() => setPackId("")} className="accent-[#1A355E]" />
                  <span className="text-sm text-gray-500">Aucun pack</span></label>
                {packs.map(pk => {
                  const sel = packId === String(pk.id);
                  return (
                    <label key={pk.id} className={`flex items-center justify-between gap-3 p-2 rounded cursor-pointer transition-colors ${sel ? "bg-blue-50 border border-blue-200" : "hover:bg-gray-50"}`}>
                      <div className="flex items-center gap-3">
                        <input type="radio" name="pack" checked={sel} onChange={() => setPackId(String(pk.id))} className="accent-[#1A355E]" />
                        <div><span className={`text-sm font-medium ${sel ? "text-blue-900" : ""}`}>{pk.nom}</span>
                          {pk.commentaire && <p className="text-xs text-gray-400">{pk.commentaire}</p>}</div>
                      </div>
                      <span className="text-sm font-medium shrink-0">{eur(pk.vente_mensuel)}/mois</span>
                    </label>);
                })}
              </div>
            </div>
          )}

          {/* Options */}
          {others.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Options</h2>
              {Array.from(cats.entries()).map(([cat, opts]) => (
                <div key={cat}>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{cat}</h3>
                  <div className="space-y-1">
                    {opts.map(o => {
                      const incl = o.statut === "Inclus";
                      const q = qty(o.id);
                      const sel = q > 0;
                      const prix = o.type_ligne === "OPTION_SETUP" ? o.vente_setup : o.vente_mensuel;
                      const u = o.type_ligne === "OPTION_SETUP" ? "" : "/mois";
                      const bg = incl ? "bg-green-50" : sel ? "bg-blue-50 border border-blue-200" : "";
                      return (
                        <div key={o.id} className={`flex items-center justify-between gap-2 p-2 rounded text-sm transition-colors ${bg}`}>
                          <div className="flex-1 min-w-0">
                            <span className={incl ? "text-green-800" : sel ? "text-blue-900 font-medium" : ""}>{o.nom}</span>
                            {incl && <span className="ml-2 text-xs text-green-600 font-medium">Inclus</span>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-xs text-gray-400">{N(prix) > 0 ? `${eur(prix)}${u}` : ""}</span>
                            {!incl && (
                              <select value={q} onChange={e => setQ(o.id, Number(e.target.value))}
                                className={`w-16 border rounded px-2 py-1 text-sm text-center ${sel ? "border-blue-300 bg-blue-50 font-medium" : ""}`}>
                                {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}</select>
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
            <button type="button" onClick={simuler} disabled={!offre || loading}
              className="flex-1 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm disabled:opacity-50">
              {loading ? "Calcul en cours..." : "Simuler"}</button>
            <button type="button" onClick={reset} className="px-6 py-3 bg-gray-100 text-gray-600 rounded-lg text-sm">Reset</button>
          </div>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        {/* Resultats */}
        <div className="lg:col-span-2">
          <div className="bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4">
            <h2 className="text-lg font-semibold mb-4">Resultats</h2>
            {!result ? <p className="text-gray-400 text-sm">Selectionnez une offre et cliquez Simuler.</p> : (
              <div className="space-y-3 text-sm">
                <Sec t="Prix"><R l="Prix vente final HT" v={eur(result.prix_vente_final)} b /><R l="Setup affiche HT" v={eur(result.prix_setup_affiche)} /><R l="Mensuel affiche HT" v={eur(result.prix_mensuel_affiche)} /></Sec>
                <Sec t="Totaux TTC"><R l="Setup TTC" v={eur(result.total_setup_ttc)} b /><R l="Mensuel TTC" v={eur(result.total_mensuel_ttc)} /></Sec>
                {(N(result.total_prestations_vente) > 0 || N(result.total_options_setup_vente) > 0 || N(result.total_pack_maintenance_vente) > 0) && (
                  <Sec t="Detail">
                    {N(result.total_prestations_vente) > 0 && <R l="Prestations" v={eur(result.total_prestations_vente)} />}
                    {N(result.total_options_setup_vente) > 0 && <R l="Options setup" v={eur(result.total_options_setup_vente)} />}
                    {N(result.total_pack_maintenance_vente) > 0 && <R l="Pack maintenance" v={eur(result.total_pack_maintenance_vente)} />}
                    {N(result.total_options_recurrent_vente) > 0 && <R l="Options recurrentes" v={eur(result.total_options_recurrent_vente)} />}
                  </Sec>
                )}
                <Sec t="Remises"><R l="Remise setup" v={eur(result.remise_eur_setup)} /><R l="Remise recurrent" v={eur(result.remise_eur_recurrent)} /></Sec>
                <Sec t="Marge"><R l="Marge" v={eur(result.marge)} /><R l="Marge totale" v={eur(result.marge_totale)} b /></Sec>
                {mode === "Comptant" && N(result.prelevement_1) > 0 && (
                  <Sec t="Plan de paiement">
                    <R l="Prelevement 1" v={eur(result.prelevement_1)} />
                    {N(result.prelevement_2) > 0 && <R l="Prelevement 2" v={eur(result.prelevement_2)} />}
                    {N(result.prelevement_3) > 0 && <R l="Prelevement 3" v={eur(result.prelevement_3)} />}
                    {N(result.prelevement_4) > 0 && <R l="Prelevement 4" v={eur(result.prelevement_4)} />}
                    {N(result.recurrent_mensuel) > 0 && <R l="Recurrent mensuel" v={eur(result.recurrent_mensuel)} />}
                  </Sec>
                )}
                {mode === "Leasing" && N(result.loyer) > 0 && (
                  <Sec t="Leasing">
                    <R l="Montant finance" v={eur(result.montant_finance)} />
                    <R l="Loyer" v={eur(result.loyer)} />
                    <R l="Loyer client HT" v={eur(result.loyer_client_ht)} b />
                  </Sec>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Sec({ t, children }: { t: string; children: React.ReactNode }) {
  return (<div className="border-t pt-3"><h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">{t}</h3><div className="space-y-1.5">{children}</div></div>);
}
function R({ l, v, b }: { l: string; v: string; b?: boolean }) {
  return (<div className="flex justify-between gap-2"><span className="text-gray-600">{l}</span><span className={`text-right shrink-0 ${b ? "font-semibold" : ""}`}>{v}</span></div>);
}
