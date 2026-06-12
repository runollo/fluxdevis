// Helpers d'affichage TOLERANTS aux valeurs invalides : evitent les "NaN €" et
// "Invalid Date" qui cassent visuellement une page quand une donnee manque ou est
// malformee. A utiliser partout a la place des Number()/new Date() bruts.

/** Montant en euros. Valeur absente ou non numerique -> "—" (jamais "NaN €"). */
export function eur(v: number | string | null | undefined): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

/** Nombre sur. Valeur non finie -> 0 (evite les calculs qui propagent NaN). */
export function num(v: unknown): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

/** Date au format fr. Vide ou invalide -> "—" (jamais "Invalid Date"). */
export function dateFr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleDateString("fr-FR");
}
