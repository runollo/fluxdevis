"use server";

import { redirect } from "next/navigation";
import { serverPost, serverPatch, serverFetch } from "./api";

export async function saveOffre(formData: FormData) {
  const id = formData.get("id") as string;
  const data: Record<string, unknown> = {
    nom: formData.get("nom"),
    type_site: formData.get("type_site"),
    type_offre: formData.get("type_offre"),
    tarif_achat: Number(formData.get("tarif_achat")),
    taux_marge: Number(formData.get("taux_marge")),
    tarif_vente_conseille: Number(formData.get("tarif_vente_conseille")),
    pages: Number(formData.get("pages")),
    heures: Number(formData.get("heures")),
    commission_apporteur: Number(formData.get("commission_apporteur")),
  };

  if (id) {
    await serverPatch(`/offres/${id}`, data);
  } else {
    await serverPost("/offres/", data);
  }
  redirect("/catalogue");
}

export async function saveOption(formData: FormData) {
  const id = formData.get("id") as string;
  const data: Record<string, unknown> = {
    code: formData.get("code"),
    nom: formData.get("nom"),
    categorie: formData.get("categorie"),
    type_ligne: formData.get("type_ligne"),
    heures_setup: Number(formData.get("heures_setup")),
    heures_mensuel: Number(formData.get("heures_mensuel")),
    prix_heure: Number(formData.get("prix_heure")),
    taux_marge: Number(formData.get("taux_marge")),
    prix_hebergement: Number(formData.get("prix_hebergement") || 0),
    commentaire: formData.get("commentaire") || null,
    selection_regle: formData.get("selection_regle"),
    quantite_defaut: Number(formData.get("quantite_defaut") || 0),
    unite: formData.get("unite") || "unite",
  };

  if (id) {
    await serverPatch(`/options/${id}`, data);
  } else {
    await serverPost("/options/", data);
  }
  redirect("/catalogue?tab=options");
}

export async function saveClient(formData: FormData) {
  const id = formData.get("id") as string;
  const fields = [
    "raison_sociale", "forme_juridique", "siret", "code_ape", "rcs", "tva_intracom",
    "adresse", "complement_adresse", "code_postal", "ville", "pays",
    "civilite", "interlocuteur", "fonction", "telephone", "mobile", "email",
    "notes",
  ];
  const data: Record<string, unknown> = {};
  for (const f of fields) {
    const val = formData.get(f);
    data[f] = val ? String(val) : null;
  }
  // raison_sociale ne doit jamais etre null
  data.raison_sociale = formData.get("raison_sociale");

  if (id) {
    await serverPatch(`/clients/${id}`, data);
  } else {
    await serverPost("/clients/", data);
  }
  redirect("/clients");
}


