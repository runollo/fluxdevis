"use server";

import { redirect } from "next/navigation";
import { serverPost, serverPatch } from "./api";

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
  const data: Record<string, unknown> = {
    raison_sociale: formData.get("raison_sociale"),
    adresse: formData.get("adresse") || null,
    code_postal: formData.get("code_postal") || null,
    ville: formData.get("ville") || null,
    interlocuteur: formData.get("interlocuteur") || null,
    telephone: formData.get("telephone") || null,
    email: formData.get("email") || null,
    siret: formData.get("siret") || null,
  };

  if (id) {
    await serverPatch(`/clients/${id}`, data);
  } else {
    await serverPost("/clients/", data);
  }
  redirect("/clients");
}
