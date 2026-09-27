from src.anonymizer import anonymisiere


def test_anonymisiere_erkennt_mehrere_kategorien_in_einem_text():
    text = (
        "Sehr geehrte Damen und Herren, mein Name ist Michael Schneider und "
        "meine E-Mail-Adresse lautet michael.schneider@beispielfirma.de. "
        "Sie erreichen mich auch unter 0176 55512345. Meine IBAN ist "
        "DE89 3704 0044 0532 0130 00 und meine Steuer-ID lautet 65929970489. "
        "Bitte fassen Sie diesen Text fuer mich zusammen."
    )

    ergebnis = anonymisiere(text)

    anonymisierter_text = ergebnis.anonymisierter_text
    assert "Michael Schneider" not in anonymisierter_text
    assert "michael.schneider@beispielfirma.de" not in anonymisierter_text
    assert "0176 55512345" not in anonymisierter_text
    assert "DE89 3704 0044 0532 0130 00" not in anonymisierter_text
    assert "65929970489" not in anonymisierter_text

    assert "[ANONYMISIERT:NAME]" in anonymisierter_text
    assert "[ANONYMISIERT:E-MAIL]" in anonymisierter_text
    assert "[ANONYMISIERT:TELEFON]" in anonymisierter_text
    assert "[ANONYMISIERT:IBAN]" in anonymisierter_text
    assert "[ANONYMISIERT:STEUER-ID]" in anonymisierter_text

    gefundene_typen = {e.entitaetstyp for e in ergebnis.erkennungen}
    assert gefundene_typen == {
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "IBAN_CODE",
        "STEUER_ID_DE",
    }


def test_anonymisiere_laesst_text_ohne_personenbezogene_daten_unveraendert():
    text = "Der Termin findet naechste Woche im Besprechungsraum statt."

    ergebnis = anonymisiere(text)

    assert ergebnis.anonymisierter_text == text
    assert ergebnis.erkennungen == []


def test_anonymisiere_beschraenkt_erkennung_auf_uebergebene_entitaeten():
    text = "Anna Beispiel erreichen Sie unter anna.beispiel@firma.de."

    ergebnis = anonymisiere(text, entitaeten=["EMAIL_ADDRESS"])

    # PERSON ist nicht in der uebergebenen Liste enthalten und darf daher
    # trotz vorhandenem Namen nicht ersetzt werden.
    assert "Anna Beispiel" in ergebnis.anonymisierter_text
    assert "anna.beispiel@firma.de" not in ergebnis.anonymisierter_text
    assert [e.entitaetstyp for e in ergebnis.erkennungen] == ["EMAIL_ADDRESS"]


def test_anonymisiere_erkennt_kreditkarte_und_personalausweisnummer():
    # Die Kreditkartenpruefung ist in Presidio standardmaessig nur fuer
    # Englisch registriert; dieser Test sichert ab, dass die manuell mit
    # supported_language="de" registrierte Instanz tatsaechlich greift.
    text = (
        "Bitte notieren Sie die Kreditkartennummer 4111111111111111 und "
        "die Ausweisnummer L01X00T471."
    )

    ergebnis = anonymisiere(text)

    anonymisierter_text = ergebnis.anonymisierter_text
    assert "4111111111111111" not in anonymisierter_text
    assert "L01X00T471" not in anonymisierter_text
    assert "[ANONYMISIERT:KREDITKARTE]" in anonymisierter_text
    assert "[ANONYMISIERT:AUSWEISNUMMER]" in anonymisierter_text

    gefundene_typen = {e.entitaetstyp for e in ergebnis.erkennungen}
    assert gefundene_typen == {"CREDIT_CARD", "PERSONALAUSWEISNUMMER_DE"}


def test_anonymisiere_loest_ueberlappende_erkennungen_eindeutig_auf():
    # Eine elfstellige Steuer-ID passt zufaellig auch auf das generische
    # Muster einer Telefonnummer. Die Erkennungsliste darf pro Textstelle
    # trotzdem nur einen Eintrag enthalten, nicht zwei widersprechende.
    text = "Die Steuer-ID lautet 65929970489 und ist wichtig."

    ergebnis = anonymisiere(text)

    treffer_an_dieser_stelle = [
        e for e in ergebnis.erkennungen if e.start == 21 and e.ende == 32
    ]
    assert len(treffer_an_dieser_stelle) == 1
    assert treffer_an_dieser_stelle[0].entitaetstyp == "STEUER_ID_DE"
    assert ergebnis.anonymisierter_text == (
        "Die Steuer-ID lautet [ANONYMISIERT:STEUER-ID] und ist wichtig."
    )


def test_anonymisiere_ersetzt_ungueltige_pruefziffer_nicht_als_steuer_id():
    # Eine elfstellige Zahl mit falscher Pruefziffer darf nicht als
    # Steuer-ID markiert werden. Das generische PHONE_NUMBER-Muster passt
    # zufaellig ebenfalls auf diese Ziffernfolge, sodass die Zahl weiterhin
    # ersetzt wird, aber unter der richtigen, weniger spezifischen Kategorie.
    text = "Die Nummer 65929970480 wurde nicht als Steuer-ID erkannt."

    ergebnis = anonymisiere(text)

    assert "65929970480" not in ergebnis.anonymisierter_text
    assert all(e.entitaetstyp != "STEUER_ID_DE" for e in ergebnis.erkennungen)
    assert any(e.entitaetstyp == "PHONE_NUMBER" for e in ergebnis.erkennungen)
