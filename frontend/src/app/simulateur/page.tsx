import { serverFetch, type Offre } from "@/lib/api";
import SimulateurClient from "./SimulateurClient";

export const dynamic = "force-dynamic";

export default async function SimulateurPage() {
  let offres: Offre[] = [];
  let error = "";

  try {
    offres = await serverFetch<Offre[]>("/offres/");
  } catch (e) {
    error = String(e);
  }

  if (error) {
    return <p className="text-red-600 p-4">Erreur : {error}</p>;
  }

  return <SimulateurClient offres={offres} />;
}
