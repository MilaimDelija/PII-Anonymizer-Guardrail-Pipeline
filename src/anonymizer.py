"""Kernpipeline der Anonymisierung: Presidio-Analyse plus Ersetzung.

Der Ablauf entspricht dem Einsatzzweck aus der Projektbeschreibung: bevor
ein Prompt an eine externe KI-Anwendung mit eigener Programmierschnittstelle
geht, laeuft der Text zunaechst durch diese Pipeline. Erkannte Angaben
werden durch einen Platzhalter ersetzt, der die Kategorie benennt, ohne den
Inhalt preiszugeben, und jede Erkennung wird zusammen mit ihrer Position
und ihrem Score zurueckgegeben, damit nachvollziehbar bleibt, was ersetzt
wurde und wie sicher die Erkennung war.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from src.recognizers_de import alle_deutschen_recognizer

SPRACHE = "de"

# Presidio erkennt ueber die eingebauten Recognizer und das spaCy-Modell noch
# weitere Kategorien (etwa URL, IP-Adresse oder Datum). Diese Auswahl
# beschraenkt die Ausgabe auf jene Kategorien, die im Anwendungsfall dieses
# Projekts, dem Versand von Text an eine externe KI-Anwendung, tatsaechlich
# als personenbezogene Daten relevant sind.
STANDARD_ENTITAETEN = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "STEUER_ID_DE",
    "PERSONALAUSWEISNUMMER_DE",
    "SVNR_DE",
]

_PLATZHALTER = {
    "PERSON": "[ANONYMISIERT:NAME]",
    "EMAIL_ADDRESS": "[ANONYMISIERT:E-MAIL]",
    "PHONE_NUMBER": "[ANONYMISIERT:TELEFON]",
    "CREDIT_CARD": "[ANONYMISIERT:KREDITKARTE]",
    "IBAN_CODE": "[ANONYMISIERT:IBAN]",
    "STEUER_ID_DE": "[ANONYMISIERT:STEUER-ID]",
    "PERSONALAUSWEISNUMMER_DE": "[ANONYMISIERT:AUSWEISNUMMER]",
    "SVNR_DE": "[ANONYMISIERT:VERSICHERUNGSNUMMER]",
}


@dataclass
class Erkennung:
    """Eine einzelne von Presidio gefundene und ersetzte Angabe."""

    entitaetstyp: str
    erkannter_text: str
    start: int
    ende: int
    score: float


@dataclass
class AnonymisierungsErgebnis:
    anonymisierter_text: str
    erkennungen: list[Erkennung] = field(default_factory=list)


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    """Baut die Analyzer-Engine einmalig auf; das Laden des spaCy-Modells
    ist der teuerste Schritt und soll nicht bei jedem Aufruf wiederholt
    werden, insbesondere nicht bei jedem Rerun der Streamlit-Oberflaeche.
    """

    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": SPRACHE, "model_name": "de_core_news_sm"}],
        }
    )
    nlp_engine = provider.create_engine()

    engine = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[SPRACHE])
    # CreditCardRecognizer ist in Presidio standardmaessig nur fuer Englisch
    # registriert, obwohl die Luhn-Pruefung sprachunabhaengig ist.
    engine.registry.add_recognizer(CreditCardRecognizer(supported_language=SPRACHE))
    for recognizer in alle_deutschen_recognizer():
        engine.registry.add_recognizer(recognizer)
    return engine


@lru_cache(maxsize=1)
def _anonymizer_engine() -> AnonymizerEngine:
    return AnonymizerEngine()


def _entferne_ueberlappungen(
    treffer: list[RecognizerResult],
) -> list[RecognizerResult]:
    """Behaelt bei ueberlappenden Erkennungen nur jene mit dem hoechsten Score.

    Dieselbe Textstelle kann von mehr als einem Recognizer erfasst werden,
    etwa wenn eine elfstellige Steuer-ID gleichzeitig zum Muster einer
    Telefonnummer passt. Ohne diesen Schritt wuerde die Ergebnisliste
    zwei widersprechende Eintraege fuer dieselbe Stelle zeigen, waehrend
    tatsaechlich nur eine Ersetzung stattfindet.
    """

    nach_score_sortiert = sorted(treffer, key=lambda r: r.score, reverse=True)
    behalten: list[RecognizerResult] = []
    for kandidat in nach_score_sortiert:
        ueberlappt_bestehenden = any(
            kandidat.start < b.end and b.start < kandidat.end for b in behalten
        )
        if not ueberlappt_bestehenden:
            behalten.append(kandidat)
    return sorted(behalten, key=lambda r: r.start)


def anonymisiere(
    text: str, entitaeten: list[str] | None = None
) -> AnonymisierungsErgebnis:
    """Erkennt personenbezogene Daten in `text` und ersetzt sie durch Platzhalter.

    `entitaeten` erlaubt es, die Erkennung auf eine Teilmenge von
    STANDARD_ENTITAETEN einzuschraenken, etwa um in der Oberflaeche einzelne
    Kategorien gezielt abzuschalten.
    """

    if entitaeten is None:
        entitaeten = STANDARD_ENTITAETEN

    rohtreffer: list[RecognizerResult] = _analyzer().analyze(
        text=text, language=SPRACHE, entities=entitaeten
    )
    treffer = _entferne_ueberlappungen(rohtreffer)

    operatoren = {
        entitaet: OperatorConfig("replace", {"new_value": platzhalter})
        for entitaet, platzhalter in _PLATZHALTER.items()
    }

    ergebnis = _anonymizer_engine().anonymize(
        text=text, analyzer_results=treffer, operators=operatoren
    )

    erkennungen = [
        Erkennung(
            entitaetstyp=treffer_einzeln.entity_type,
            erkannter_text=text[treffer_einzeln.start : treffer_einzeln.end],
            start=treffer_einzeln.start,
            ende=treffer_einzeln.end,
            score=round(treffer_einzeln.score, 2),
        )
        for treffer_einzeln in treffer
    ]

    return AnonymisierungsErgebnis(
        anonymisierter_text=ergebnis.text, erkennungen=erkennungen
    )
