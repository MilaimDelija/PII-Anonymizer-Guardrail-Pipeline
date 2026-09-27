from src.checksums_de import (
    deutsche_iban_gueltig,
    iban_pruefziffer_gueltig,
    personalausweisnummer_pruefziffer_gueltig,
    rentenversicherungsnummer_pruefziffer_gueltig,
    steuer_id_pruefziffer_gueltig,
)


def test_deutsche_iban_musterbeispiel_ist_gueltig():
    assert deutsche_iban_gueltig("DE89370400440532013000") is True


def test_deutsche_iban_mit_leerzeichen_wird_erkannt():
    assert deutsche_iban_gueltig("DE89 3704 0044 0532 0130 00") is True


def test_deutsche_iban_mit_falscher_pruefziffer_ist_ungueltig():
    assert deutsche_iban_gueltig("DE89370400440532013001") is False


def test_deutsche_iban_mit_falscher_laenderkennung_wird_abgelehnt():
    assert deutsche_iban_gueltig("FR1420041010050500013M02606") is False


def test_generische_iban_pruefung_funktioniert_laenderuebergreifend():
    # Oesterreichisches Musterbeispiel, ebenfalls Mod-97-Verfahren.
    assert iban_pruefziffer_gueltig("AT611904300234573201") is True


def test_steuer_id_gueltiges_beispiel():
    assert steuer_id_pruefziffer_gueltig("65929970489") is True


def test_steuer_id_mit_falscher_pruefziffer():
    assert steuer_id_pruefziffer_gueltig("65929970480") is False


def test_steuer_id_mit_fuehrender_null_ist_ungueltig():
    assert steuer_id_pruefziffer_gueltig("05929970489") is False


def test_steuer_id_mit_falscher_laenge():
    assert steuer_id_pruefziffer_gueltig("659299704") is False


def test_personalausweisnummer_gueltiges_beispiel():
    assert personalausweisnummer_pruefziffer_gueltig("L01X00T471") is True


def test_personalausweisnummer_mit_falscher_pruefziffer():
    assert personalausweisnummer_pruefziffer_gueltig("L01X00T470") is False


def test_personalausweisnummer_mit_nicht_erlaubtem_buchstaben():
    assert personalausweisnummer_pruefziffer_gueltig("A01X00T471") is False


def test_rentenversicherungsnummer_gueltiges_beispiel():
    assert rentenversicherungsnummer_pruefziffer_gueltig("15070649C103") is True


def test_rentenversicherungsnummer_mit_falscher_pruefziffer():
    assert rentenversicherungsnummer_pruefziffer_gueltig("15070649C104") is False


def test_rentenversicherungsnummer_mit_unplausiblem_geburtsdatum():
    assert rentenversicherungsnummer_pruefziffer_gueltig("15329649C103") is False
