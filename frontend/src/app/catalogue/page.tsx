import { serverFetch, type Offre, type Option } from "@/lib/api";
import CatalogueClient from "./CatalogueClient";

export const dynamic = "force-dynamic";

export default async function CataloguePage() {
  let offres: Offre[] = [];
  let options: Option[] = [];
  let error = "";

  try {
    [offres, options] = await Promise.all([
      serverFetch<Offre[]>("/offres/"),
      serverFetch<Option[]>("/options/"),
    ]);
  } catch (e) {
    error = String(e);
  }

  if (error) {
    return <p className="text-red-600 p-4">Erreur : {error}</p>;
  }

  return <CatalogueClient offres={offres} options={options} />;
}
