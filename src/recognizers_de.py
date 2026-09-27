"""Deutsche Custom-Recognizer fuer Microsoft Presidio.

Presidio validiert IBAN bereits laenderuebergreifend ueber einen eigenen,
mitgelieferten Recognizer mit korrekter Mod-97-Pruefung; ein zusaetzlicher
Recognizer dafuer waere reine Doppelarbeit und wird hier bewusst nicht
angelegt. Was in der Standardauslieferung tatsaechlich fehlt, sind
Formate, die es nur im deutschen Rechtsraum gibt: die Steuerliche
Identifikationsnummer, die Dokumentennummer des Personalausweises und die
Rentenversicherungsnummer. Die folgenden Klassen ergaenzen genau diese drei
Formate, jeweils mit einer Mustererkennung per regulaerem Ausdruck und einer
anschliessenden Pruefziffernvalidierung aus checksums_de, sodass nicht jede
zufaellige Ziffernfolge mit passender Laenge als Treffer gewertet wird.
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer

from src.checksums_de import (
    personalausweisnummer_pruefziffer_gueltig,
    rentenversicherungsnummer_pruefziffer_gueltig,
    steuer_id_pruefziffer_gueltig,
)


class SteuerIdRecognizer(PatternRecognizer):
    """Erkennt die elfstellige Steuerliche Identifikationsnummer."""

    PATTERNS = [Pattern(name="steuer_id", regex=r"\b\d{11}\b", score=0.2)]

    CONTEXT = [
        "steuer-id",
        "steuerliche identifikationsnummer",
        "identifikationsnummer",
        "idnr",
        "steueridentifikationsnummer",
    ]

    def __init__(self):
        super().__init__(
            supported_entity="STEUER_ID_DE",
            supported_language="de",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )

    def validate_result(self, pattern_text: str):
        try:
            return steuer_id_pruefziffer_gueltig(pattern_text)
        except (ValueError, TypeError):
            return False


class PersonalausweisnummerRecognizer(PatternRecognizer):
    """Erkennt die Dokumentennummer eines Personalausweises (Format seit 11/2010)."""

    PATTERNS = [
        Pattern(
            name="personalausweisnummer",
            regex=r"\b[C-HJ-NPRTVWXYZ][A-Z0-9]{8}\d\b",
            score=0.25,
        )
    ]

    CONTEXT = ["personalausweis", "ausweisnummer", "dokumentennummer", "ausweisdokument"]

    def __init__(self):
        super().__init__(
            supported_entity="PERSONALAUSWEISNUMMER_DE",
            supported_language="de",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )

    def validate_result(self, pattern_text: str):
        try:
            return personalausweisnummer_pruefziffer_gueltig(pattern_text)
        except (ValueError, TypeError):
            return False


class RentenversicherungsnummerRecognizer(PatternRecognizer):
    """Erkennt die zwoelfstellige Rentenversicherungsnummer (Sozialversicherungsnummer)."""

    PATTERNS = [
        Pattern(
            name="rentenversicherungsnummer",
            regex=r"\b\d{8}[A-Za-z]\d{3}\b",
            score=0.3,
        )
    ]

    CONTEXT = [
        "versicherungsnummer",
        "rentenversicherungsnummer",
        "sozialversicherungsnummer",
        "svnr",
    ]

    def __init__(self):
        super().__init__(
            supported_entity="SVNR_DE",
            supported_language="de",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )

    def validate_result(self, pattern_text: str):
        try:
            return rentenversicherungsnummer_pruefziffer_gueltig(pattern_text)
        except (ValueError, TypeError):
            return False


def alle_deutschen_recognizer() -> list[PatternRecognizer]:
    """Gibt eine Instanz jedes deutschen Custom-Recognizers zurueck."""

    return [
        SteuerIdRecognizer(),
        PersonalausweisnummerRecognizer(),
        RentenversicherungsnummerRecognizer(),
    ]
