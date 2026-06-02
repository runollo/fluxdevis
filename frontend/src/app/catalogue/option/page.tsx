import { serverFetch, type Option, type ContenuPack } from "@/lib/api";
import OptionForm from "./OptionForm";
import PackContenuEditor from "./PackContenuEditor";

export const dynamic = "force-dynamic";

// Server Component : charge l'option a editer, puis delegue le formulaire
// (avec apercu temps reel des prix/marge) au Client Component OptionForm.
// Pour un pack de maintenance, charge aussi son contenu editable (descriptif)
// et affiche l'editeur dedie en dessous.
export default async function OptionEditPage(
  { searchParams }: { searchParams: Promise<{ id?: string; pack_maj?: string; pack_reset?: string }> }
) {
  const params = await searchParams;
  const id = params.id;
  let option: Option | null = null;
  let contenuPack: ContenuPack | null = null;

  if (id) {
    try {
      option = await serverFetch<Option>(`/options/${id}`);
    } catch { /* nouvelle option */ }
    if (option?.type_ligne === "PACK") {
      try {
        contenuPack = await serverFetch<ContenuPack>(`/options/${id}/contenu-pack`);
      } catch { /* pack hors referentiel : pas d'editeur de contenu */ }
    }
  }

  return (
    <>
      {(params.pack_maj || params.pack_reset) && (
        <div className="max-w-2xl mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          {params.pack_maj ? "Contenu du pack enregistre." : "Contenu du pack reinitialise au defaut."}
        </div>
      )}
      <OptionForm option={option} />
      {contenuPack && <PackContenuEditor data={contenuPack} />}
    </>
  );
}
