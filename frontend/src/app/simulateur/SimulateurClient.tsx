"use client";

// Simulateur en TEMPS REEL. Tout l'etat vit dans le navigateur (React) et chaque
// changement (quantite, case "Offrir", remise, mode...) relance automatiquement le
// calcul cote backend Python via /api/simulation/ — une seule source de verite, pas
// de divergence avec le devis. Plus de bouton "Simuler".
//
// La case "Offrir" n'apparait que sur une option dont la quantite est > 0 (jamais
// sur une option a 0 ni sur une option "Inclus", deja gratuite).

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { saveDevis } from "@/lib/actions";
import type { Client } from "@/lib/api";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}
function N(v: unknown) { return Number(v || 0); }

const PLANS = ["100%", "50/50", "33/33/33", "50/25/25", "25/25/25/25"];
const DUREES = ["8 T (2 ans)", "12 T (3 ans)", "16 T (4 ans)", "20 T (5 ans)", "28 T (7 ans)"];

export interface OptS {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: string; vente_mensuel: string; setup_achat: string; mensuel_achat: string;
  statut: string; commentaire: string | null;
}
export interface OffreS {
  id: number; nom: string; type_site: string;
  tarif_achat: string | number; tarif_vente_conseille: string | number;
  pages: number; heures: number;
}
interface Presta { nom: string; qty: string; achat: string; vente: string; offrir: boolean; }
type Result = Record<string, string>;

// Etat initial de reedition d'un devis existant (renvoye par GET /devis/{id}/edition).
export interface EditionInitial {
  id: number;
  statut: string;
  offre_id: number;
  client_id: number;
  mode: string;
  plan: string;
  remise_setup: string;
  remise_recurrent: string;
  marge_add: string;
  pack_id: number | null;
  options: Array<{ option_id: number; quantite: number; inclus: boolean }>;
  offrir_option_ids: number[];
  prestations: Array<{ nom: string; qty: string; achat: string; vente: string; offrir: boolean }>;
}

interface RecapLigne {
  nom: string; detail?: string; montant: number;
  recurrent: boolean; inclus: boolean; offert: boolean;
}

const PRESTA_VIDE: Presta = { nom: "", qty: "1", achat: "", vente: "", offrir: false };

