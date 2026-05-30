import { serverFetch, type Offre } from "@/lib/api";
import OffreForm from "./OffreForm";

export const dynamic = "force-dynamic";

// Server Component : charge l'offre a editer, puis delegue le formulaire
// (avec apercu temps reel de la marge) au Client Component OffreForm.
export default async function OffreEditPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const { id } = await searchParams;
  let offre: Offre | null = null;

  if (id) {
    try {
      offre = await serverFetch<Offre>(`/offres/${id}`);
    } catch { /* nouvelle offre */ }
  }

  return <OffreForm offre={offre} />;
}
