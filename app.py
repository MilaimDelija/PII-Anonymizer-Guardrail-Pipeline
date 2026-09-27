"""PII Anonymizer & Guardrail-Pipeline — Streamlit-Oberflaeche.

Zeigt den in `src/anonymizer.py` implementierten Erkennungs- und
Ersetzungsschritt an einem eingegebenen Text: Bevor ein Prompt an eine
externe KI-Anwendung mit eigener Programmierschnittstelle geschickt wird,
laesst er sich hier zuerst durch dieselbe Pipeline schicken, die auch
programmatisch (etwa aus einem vorgeschalteten Skript heraus) aufgerufen
werden kann.
"""

from __future__ import annotations

import streamlit as st

from src.anonymizer import STANDARD_ENTITAETEN, anonymisiere

st.set_page_config(page_title="PII Anonymizer", page_icon="🛡️", layout="wide")

_LABEL_JE_ENTITAET = {
    "PERSON": "Namen",
    "EMAIL_ADDRESS": "E-Mail-Adressen",
    "PHONE_NUMBER": "Telefonnummern",
    "CREDIT_CARD": "Kreditkartennummern",
    "IBAN_CODE": "IBAN",
    "STEUER_ID_DE": "Steuerliche Identifikationsnummer",
    "PERSONALAUSWEISNUMMER_DE": "Personalausweisnummer",
    "SVNR_DE": "Rentenversicherungsnummer (Sozialversicherung)",
}

_BEISPIELTEXT = (
    "Bitte fasse folgende Kundenanfrage zusammen: Sehr geehrtes Team, mein "
    "Name ist Sabine Hoffmann und ich schreibe Ihnen bezueglich meines "
    "Vertrags. Sie erreichen mich unter sabine.hoffmann@beispielmail.de "
    "oder telefonisch unter 030 55512345. Zur Identifikation nenne ich "
    "Ihnen meine IBAN DE89 3704 0044 0532 0130 00. Vielen Dank im Voraus."
)

st.title("PII Anonymizer & Guardrail-Pipeline")
st.caption(
    "Erkennt personenbezogene Angaben in einem Text und ersetzt sie durch Platzhalter, "
    "bevor der Text an eine externe KI-Anwendung uebergeben wird."
)

with st.expander("Hinweis zur Verwendung und zu den Grenzen dieses Werkzeugs"):
    st.write(
        "Die Erkennung beruht auf zwei Bausteinen: einem statistischen Named-Entity-"
        "Modell (spaCy, deutsches Sprachmodell) fuer Namen und aehnliche freie Angaben "
        "sowie regelbasierten Mustern mit Pruefziffernvalidierung fuer Formate wie IBAN, "
        "Steuer-ID, Personalausweisnummer oder Rentenversicherungsnummer. Das "
        "statistische Modell erkennt Namen nicht mit letzter Sicherheit: Es kann "
        "einzelne Namen uebersehen und gelegentlich eine andere grossgeschriebene "
        "Wortfolge faelschlich als Namen einordnen. Die Pruefziffernverfahren "
        "bestaetigen ausschliesslich die mathematische Gueltigkeit einer Nummer, nicht "
        "ihre tatsaechliche Zuordnung zu einer realen Person; bei der Steuer-ID wird "
        "zudem nur das Pruefziffernverfahren selbst abgebildet, nicht die zusaetzliche "
        "Vergaberegel des Bundeszentralamts fuer Steuern zur Ziffernwiederholung. Diese "
        "Ausgabe ersetzt daher keine manuelle Kontrolle bei besonders sensiblen "
        "Texten. Die unten angezeigte Liste der Erkennungen enthaelt die "
        "urspruenglichen, noch nicht anonymisierten Werte und sollte in einem "
        "produktiven Einsatz aus genau diesem Grund nicht protokolliert oder "
        "gespeichert werden."
    )

st.divider()

verfuegbare_entitaeten = [e for e in STANDARD_ENTITAETEN if e in _LABEL_JE_ENTITAET]

spalte_eingabe, spalte_auswahl = st.columns([3, 2])

with spalte_auswahl:
    st.subheader("Zu erkennende Kategorien")
    ausgewaehlte_labels = st.multiselect(
        "Kategorien",
        options=[_LABEL_JE_ENTITAET[e] for e in verfuegbare_entitaeten],
        default=[_LABEL_JE_ENTITAET[e] for e in verfuegbare_entitaeten],
        label_visibility="collapsed",
    )
    ausgewaehlte_entitaeten = [
        e for e in verfuegbare_entitaeten if _LABEL_JE_ENTITAET[e] in ausgewaehlte_labels
    ]

with spalte_eingabe:
    st.subheader("Eingabetext")
    text = st.text_area(
        "Text",
        value=_BEISPIELTEXT,
        height=220,
        label_visibility="collapsed",
    )

st.divider()

if not text.strip():
    st.info("Bitte einen Text eingeben, um die Erkennung auszufuehren.")
elif not ausgewaehlte_entitaeten:
    st.warning("Es ist keine Kategorie ausgewaehlt. Es wird nichts erkannt oder ersetzt.")
else:
    ergebnis = anonymisiere(text, entitaeten=ausgewaehlte_entitaeten)

    st.header("Ergebnis")

    spalte_ergebnis_links, spalte_ergebnis_rechts = st.columns(2)
    with spalte_ergebnis_links:
        st.markdown("**Anonymisierter Text**")
        st.text_area(
            "Anonymisierter Text",
            value=ergebnis.anonymisierter_text,
            height=220,
            label_visibility="collapsed",
            disabled=True,
        )
        st.download_button(
            "Anonymisierten Text herunterladen",
            data=ergebnis.anonymisierter_text,
            file_name="anonymisierter_text.txt",
            mime="text/plain",
        )

    with spalte_ergebnis_rechts:
        st.markdown("**Erkannte Angaben**")
        if ergebnis.erkennungen:
            zeilen = [
                {
                    "Kategorie": _LABEL_JE_ENTITAET.get(e.entitaetstyp, e.entitaetstyp),
                    "Erkannter Text": e.erkannter_text,
                    "Score": e.score,
                }
                for e in ergebnis.erkennungen
            ]
            st.table(zeilen)
        else:
            st.write("In diesem Text wurde in den ausgewaehlten Kategorien nichts erkannt.")
