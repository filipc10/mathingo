// Mirror of DISPLAY_NAME_PATTERN in backend/app/schemas/auth.py.
// Keep in sync if either side changes.
export const DISPLAY_NAME_REGEX = /^[A-Za-z0-9_.\-]+$/;

export const DISPLAY_NAME_HINT =
  "3–30 znaků, povolená jsou písmena bez diakritiky, čísla, tečka, podtržítko a pomlčka.";

export function validateDisplayName(value: string): string | null {
  if (value.length < 3 || value.length > 30) {
    return "Přezdívka musí mít 3 až 30 znaků.";
  }
  if (!DISPLAY_NAME_REGEX.test(value)) {
    return DISPLAY_NAME_HINT;
  }
  return null;
}
