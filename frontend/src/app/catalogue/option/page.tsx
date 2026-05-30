import { serverFetch, type Option } from "@/lib/api";
import OptionForm from "./OptionForm";

export const dynamic = "force-dynamic";

// Server Component : charge l'option a editer, puis delegue le formulaire
// (avec apercu temps reel des prix/marge) au Client Component OptionForm.
export default async function OptionEditPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const params = await searchParams;
  const id = params.id;
  let option: Option | null = null;

  if (id) {
    try {
      option = await serverFetch<Option>(`/options/${id}`);
    } catch { /* nouvelle option */ }
  }

  return <OptionForm option={option} />;
}
