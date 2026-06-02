import { serverFetch, type Offre, type OptionStatut } from "@/lib/api";
import OffreForm from "./OffreForm";
import OffreInclusionsEditor from "./OffreInclusionsEditor";

export const dynamic = "force-dynamic";

// Server Component : charge l'offre a editer, puis delegue le formulaire
// (avec apercu temps reel de la marge) au Client Component OffreForm. Pour une
// offre existante, charge aussi la liste des options avec leur statut afin
// d'editer les options incluses d'office.
export default async function OffreEditPage(
  { searchParams }: { searchParams: Promise<{ id?: string; incl_maj?: string }> }
) {
  const { id, incl_maj } = await searchParams;
  let offre: Offre | null = null;
  let options: OptionStatut[] = [];

  if (id) {
    try {
      offre = await serverFetch<Offre>(`/offres/${id}`);
    } catch { /* nouvelle offre */ }
    if (offre) {
      try {
        options = await serverFetch<OptionStatut[]>(`/offres/${id}/options`);
      } catch { /* pas d'options : on n'affiche pas l'editeur */ }
    }
  }

  return (
    <>
      {incl_maj && (
        <div className="max-w-2xl mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          Options incluses enregistrees.
        </div>
      )}
      <OffreForm offre={offre} />
      {offre && options.length > 0 && (
        <OffreInclusionsEditor offreId={offre.id} options={options} />
      )}
    </>
  );
}
