import { vocative as voc } from "czech-vocative";

/**
 * Převádí české jméno do pátého pádu (vokativu).
 *
 * Tenký wrapper nad knihovnou czech-vocative s graceful fallback
 * na nominativ pro hraniční případy (krátké stringy, throw z knihovny).
 *
 *   vocative("Filip")   // "Filipe"
 *   vocative("Pavel")   // "Pavle"
 *   vocative("Tomáš")   // "Tomáši"
 *   vocative("Anna")    // "Anno"
 *   vocative("Marie")   // "Marie"
 *   vocative("Mateusz") // "Mateuszi" (knihovna pokrývá i cizí jména)
 */
export function vocative(name: string): string {
  if (!name || name.length < 2) return name;
  try {
    return voc(name);
  } catch {
    return name;
  }
}
