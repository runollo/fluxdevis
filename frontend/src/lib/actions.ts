"use server";

import { redirect } from "next/navigation";
import { serverPost, serverPatch, serverFetch, serverDelete } from "./api";

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


export async function saveDevis(formData: FormData) {
  const client_id = formData.get("client_id") as string;
  const offre_id = formData.get("offre_id") as string;
  if (!client_id || !offre_id) redirect("/simulateur");

  const resultJson = formData.get("result_json") as string;
  if (!resultJson) redirect("/simulateur");

  const result = JSON.parse(resultJson);

  // Construire les options selectionnees pour le devis
  const optionsJson = formData.get("options_json") as string;
  const options = optionsJson ? JSON.parse(optionsJson) : [];

  const data = {
    client_id: Number(client_id),
    offre_id: Number(offre_id),
    mode_reglement: formData.get("mode") || "Comptant",
    plan_paiement: formData.get("plan") || "100%",
    prix_vente_final: result.prix_vente_final,
    total_prestations_ht: result.total_prestations_vente || "0",
    total_options_setup_ht: result.total_options_setup_vente || "0",
    total_pack_maintenance_ht: result.total_pack_maintenance_vente || "0",
    total_options_recurrent_ht: result.total_options_recurrent_vente || "0",
    remise_pct_setup: formData.get("remise_setup") || "0",
    remise_pct_recurrent: formData.get("remise_recurrent") || "0",
    remise_eur_setup: result.remise_eur_setup || "0",
    remise_eur_recurrent: result.remise_eur_recurrent || "0",
    marge_additionnelle: formData.get("marge_add") || "0",
    total_ht: result.prix_setup_affiche || "0",
    total_tva: result.total_setup_tva || "0",
    total_ttc: result.total_setup_ttc || "0",
    options: options.map((o: Record<string, unknown>) => ({
      option_id: o.option_id,
      code: o.code,
      nom: o.nom,
      type_ligne: o.type_ligne,
      quantite: o.quantite,
      prix_setup_ht: o.prix_vente_setup || "0",
      prix_mensuel_ht: o.prix_vente_mensuel || "0",
      inclus: o.statut === "Inclus",
    })),
  };

  await serverPost("/devis/", data);
  redirect("/devis");
}


export async function genererFactures(formData: FormData) {
  const devisId = formData.get("devis_id") as string;
  const retour = (formData.get("retour") as string) || "/factures";
  if (!devisId) redirect("/devis");

  let ok = false;
  try {
    await serverPost(`/devis/${devisId}/factures`, {});
    ok = true;
  } catch {
    ok = false;
  }
  redirect(ok ? retour : `${retour}${retour.includes("?") ? "&" : "?"}erreur=1`);
}


export async function changerStatut(formData: FormData) {
  const id = formData.get("devis_id") as string;
  const statut = formData.get("statut") as string;
  if (!id || !statut) redirect("/devis");
  await serverPatch(`/devis/${id}/statut`, { statut });
  redirect(`/devis/detail?id=${id}`);
}


export async function definirMiseEnLigne(formData: FormData) {
  const id = formData.get("devis_id") as string;
  const date = (formData.get("date_mise_en_ligne") as string) || null;
  if (!id) redirect("/devis");
  await serverPatch(`/devis/${id}/mise-en-ligne`, { date_mise_en_ligne: date });
  redirect(`/devis/detail?id=${id}`);
}


export async function genererFactureMaintenance(formData: FormData) {
  const id = formData.get("devis_id") as string;
  if (!id) redirect("/devis");
  let ok = false;
  try {
    await serverPost(`/devis/${id}/factures-maintenance`, {});
    ok = true;
  } catch {
    ok = false;
  }
  redirect(`/devis/detail?id=${id}${ok ? "" : "&maint_erreur=1"}`);
}


// Extrait le champ "detail" d'un message d'erreur API ("API 400: {\"detail\":\"...\"}")
function extraireDetail(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e);
  const i = msg.indexOf("{");
  if (i >= 0) {
    try {
      const obj = JSON.parse(msg.slice(i));
      if (obj?.detail) return String(obj.detail);
    } catch {}
  }
  return "Operation impossible.";
}