export default function SimulateurClient({
  offre, options, clients, initial,
}: { offre: OffreS; options: OptS[]; clients: Client[]; initial?: EditionInitial | null }) {
  const packs = options.filter(o => o.type_ligne === "PACK");
  const others = options.filter(o => o.type_ligne !== "PACK");
  const cats = new Map<string, OptS[]>();
  for (const o of others) { if (!cats.has(o.categorie)) cats.set(o.categorie, []); cats.get(o.categorie)!.push(o); }

  // Prefill depuis un devis existant (reedition), sinon valeurs par defaut.
  const initQty: Record<number, number> = {};
  const initOffrir: Record<number, boolean> = {};
  if (initial) {
    for (const o of initial.options) if (!o.inclus) initQty[o.option_id] = o.quantite;
    for (const id of initial.offrir_option_ids) initOffrir[id] = true;
  }
  const initPrestas: Presta[] = [{ ...PRESTA_VIDE }, { ...PRESTA_VIDE }, { ...PRESTA_VIDE }];
  if (initial) {
    initial.prestations.slice(0, 3).forEach((p, i) => {
      initPrestas[i] = { nom: p.nom, qty: p.qty, achat: p.achat, vente: p.vente, offrir: p.offrir };
    });
  }

  // --- Etat du formulaire ---
  const [mode, setMode] = useState(initial?.mode ?? "Comptant");
  const [plan, setPlan] = useState(initial?.plan ?? "100%");
  const [remiseSetup, setRemiseSetup] = useState(initial?.remise_setup ?? "0");
  const [remiseRecurrent, setRemiseRecurrent] = useState(initial?.remise_recurrent ?? "0");
  const [margeAdd, setMargeAdd] = useState(initial?.marge_add ?? "0");
  // Leasing
  const [duree, setDuree] = useState("");
  const [coeff, setCoeff] = useState("3.20");
  const [pctMaint, setPctMaint] = useState("30");
  const [garantie, setGarantie] = useState("10");
  // Selections
  const [qty, setQty] = useState<Record<number, number>>(initQty);
  const [packId, setPackId] = useState<number | null>(initial?.pack_id ?? null);
  const [offrir, setOffrir] = useState<Record<number, boolean>>(initOffrir);
  const [prestas, setPrestas] = useState<Presta[]>(initPrestas);
  // Resultat
  const [result, setResult] = useState<Result | null>(null);
  const [calcul, setCalcul] = useState(false);

  const edition = !!initial;
  const creerNouvelleVersion = edition && initial!.statut !== "brouillon";

  const setQ = (id: number, v: number) => setQty(p => ({ ...p, [id]: v }));
  const setOff = (id: number, v: boolean) => setOffrir(p => ({ ...p, [id]: v }));
  const setPresta = (i: number, patch: Partial<Presta>) =>
    setPrestas(p => p.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  // --- Construction des articles offerts (pour calcul + recap + sauvegarde) ---
  const articlesOfferts: Array<{ designation: string; prix_achat: string; prix_vente: string; est_setup: boolean }> = [];
  for (const o of others) {
    const q = o.statut === "Inclus" ? 1 : (qty[o.id] || 0);
    if (q > 0 && o.statut !== "Inclus" && offrir[o.id]) {
      const est_setup = o.type_ligne === "OPTION_SETUP";
      articlesOfferts.push({
        designation: o.nom,
        prix_achat: String(Number(est_setup ? o.setup_achat : o.mensuel_achat) * q),
        prix_vente: String(Number(est_setup ? o.vente_setup : o.vente_mensuel) * q),
        est_setup,
      });
    }
  }
  for (const pk of packs) {
    if (packId === pk.id && offrir[pk.id]) {
      articlesOfferts.push({
        designation: pk.nom, prix_achat: String(Number(pk.mensuel_achat)),
        prix_vente: String(Number(pk.vente_mensuel)), est_setup: false,
      });
    }
  }
  prestas.forEach(pr => {
    const q = N(pr.qty), pv = N(pr.vente);
    if (pr.nom && q > 0 && pv > 0 && pr.offrir) {
      articlesOfferts.push({
        designation: pr.nom, prix_achat: String(N(pr.achat) * q),
        prix_vente: String(pv * q), est_setup: true,
      });
    }
  });
  const offertsRecurrent = articlesOfferts.filter(a => !a.est_setup);

  // --- Recapitulatif (panier) ---
  const recap: RecapLigne[] = [{
    nom: offre.nom, montant: Number(offre.tarif_vente_conseille),
    recurrent: false, inclus: false, offert: false,
  }];
  prestas.forEach(pr => {
    const q = N(pr.qty), pv = N(pr.vente);
    if (pr.nom && q > 0 && pv > 0) {
      recap.push({ nom: pr.nom, detail: q > 1 ? `${q} x ${eur(pv)}` : undefined,
        montant: q * pv, recurrent: false, inclus: false, offert: pr.offrir });
    }
  });
  for (const o of others) {
    const incl = o.statut === "Inclus";
    const q = incl ? 1 : (qty[o.id] || 0);
    if (q <= 0) continue;
    const est_setup = o.type_ligne === "OPTION_SETUP";
    const pu = Number(est_setup ? o.vente_setup : o.vente_mensuel);
    recap.push({ nom: o.nom, detail: q > 1 ? `${q} x ${eur(pu)}` : undefined,
      montant: pu * q, recurrent: !est_setup, inclus: incl, offert: !incl && !!offrir[o.id] });
  }
  for (const pk of packs) {
    if (packId === pk.id) {
      recap.push({ nom: pk.nom, montant: Number(pk.vente_mensuel),
        recurrent: true, inclus: false, offert: !!offrir[pk.id] });
    }
  }
  const recapSetup = recap.filter(l => !l.recurrent);
  const recapRecurrent = recap.filter(l => l.recurrent);

  // --- Recalcul automatique (debounce + anti-course) ---
  const reqId = useRef(0);
  // Cle qui resume tout l'etat pertinent : declenche le recalcul a chaque changement.
  const cle = JSON.stringify({
    mode, plan, remiseSetup, remiseRecurrent, margeAdd, duree, coeff, pctMaint, garantie,
    qty, packId, offrir, prestas,
  });

  useEffect(() => {
    const id = ++reqId.current;
    const t = setTimeout(async () => {
      setCalcul(true);
      try {
        const selections = [];
        for (const o of others) {
          const q = qty[o.id] || 0;
          if (q > 0 || o.statut === "Inclus") {
            selections.push({
              option_id: o.id, code: o.code, nom: o.nom, type_ligne: o.type_ligne,
              quantite: o.statut === "Inclus" ? 1 : q, statut: o.statut,
              prix_achat_setup: o.setup_achat, prix_vente_setup: o.vente_setup,
              prix_achat_mensuel: o.mensuel_achat, prix_vente_mensuel: o.vente_mensuel,
            });
          }
        }
        for (const pk of packs) {
          if (packId === pk.id) {
            selections.push({
              option_id: pk.id, code: pk.code, nom: pk.nom, type_ligne: "PACK",
              quantite: 1, statut: pk.statut,
              prix_achat_setup: pk.setup_achat, prix_vente_setup: pk.vente_setup,
              prix_achat_mensuel: pk.mensuel_achat, prix_vente_mensuel: pk.vente_mensuel,
            });
          }
        }
        const prestations = prestas
          .filter(pr => pr.nom && N(pr.qty) > 0 && N(pr.vente) > 0)
          .map(pr => ({ designation: pr.nom, quantite: N(pr.qty),
            prix_unitaire_achat: String(N(pr.achat)), prix_unitaire_vente: String(N(pr.vente)) }));

        const body: Record<string, unknown> = {
          offre_nom: offre.nom, offre_type_site: offre.type_site,
          prix_achat: String(offre.tarif_achat), prix_vente_conseille: String(offre.tarif_vente_conseille),
          mode_reglement: mode, plan_paiement: plan,
          remise_pct_setup: String(N(remiseSetup) / 100),
          remise_pct_recurrent: String(N(remiseRecurrent) / 100),
          marge_additionnelle: margeAdd || "0",
          selections, prestations, articles_offerts: articlesOfferts,
        };
        if (mode === "Leasing") {
          body.duree_financement = duree;
          body.coefficient_locam = coeff || "0";
          body.pct_maintenance_locam = String(N(pctMaint) / 100);
          body.garantie_web = garantie || "10";
        }

        const res = await fetch("/api/simulation/", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (id === reqId.current) setResult(data);
      } catch {
        // on garde le dernier resultat valide en cas d'erreur reseau
      } finally {
        if (id === reqId.current) setCalcul(false);
      }
    }, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cle]);

  // --- Donnees pour la sauvegarde (form server action) ---
  const optionsPourDevis = options
    .filter(o => o.statut === "Inclus" || (qty[o.id] || 0) > 0 || (o.type_ligne === "PACK" && packId === o.id))
    .map(o => ({
      option_id: o.id, code: o.code, nom: o.nom, type_ligne: o.type_ligne,
      quantite: o.statut === "Inclus" ? 1 : (o.type_ligne === "PACK" ? 1 : (qty[o.id] || 0)),
      statut: o.statut, prix_vente_setup: o.vente_setup, prix_vente_mensuel: o.vente_mensuel,
    }));

  // Prestations sur mesure a persister dans le devis (etaient perdues avant).
  const prestationsPourDevis = prestas
    .filter(pr => pr.nom && N(pr.qty) > 0 && N(pr.vente) > 0)
    .map(pr => ({
      designation: pr.nom, quantite: N(pr.qty),
      prix_unitaire_achat: pr.achat || "0", prix_unitaire_vente: pr.vente || "0",
    }));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Simulateur de prix</h1>
        <Link href="/simulateur" className="px-3 py-2 text-sm text-gray-500 border rounded hover:bg-gray-50">
          Changer d&apos;offre
        </Link>
      </div>

      <div className="bg-[#1A355E] text-white rounded-lg p-4 mb-4">
        <h2 className="font-semibold">{offre.nom}</h2>
        <div className="flex gap-4 text-sm mt-1 text-white/70">
          <span>{offre.type_site}</span>
          <span>{eur(offre.tarif_vente_conseille)} HT</span>
          <span>{offre.pages} pages</span>
          <span>{offre.heures} h</span>
        </div>
      </div>

      <div className="space-y-4 lg:space-y-0 lg:grid lg:grid-cols-5 lg:gap-6">
        {/* Colonne formulaire */}
        <div className="lg:col-span-3 space-y-4">
          {/* Mode + remises */}
          <div className="bg-white border rounded-lg p-4 space-y-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Mode et remises</h2>
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
                <input type="number" inputMode="decimal" min={0} max={100} value={remiseSetup}
                  onChange={e => setRemiseSetup(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Remise recur. %</label>
                <input type="number" inputMode="decimal" min={0} max={100} value={remiseRecurrent}
                  onChange={e => setRemiseRecurrent(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              <div><label className="block text-sm font-medium mb-1">Marge add.</label>
                <input type="number" inputMode="decimal" value={margeAdd}
                  onChange={e => setMargeAdd(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
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
                  <input type="number" inputMode="decimal" step="0.01" value={coeff}
                    onChange={e => setCoeff(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
                <div><label className="block text-sm font-medium mb-1">% Maintenance</label>
                  <input type="number" inputMode="decimal" min={0} max={100} value={pctMaint}
                    onChange={e => setPctMaint(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
                <div><label className="block text-sm font-medium mb-1">Garantie web</label>
                  <input type="number" inputMode="decimal" step="0.01" value={garantie}
                    onChange={e => setGarantie(e.target.value)} className="w-full border rounded px-3 py-2.5 text-sm" /></div>
              </div>
            </div>
          )}

          {/* Prestations sur mesure */}
          <div className="bg-white border rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase">Prestations sur mesure</h2>
            {prestas.map((pr, i) => (
              <div key={i} className="space-y-1">
                <div className="grid grid-cols-4 gap-2">
                  <div className="col-span-4 sm:col-span-1">
                    <input placeholder={`Prestation ${i + 1}`} value={pr.nom}
                      onChange={e => setPresta(i, { nom: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" /></div>
                  <input type="number" inputMode="numeric" placeholder="Qte" min={0} value={pr.qty}
                    onChange={e => setPresta(i, { qty: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
                  <input type="number" inputMode="decimal" step="0.01" placeholder="PU achat" value={pr.achat}
                    onChange={e => setPresta(i, { achat: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
                  <input type="number" inputMode="decimal" step="0.01" placeholder="PU vente" value={pr.vente}
                    onChange={e => setPresta(i, { vente: e.target.value })} className="w-full border rounded px-3 py-2 text-sm" />
                </div>
                {pr.nom && N(pr.qty) > 0 && N(pr.vente) > 0 && (
                  <label className="flex items-center gap-1 text-xs text-amber-600 cursor-pointer">
                    <input type="checkbox" checked={pr.offrir} onChange={e => setPresta(i, { offrir: e.target.checked })} className="accent-amber-500" />
                    Offrir cette prestation
                  </label>
                )}
              </div>
            ))}
          </div>

          {/* Pack maintenance */}
          {packs.length > 0 && (
            <div className="bg-white border rounded-lg p-4 space-y-3">
              <h2 className="text-sm font-semibold text-gray-500 uppercase">Pack maintenance</h2>
              <div className="space-y-2">
                <label className={`flex items-center gap-3 p-2 rounded cursor-pointer ${packId === null ? "bg-gray-50" : "hover:bg-gray-50"}`}>
                  <input type="radio" name="pack" checked={packId === null} onChange={() => setPackId(null)} className="accent-[#1A355E]" />
                  <span className="text-sm text-gray-500">Aucun pack</span></label>
                {packs.map(pk => {
                  const sel = packId === pk.id;
                  return (
                    <div key={pk.id} className={`flex items-center justify-between gap-3 p-2 rounded ${sel ? "bg-blue-50 border border-blue-200" : "hover:bg-gray-50"}`}>
                      <label className="flex items-center gap-3 cursor-pointer flex-1 min-w-0">
                        <input type="radio" name="pack" checked={sel} onChange={() => setPackId(pk.id)} className="accent-[#1A355E]" />
                        <div><span className={`text-sm font-medium ${sel ? "text-blue-900" : ""}`}>{pk.nom}</span>
                          {sel && offrir[pk.id] && <span className="ml-2 text-xs text-red-600 font-medium">Offert</span>}
                          {pk.commentaire && <p className="text-xs text-gray-400">{pk.commentaire}</p>}</div>
                      </label>
                      <div className="flex items-center gap-3 shrink-0">
                        {sel && (
                          <label className="flex items-center gap-1 text-xs text-red-600 cursor-pointer"
                            title="Offrir le pack en RECURRENT (mensuel) — exceptionnel">
                            <input type="checkbox" checked={!!offrir[pk.id]} onChange={e => setOff(pk.id, e.target.checked)} className="accent-red-600" />
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
                      const q = qty[o.id] || 0;
                      const sel = q > 0;
                      const recurrent = o.type_ligne !== "OPTION_SETUP";
                      const prix = o.type_ligne === "OPTION_SETUP" ? o.vente_setup : o.vente_mensuel;
                      const u = o.type_ligne === "OPTION_SETUP" ? "" : "/mois";
                      const bg = incl ? "bg-green-50" : sel ? "bg-blue-50 border border-blue-200" : "";
                      return (
                        <div key={o.id} className={`flex items-center justify-between gap-2 p-2 rounded text-sm ${bg}`}>
                          <div className="flex-1 min-w-0">
                            <span className={incl ? "text-green-800" : sel ? "text-blue-900 font-medium" : ""}>{o.nom}</span>
                            {incl && <span className="ml-2 text-xs text-green-600 font-medium">Inclus</span>}
                            {sel && !incl && offrir[o.id] && <span className={`ml-2 text-xs font-medium ${recurrent ? "text-red-600" : "text-amber-600"}`}>Offert</span>}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {/* Case "Offrir" : uniquement si quantite > 0 (et option non incluse) */}
                            {sel && !incl && (
                              <label className={`flex items-center gap-1 text-xs cursor-pointer ${recurrent ? "text-red-600" : "text-gray-500"}`}
                                title={recurrent ? "Offrir en RECURRENT (mensuel) — exceptionnel" : "Offrir (one-shot)"}>
                                <input type="checkbox" checked={!!offrir[o.id]} onChange={e => setOff(o.id, e.target.checked)}
                                  className={recurrent ? "accent-red-600" : "accent-amber-500"} />
                                Offrir{recurrent ? " (recur.)" : ""}
                              </label>
                            )}
                            <span className="text-xs text-gray-400">{N(prix) > 0 ? `${eur(prix)}${u}` : ""}</span>
                            {incl ? (
                              <span className="text-xs text-green-600 w-16 text-center">compris</span>
                            ) : (
                              <select value={q} onChange={e => setQ(o.id, Number(e.target.value))}
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
        </div>

        {/* Colonne resultats */}
        <div className="lg:col-span-2">
          <div className="bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Resultats</h2>
              {calcul && <span className="text-xs text-gray-400">calcul...</span>}
            </div>
            {!result ? <p className="text-gray-400 text-sm">Calcul en cours...</p> : (
              <div className="space-y-4 text-sm">

                {/* 1. Recapitulatif (le panier), en cartes */}
                {recapSetup.length > 0 && (
                  <CarteRecap titre="Prestation initiale" sousTitre="paiement unique" lignes={recapSetup} />
                )}
                {recapRecurrent.length > 0 && (
                  <CarteRecap titre="Abonnement mensuel" sousTitre="recurrent" lignes={recapRecurrent} suffix="/mois" />
                )}

                {/* 2. Totaux a payer : HT -> TVA -> TTC, bien separes */}
                <div className="rounded-lg border-2 border-[#1A355E]/15 bg-[#1A355E]/5 p-3 space-y-3">
                  <BlocTotal
                    titre="A payer (prestation initiale)"
                    ht={result.total_setup_ht} tva={result.total_setup_tva} ttc={result.total_setup_ttc}
                  />
                  {N(result.total_mensuel_ttc) > 0 && (
                    <BlocTotal
                      titre="Puis chaque mois" suffix="/mois"
                      ht={result.total_mensuel_ht} tva={result.total_mensuel_tva} ttc={result.total_mensuel_ttc}
                    />
                  )}
                </div>

                {/* 3. Plan de paiement (comptant) */}
                {mode === "Comptant" && N(result.prelevement_1) > 0 && N(result.prelevement_2) > 0 && (
                  <Sec t="Echeancier (TTC)">
                    <R l="Versement 1" v={eur(result.prelevement_1)} />
                    {N(result.prelevement_2) > 0 && <R l="Versement 2" v={eur(result.prelevement_2)} />}
                    {N(result.prelevement_3) > 0 && <R l="Versement 3" v={eur(result.prelevement_3)} />}
                    {N(result.prelevement_4) > 0 && <R l="Versement 4" v={eur(result.prelevement_4)} />}
                  </Sec>)}

                {/* 4. Leasing */}
                {mode === "Leasing" && N(result.loyer) > 0 && (
                  <Sec t="Leasing">
                    <R l="Montant finance" v={eur(result.montant_finance)} />
                    <R l="Loyer" v={eur(result.loyer)} />
                    <R l="Loyer client HT" v={eur(result.loyer_client_ht)} b />
                  </Sec>)}

                {/* 5. Alerte recurrent offert */}
                {offertsRecurrent.length > 0 && (
                  <div className="border-2 border-red-300 bg-red-50 rounded-lg p-3">
                    <p className="text-sm font-semibold text-red-700">Attention : vous offrez du RECURRENT (mensuel)</p>
                    <p className="text-xs text-red-600 mt-1">
                      {offertsRecurrent.map(a => a.designation).join(", ")} — soit {eur(offertsRecurrent.reduce((s, a) => s + Number(a.prix_vente), 0))}/mois deduits du revenu recurrent. C&apos;est exceptionnel : verifiez que c&apos;est intentionnel.
                    </p>
                  </div>)}

                {/* 6. Infos internes (remises + marge), discretes */}
                <details className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs">
                  <summary className="cursor-pointer font-semibold text-gray-500 uppercase">Detail interne (remises, marge)</summary>
                  <div className="mt-2 space-y-1">
                    {(N(result.remise_eur_setup) > 0 || N(result.remise_eur_recurrent) > 0) && (
                      <>
                        {N(result.remise_eur_setup) > 0 && <R l="Remise setup" v={`- ${eur(result.remise_eur_setup)}`} />}
                        {N(result.remise_eur_recurrent) > 0 && <R l="Remise recurrent" v={`- ${eur(result.remise_eur_recurrent)}/mois`} />}
                      </>
                    )}
                    <R l="Marge totale" v={eur(result.marge_totale)} b />
                  </div>
                </details>

              </div>
            )}
          </div>

          {/* Enregistrer le devis */}
          {result && (
            <div className="bg-white border-2 border-green-200 rounded-lg p-4 mt-4">
              <h2 className="text-sm font-semibold text-green-800 uppercase mb-3">
                {edition ? (creerNouvelleVersion ? "Enregistrer une nouvelle version" : "Enregistrer les modifications") : "Enregistrer ce devis"}
              </h2>
              {creerNouvelleVersion && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-3">
                  Ce devis a deja ete transmis : l&apos;enregistrement creera une nouvelle version
                  (l&apos;actuelle sera conservee en lecture seule).
                </p>
              )}
              <form action={saveDevis}>
                {edition && <input type="hidden" name="devis_id" value={initial!.id} />}
                <input type="hidden" name="offre_id" value={offre.id} />
                <input type="hidden" name="mode" value={mode} />
                <input type="hidden" name="plan" value={plan} />
                <input type="hidden" name="remise_setup" value={remiseSetup} />
                <input type="hidden" name="remise_recurrent" value={remiseRecurrent} />
                <input type="hidden" name="marge_add" value={margeAdd} />
                <input type="hidden" name="result_json" value={JSON.stringify(result)} />
                <input type="hidden" name="options_json" value={JSON.stringify(optionsPourDevis)} />
                <input type="hidden" name="prestations_json" value={JSON.stringify(prestationsPourDevis)} />
                <input type="hidden" name="articles_offerts_json" value={JSON.stringify(articlesOfferts)} />
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-1">Client</label>
                  <select name="client_id" required defaultValue={initial?.client_id ?? ""}
                    className="w-full border rounded px-3 py-2.5 text-sm">
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
                  {edition ? (creerNouvelleVersion ? "Creer la nouvelle version" : "Enregistrer les modifications") : "Enregistrer le devis"}
                </button>
              </form>
            </div>
          )}
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
// Carte d'un groupe du recapitulatif (prestation initiale ou abonnement) avec
// ses lignes et un sous-total HT (net des articles offerts/inclus).
function CarteRecap({ titre, sousTitre, lignes, suffix = "" }: {
  titre: string; sousTitre: string; lignes: RecapLigne[]; suffix?: string;
}) {
  const sousTotal = lignes.reduce((s, l) => s + (l.offert ? 0 : l.montant), 0);
  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden">
      <div className="flex items-baseline justify-between bg-gray-50 px-3 py-2 border-b border-gray-200">
        <span className="text-xs font-semibold text-gray-600 uppercase">{titre}</span>
        <span className="text-[11px] text-gray-400">{sousTitre}</span>
      </div>
      <div className="divide-y divide-gray-100">
        {lignes.map((l, i) => <LigneRecap key={i} l={l} />)}
      </div>
      <div className="flex justify-between px-3 py-2 bg-gray-50 border-t border-gray-200">
        <span className="text-xs font-medium text-gray-500">Sous-total HT</span>
        <span className="text-sm font-semibold">{eur(sousTotal)}{suffix}</span>
      </div>
    </div>
  );
}

function Pastille({ texte, couleur }: { texte: string; couleur: string }) {
  return <span className={`ml-2 inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${couleur}`}>{texte}</span>;
}

function LigneRecap({ l }: { l: RecapLigne }) {
  return (
    <div className="flex justify-between gap-2 items-baseline px-3 py-1.5">
      <span className="text-gray-700 min-w-0">
        {l.nom}
        {l.detail && <span className="text-gray-400 text-xs"> ({l.detail})</span>}
        {l.inclus && <Pastille texte="Inclus" couleur="bg-green-100 text-green-700" />}
        {l.offert && <Pastille texte="Offert" couleur={l.recurrent ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"} />}
      </span>
      <span className={`text-right shrink-0 ${l.offert ? "line-through text-gray-400" : l.inclus ? "text-green-600" : "text-gray-700"}`}>
        {l.inclus ? "compris" : `${eur(l.montant)}${l.recurrent ? "/mois" : ""}`}
      </span>
    </div>
  );
}

// Bloc total HT -> TVA -> TTC, le TTC mis en avant.
function BlocTotal({ titre, ht, tva, ttc, suffix = "" }: {
  titre: string; ht: string; tva: string; ttc: string; suffix?: string;
}) {
  return (
    <div>
      <p className="text-[11px] font-semibold text-gray-500 uppercase mb-1">{titre}</p>
      <div className="space-y-0.5">
        <div className="flex justify-between text-xs text-gray-500"><span>Total HT</span><span>{eur(ht)}{suffix}</span></div>
        <div className="flex justify-between text-xs text-gray-500"><span>TVA 20 %</span><span>{eur(tva)}{suffix}</span></div>
        <div className="flex justify-between text-base font-bold text-[#1A355E] pt-0.5">
          <span>Total TTC</span><span>{eur(ttc)}{suffix}</span>
        </div>
      </div>
    </div>
  );
}
