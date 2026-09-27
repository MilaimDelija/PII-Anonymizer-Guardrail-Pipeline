"""Smoke- und Verhaltenstests fuer die Streamlit-Oberflaeche (app.py).

Laeuft ohne Browser ueber Streamlits eigenes Testwerkzeug
(`streamlit.testing.v1.AppTest`), das die App headless ausfuehrt und die
gerenderten Elemente sowie deren Werte zur Pruefung bereitstellt.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PFAD = Path(__file__).resolve().parent.parent / "app.py"


def _app() -> AppTest:
    at = AppTest.from_file(str(_APP_PFAD))
    at.run()
    assert not at.exception
    return at


def _eingabefeld(at: AppTest):
    # Es gibt zwei text_area-Elemente: das editierbare Eingabefeld und das
    # deaktivierte Ausgabefeld fuer den anonymisierten Text.
    return next(t for t in at.text_area if not t.disabled)


def _ausgabefeld(at: AppTest):
    return next(t for t in at.text_area if t.disabled)


def test_app_startet_ohne_fehler_und_zeigt_ergebnis_zum_beispieltext():
    at = _app()
    assert any(h.value == "Ergebnis" for h in at.header)
    # Der voreingestellte Beispieltext enthaelt einen Namen und eine
    # E-Mail-Adresse, die im anonymisierten Text nicht mehr vorkommen duerfen.
    ausgabe = _ausgabefeld(at).value
    assert "Sabine Hoffmann" not in ausgabe
    assert "sabine.hoffmann@beispielmail.de" not in ausgabe
    assert "[ANONYMISIERT:NAME]" in ausgabe
    assert "[ANONYMISIERT:E-MAIL]" in ausgabe


def test_leerer_text_zeigt_hinweis_statt_ergebnis():
    at = _app()
    _eingabefeld(at).set_value("   ")
    at.run()
    assert any("Bitte einen Text eingeben" in i.value for i in at.info)
    assert not any(h.value == "Ergebnis" for h in at.header)


def test_abwahl_aller_kategorien_zeigt_warnung():
    at = _app()
    at.multiselect[0].set_value([])
    at.run()
    assert any("keine Kategorie ausgewaehlt" in w.value for w in at.warning)


def test_abwahl_der_kategorie_namen_laesst_namen_im_text_stehen():
    at = _app()
    kategorien = list(at.multiselect[0].value)
    kategorien.remove("Namen")
    at.multiselect[0].set_value(kategorien)
    at.run()
    ausgabe = _ausgabefeld(at).value
    assert "Sabine Hoffmann" in ausgabe
    assert "[ANONYMISIERT:E-MAIL]" in ausgabe


def test_eigener_text_mit_iban_wird_erkannt_und_ersetzt():
    at = _app()
    _eingabefeld(at).set_value(
        "Fuer die Ueberweisung nutzen Sie bitte die IBAN DE89 3704 0044 0532 0130 00."
    )
    at.run()
    ausgabe = _ausgabefeld(at).value
    assert "DE89 3704 0044 0532 0130 00" not in ausgabe
    assert "[ANONYMISIERT:IBAN]" in ausgabe


def test_download_button_fuer_anonymisierten_text_ist_vorhanden():
    at = _app()
    assert any(
        "Anonymisierten Text herunterladen" in db.label for db in at.download_button
    )