function ajouterParam(url: string, cle: string, valeur: string): string {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}${cle}=${encodeURIComponent(valeur)}`;
}


export async function archiverDevis(formData: FormData) {
  const id = formData.get("devis_id") as string;
  const retour = (formData.get("retour") as string) || "/devis";
  if (!id) redirect("/devis");
  try {
    await serverDelete(`/devis/${id}`);
  } catch (e) {
    redirect(ajouterParam(retour, "suppr_msg", extraireDetail(e)));
  }
  redirect("/devis");
}


export async function restaurerDevis(formData: FormData) {
  const id = formData.get("devis_id") as string;
  if (!id) redirect("/devis");
  await serverPost(`/devis/${id}/restaurer`, {});
  redirect("/devis?archives=1");
}


export async function archiverFacture(formData: FormData) {
  const id = formData.get("facture_id") as string;
  const retour = (formData.get("retour") as string) || "/factures";
  if (!id) redirect("/factures");
  try {
    await serverDelete(`/factures/${id}`);
  } catch (e) {
    redirect(ajouterParam(retour, "suppr_msg", extraireDetail(e)));
  }
  redirect(retour);
}


// Niveau 2 : annulation par avoir d'une facture emise. Exige la saisie du mot
// SUPPRIMER (acte comptable engageant).
export async function annulerFacture(formData: FormData) {
  const id = formData.get("facture_id") as string;
  const retour = (formData.get("retour") as string) || "/factures";
  const confirmation = ((formData.get("confirmation") as string) || "").trim();
  if (!id) redirect("/factures");
  if (confirmation !== "SUPPRIMER") {
    redirect(`/factures/confirmer?id=${id}&action=annuler&retour=${encodeURIComponent(retour)}&err=mot`);
  }
  try {
    await serverPost(`/factures/${id}/annuler`, {});
  } catch (e) {
    redirect(ajouterParam(retour, "suppr_msg", extraireDetail(e)));
  }
  redirect(retour);
}


// Niveau 3 : suppression DEFINITIVE depuis la corbeille. Exige le mot SUPPRIMER
// + la case "irreversible" cochee.
export async function supprimerDevisDefinitif(formData: FormData) {
  const id = formData.get("devis_id") as string;
  if (!id) redirect("/devis");
  const confirmation = ((formData.get("confirmation") as string) || "").trim();
  const comprends = formData.get("comprends");
  if (confirmation !== "SUPPRIMER" || !comprends) {
    redirect(`/devis/confirmer?id=${id}&mode=definitif&err=mot`);
  }
  try {
    await serverDelete(`/devis/${id}/definitif`);
  } catch (e) {
    redirect(`/devis/confirmer?id=${id}&mode=definitif&err=${encodeURIComponent(extraireDetail(e))}`);
  }
  redirect("/devis?archives=1");
}


export async function supprimerFactureDefinitif(formData: FormData) {
  const id = formData.get("facture_id") as string;
  if (!id) redirect("/factures");
  const confirmation = ((formData.get("confirmation") as string) || "").trim();
  const comprends = formData.get("comprends");
  if (confirmation !== "SUPPRIMER" || !comprends) {
    redirect(`/factures/confirmer?id=${id}&action=definitif&err=mot`);
  }
  try {
    await serverDelete(`/factures/${id}/definitif`);
  } catch (e) {
    redirect(`/factures/confirmer?id=${id}&action=definitif&err=${encodeURIComponent(extraireDetail(e))}`);
  }
  redirect("/factures?archives=1");
}


export async function restaurerFacture(formData: FormData) {
  const id = formData.get("facture_id") as string;
  if (!id) redirect("/factures");
  await serverPost(`/factures/${id}/restaurer`, {});
  redirect("/factures?archives=1");
}


// FONCTIONNALITE PREVUE, NON ACTIVEE (cf. HANDOFF, section envoi email).
// Tant que RESEND_API_KEY n'est pas configuree cote backend, l'appel renvoie une
// erreur "non configure" affichee via suppr_msg ; aucun email ne part.
export async function envoyerFacture(formData: FormData) {
  const id = formData.get("facture_id") as string;
  const retour = (formData.get("retour") as string) || "/factures";
  if (!id) redirect("/factures");
  try {
    await serverPost(`/factures/${id}/envoyer`, {});
  } catch (e) {
    redirect(ajouterParam(retour, "suppr_msg", extraireDetail(e)));
  }
  redirect(ajouterParam(retour, "envoye", "1"));
}
