#!/usr/bin/env python3
"""Pseudonimiseer een CSV-dossierexport vóórdat die aan de AI-agent wordt gegeven.

Gebruik:
    python3 scripts/pseudonimiseer.py data/inbox/dossiers.csv

Resultaat:
    data/inbox/dossiers.pseudo.csv   -> veilig voor trap 1-verwerking
    data/sleutels/dossiers.sleutel.csv -> vertaaltabel code -> origineel (blijft lokaal)

Werkwijze:
- Kolommen waarvan de naam op een persoonsgegeven duidt worden GECODEERD
  (P0001, P0002, ...) of, voor contact-/nummervelden, VERWIJDERD.
- Alle overige celwaarden worden gescand op BSN-achtige nummers
  (9 cijfers die aan de elfproef voldoen) en e-mailadressen; treffers
  worden gemaskeerd.

Draai dit lokaal op de Mac Mini. De sleuteltabel verlaat de machine nooit.
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path

# Kolomnamen (genormaliseerd, zonder accenten/hoofdletters) die een
# persoonsgegeven bevatten. "codeer": waarde vervangen door een code die via
# de sleuteltabel herleidbaar blijft. "verwijder": waarde volledig weglaten.
CODEER_KOLOMMEN = {
    "naam", "voornaam", "voornamen", "achternaam", "tussenvoegsel",
    "partner", "partnernaam", "wederpartij", "client", "clientnaam",
    "verkoper", "koper", "comparant", "name", "firstname", "lastname",
}
VERWIJDER_KOLOMMEN = {
    "adres", "straat", "huisnummer", "postcode", "woonplaats", "plaats",
    "email", "emailadres", "mailadres", "telefoon", "telefoonnummer",
    "mobiel", "bsn", "burgerservicenummer", "geboortedatum", "geboorteplaats",
    "iban", "rekeningnummer", "address", "city", "phone", "birthdate",
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
NEGEN_CIJFERS_RE = re.compile(r"(?<!\d)(\d{9})(?!\d)")


def normaliseer(kolomnaam: str) -> str:
    s = unicodedata.normalize("NFKD", kolomnaam).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def is_bsn(nummer: str) -> bool:
    """Elfproef voor BSN: (9*a + 8*b + ... + 2*h - 1*i) deelbaar door 11."""
    cijfers = [int(c) for c in nummer]
    som = sum(c * g for c, g in zip(cijfers, [9, 8, 7, 6, 5, 4, 3, 2, -1]))
    return som % 11 == 0 and som > 0


def maskeer_vrije_tekst(waarde: str) -> str:
    waarde = EMAIL_RE.sub("[email verwijderd]", waarde)
    return NEGEN_CIJFERS_RE.sub(
        lambda m: "[BSN verwijderd]" if is_bsn(m.group(1)) else m.group(1), waarde
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    bron = Path(sys.argv[1])
    if not bron.is_file():
        print(f"Bestand niet gevonden: {bron}")
        return 1

    basis = bron.stem
    doel = bron.with_name(f"{basis}.pseudo.csv")
    sleutelmap = Path(__file__).resolve().parent.parent / "data" / "sleutels"
    sleutelmap.mkdir(parents=True, exist_ok=True)
    sleutelbestand = sleutelmap / f"{basis}.sleutel.csv"

    codes: dict[str, str] = {}  # origineel -> code (zelfde persoon = zelfde code)

    def code_voor(origineel: str) -> str:
        sleutel = origineel.strip()
        if sleutel not in codes:
            codes[sleutel] = f"P{len(codes) + 1:04d}"
        return codes[sleutel]

    with bron.open(newline="", encoding="utf-8-sig") as f:
        lezer = csv.reader(f)
        rijen = list(lezer)
    if not rijen:
        print("Leeg bestand.")
        return 1

    kop = rijen[0]
    acties = []  # per kolom: "codeer" | "verwijder" | "scan"
    for naam in kop:
        genorm = normaliseer(naam)
        if genorm in CODEER_KOLOMMEN:
            acties.append("codeer")
        elif genorm in VERWIJDER_KOLOMMEN:
            acties.append("verwijder")
        else:
            acties.append("scan")

    behouden = [i for i, a in enumerate(acties) if a != "verwijder"]
    with doel.open("w", newline="", encoding="utf-8") as f:
        schrijver = csv.writer(f)
        schrijver.writerow([kop[i] for i in behouden])
        for rij in rijen[1:]:
            rij = rij + [""] * (len(kop) - len(rij))
            uit = []
            for i in behouden:
                waarde = rij[i]
                if acties[i] == "codeer" and waarde.strip():
                    uit.append(code_voor(waarde))
                else:
                    uit.append(maskeer_vrije_tekst(waarde))
            schrijver.writerow(uit)

    with sleutelbestand.open("w", newline="", encoding="utf-8") as f:
        schrijver = csv.writer(f)
        schrijver.writerow(["code", "origineel"])
        for origineel, code in sorted(codes.items(), key=lambda x: x[1]):
            schrijver.writerow([code, origineel])

    verwijderd = [kop[i] for i, a in enumerate(acties) if a == "verwijder"]
    gecodeerd = [kop[i] for i, a in enumerate(acties) if a == "codeer"]
    print(f"Geschreven : {doel}")
    print(f"Sleutels   : {sleutelbestand}  ({len(codes)} personen/namen gecodeerd)")
    print(f"Verwijderde kolommen: {', '.join(verwijderd) or '-'}")
    print(f"Gecodeerde kolommen : {', '.join(gecodeerd) or '-'}")
    print("Controleer het resultaat steekproefsgewijs voordat je het aan de agent geeft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