export async function runSimulation(formData: FormData) {
  const offre_id = formData.get("offre_id") as string;
  if (!offre_id) redirect("/simulateur");

  // Charger l'offre
  const offres = await serverFetch<Array<{
    id: number; nom: string; type_site: string;
    tarif_achat: string; tarif_vente_conseille: string;
  }>>("/offres/");
  const offre = offres.find(o => o.id === Number(offre_id));
  if (!offre) redirect("/simulateur");

  const mode = (formData.get("mode") as string) || "Comptant";
  const plan = (formData.get("plan") as string) || "100%";

  // Options selectionnees
  const selections: Array<Record<string, unknown>> = [];
  const optionsData = await serverFetch<Array<{
    id: number; code: string; nom: string; type_ligne: string; statut: string;
    setup_achat: string; vente_setup: string; mensuel_achat: string; vente_mensuel: string;
  }>>(`/offres/${offre_id}/options`);

  const packId = Number(formData.get("pack_id") || "0");

  for (const opt of optionsData) {
    let qty = Number(formData.get(`opt_${opt.id}`) || "0");

    // Pack maintenance : selectionne via radio button
    if (opt.type_ligne === "PACK") {
      qty = opt.id === packId ? 1 : 0;
    }

    if (qty > 0 || opt.statut === "Inclus") {
      selections.push({
        option_id: opt.id,
        code: opt.code,
        nom: opt.nom,
        type_ligne: opt.type_ligne,
        quantite: opt.statut === "Inclus" ? 1 : qty,
        statut: opt.statut,
        prix_achat_setup: opt.setup_achat,
        prix_vente_setup: opt.vente_setup,
        prix_achat_mensuel: opt.mensuel_achat,
        prix_vente_mensuel: opt.vente_mensuel,
      });
    }
  }

  // Prestations sur mesure
  const prestations: Array<Record<string, unknown>> = [];
  for (let i = 1; i <= 3; i++) {
    const designation = formData.get(`presta_${i}_nom`) as string;
    const qty = Number(formData.get(`presta_${i}_qty`) || "0");
    const pu_achat = Number(formData.get(`presta_${i}_achat`) || "0");
    const pu_vente = Number(formData.get(`presta_${i}_vente`) || "0");
    if (designation && qty > 0 && pu_vente > 0) {
      prestations.push({
        designation, quantite: qty,
        prix_unitaire_achat: String(pu_achat),
        prix_unitaire_vente: String(pu_vente),
      });
    }
  }

  const body: Record<string, unknown> = {
    offre_nom: offre!.nom,
    offre_type_site: offre!.type_site,
    prix_achat: offre!.tarif_achat,
    prix_vente_conseille: offre!.tarif_vente_conseille,
    mode_reglement: mode,
    plan_paiement: plan,
    remise_pct_setup: String(Number(formData.get("remise_setup") || "0") / 100),
    remise_pct_recurrent: String(Number(formData.get("remise_recurrent") || "0") / 100),
    marge_additionnelle: formData.get("marge_add") || "0",
    selections,
    prestations,
  };

  // Leasing
  if (mode === "Leasing") {
    body.duree_financement = formData.get("duree_financement") || "";
    body.coefficient_locam = formData.get("coefficient_locam") || "0";
    body.pct_maintenance_locam = String(Number(formData.get("pct_maintenance") || "0") / 100);
    body.garantie_web = formData.get("garantie_web") || "10";
  }

  const result = await serverPost<Record<string, string>>("/simulation/", body);

  // Encoder TOUT l'etat du formulaire dans l'URL pour le restaurer apres redirect
  const params = new URLSearchParams({
    offre_id,
    mode,
    plan,
    remise_setup: formData.get("remise_setup") as string || "0",
    remise_recurrent: formData.get("remise_recurrent") as string || "0",
    marge_add: formData.get("marge_add") as string || "0",
    result: encodeURIComponent(JSON.stringify(result)),
  });

  // Pack maintenance
  if (packId) params.set("pack_id", String(packId));

  // Options selectionnees (quantites > 0)
  for (const opt of optionsData) {
    if (opt.type_ligne === "PACK") continue;
    const qty = Number(formData.get(`opt_${opt.id}`) || "0");
    if (qty > 0) params.set(`opt_${opt.id}`, String(qty));
  }

  // Prestations sur mesure
  for (let i = 1; i <= 3; i++) {
    const nom = formData.get(`presta_${i}_nom`) as string;
    if (nom) {
      params.set(`presta_${i}_nom`, nom);
      params.set(`presta_${i}_qty`, formData.get(`presta_${i}_qty`) as string || "0");
      params.set(`presta_${i}_achat`, formData.get(`presta_${i}_achat`) as string || "0");
      params.set(`presta_${i}_vente`, formData.get(`presta_${i}_vente`) as string || "0");
    }
  }

  // Leasing
  if (mode === "Leasing") {
    params.set("duree_financement", formData.get("duree_financement") as string || "");
    params.set("coefficient_locam", formData.get("coefficient_locam") as string || "3.20");
    params.set("pct_maintenance", formData.get("pct_maintenance") as string || "30");
    params.set("garantie_web", formData.get("garantie_web") as string || "10");
  }

  redirect(`/simulateur?${params.toString()}`);
}
