"""Pruefziffernverfahren fuer deutsche Identifikationsnummern.

Die Funktionen in diesem Modul pruefen ausschliesslich die mathematische
Gueltigkeit einer Kennung, nicht deren tatsaechliche Existenz oder Zuordnung
zu einer realen Person. Sie dienen als Filter innerhalb der Erkennungslogik,
um aus einer Zeichenkette mit passendem Format jene Faelle auszusondern, die
schon rein rechnerisch keine gueltige Nummer sein koennen.

Fuer die Steuerliche Identifikationsnummer wird ausschliesslich das in
Paragraph 139b AO vorgesehene Pruefziffernverfahren nach ISO/IEC 7064
(Mod 11,10) abgebildet. Die zusaetzliche Vergaberegel, wonach unter den
ersten zehn Ziffern genau eine Ziffer zwei- oder unter bestimmten
Bedingungen dreifach vorkommen muss, betrifft die Zuteilung durch das
Bundeszentralamt fuer Steuern und wird hier nicht geprueft; eine Nummer
kann die Pruefziffer erfuellen, ohne tatsaechlich vergeben worden zu sein.
"""

from __future__ import annotations


def iban_pruefziffer_gueltig(iban: str) -> bool:
    """Prueft eine IBAN nach dem international genutzten Mod-97-Verfahren."""

    bereinigt = "".join(iban.split()).upper()
    if len(bereinigt) < 5 or not bereinigt[:2].isalpha():
        return False

    umgestellt = bereinigt[4:] + bereinigt[:4]
    ziffernfolge_teile = []
    for zeichen in umgestellt:
        if zeichen.isdigit():
            ziffernfolge_teile.append(zeichen)
        elif zeichen.isalpha():
            ziffernfolge_teile.append(str(ord(zeichen) - ord("A") + 10))
        else:
            return False

    ziffernfolge = "".join(ziffernfolge_teile)
    return int(ziffernfolge) % 97 == 1


def deutsche_iban_gueltig(iban: str) -> bool:
    """Prueft speziell eine deutsche IBAN (Laenderkennung DE, 22 Stellen)."""

    bereinigt = "".join(iban.split()).upper()
    if len(bereinigt) != 22 or not bereinigt.startswith("DE"):
        return False
    return iban_pruefziffer_gueltig(bereinigt)


def steuer_id_pruefziffer_gueltig(nummer: str) -> bool:
    """Prueft die Steuerliche Identifikationsnummer nach ISO/IEC 7064 Mod 11,10."""

    if len(nummer) != 11 or not nummer.isdigit() or nummer[0] == "0":
        return False

    basisziffern = [int(z) for z in nummer[:10]]
    pruefziffer_soll = int(nummer[10])

    produkt = 10
    for ziffer in basisziffern:
        summe = (ziffer + produkt) % 10
        if summe == 0:
            summe = 10
        produkt = (summe * 2) % 11

    pruefziffer = (11 - produkt) % 10
    return pruefziffer == pruefziffer_soll


_ERLAUBTE_BUCHSTABEN_PERSONALAUSWEIS = "CFGHJKLMNPRTVWXYZ"


def personalausweisnummer_pruefziffer_gueltig(nummer: str) -> bool:
    """Prueft die Dokumentennummer eines Personalausweises (Format seit 11/2010).

    Das Verfahren entspricht der bei Ausweisdokumenten ueblichen
    Gewichtung 7-3-1: jede der ersten neun Stellen wird mit ihrem
    Gewicht multipliziert, von jedem Produkt wird die Einerstelle
    gebildet, die neun Einerstellen werden addiert, und die Einerstelle
    dieser Summe ergibt die Pruefziffer an zehnter Stelle.
    """

    nummer = nummer.upper()
    if len(nummer) != 10 or not nummer[9].isdigit():
        return False

    gewichte = (7, 3, 1)
    summe = 0
    for index, zeichen in enumerate(nummer[:9]):
        if zeichen.isdigit():
            wert = int(zeichen)
        elif zeichen in _ERLAUBTE_BUCHSTABEN_PERSONALAUSWEIS:
            wert = ord(zeichen) - ord("A") + 10
        else:
            return False
        produkt = wert * gewichte[index % 3]
        summe += produkt % 10

    pruefziffer = summe % 10
    return pruefziffer == int(nummer[9])


def rentenversicherungsnummer_pruefziffer_gueltig(nummer: str) -> bool:
    """Prueft die zwoelfstellige Rentenversicherungsnummer (Versicherungsnummer).

    Aufbau: zwei Stellen Bereichsnummer, sechs Stellen Geburtsdatum
    (TTMMJJ), ein Buchstabe als Anfangsbuchstabe des Geburtsnamens,
    zwei Stellen Seriennummer, eine Pruefziffer. Fuer die Berechnung
    wird der Buchstabe in seinen Positionswert im Alphabet (A=01 bis
    Z=26) umgewandelt, wodurch sich eine zwoelfstellige Ziffernfolge
    ergibt, die mit den Gewichten 2, 1, 2, 5, 7, 1, 2, 1, 2, 1, 2, 1
    verrechnet wird.
    """

    nummer = nummer.upper()
    if len(nummer) != 12:
        return False

    bereich, geburtsdatum, buchstabe, seriennummer, pruefziffer_zeichen = (
        nummer[0:2],
        nummer[2:8],
        nummer[8],
        nummer[9:11],
        nummer[11],
    )

    if not (
        bereich.isdigit()
        and geburtsdatum.isdigit()
        and seriennummer.isdigit()
        and pruefziffer_zeichen.isdigit()
        and buchstabe.isalpha()
    ):
        return False

    tag, monat = int(geburtsdatum[0:2]), int(geburtsdatum[2:4])
    if not (1 <= tag <= 31 and 1 <= monat <= 12):
        return False

    buchstabenwert = ord(buchstabe) - ord("A") + 1
    ziffernfolge = (
        [int(z) for z in bereich]
        + [int(z) for z in geburtsdatum]
        + [int(z) for z in f"{buchstabenwert:02d}"]
        + [int(z) for z in seriennummer]
    )
    gewichte = (2, 1, 2, 5, 7, 1, 2, 1, 2, 1, 2, 1)

    gesamtsumme = 0
    for ziffer, gewicht in zip(ziffernfolge, gewichte):
        produkt = ziffer * gewicht
        gesamtsumme += produkt // 10 + produkt % 10

    pruefziffer = gesamtsumme % 10
    return pruefziffer == int(pruefziffer_zeichen)
