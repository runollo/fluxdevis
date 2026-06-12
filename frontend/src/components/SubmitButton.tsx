"use client";

// Bouton de soumission qui se desactive et affiche un libelle d'attente pendant
// que la Server Action du <form> parent s'execute (evite les doubles-soumissions
// et donne un retour visuel). A placer DANS un <form>. useFormStatus lit l'etat
// du formulaire ancetre le plus proche.

import { useFormStatus } from "react-dom";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  pendingLabel?: string;
};

export default function SubmitButton({ children, pendingLabel, className = "", disabled, ...rest }: Props) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending || disabled}
      aria-busy={pending}
      className={`${className} disabled:opacity-60 disabled:cursor-not-allowed`}
      {...rest}
    >
      {pending ? (pendingLabel ?? "Patientez…") : children}
    </button>
  );
}
