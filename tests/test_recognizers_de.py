from src.recognizers_de import (
    PersonalausweisnummerRecognizer,
    RentenversicherungsnummerRecognizer,
    SteuerIdRecognizer,
)


def test_steuer_id_recognizer_erkennt_gueltige_nummer_im_satz():
    recognizer = SteuerIdRecognizer()
    text = "Die Steuer-ID lautet 65929970489 und ist wichtig."

    treffer = recognizer.analyze(text, entities=["STEUER_ID_DE"])

    assert len(treffer) == 1
    assert treffer[0].start == 21
    assert treffer[0].end == 32
    assert text[treffer[0].start : treffer[0].end] == "65929970489"


def test_steuer_id_recognizer_verwirft_nummer_mit_falscher_pruefziffer():
    recognizer = SteuerIdRecognizer()
    text = "Die Steuer-ID lautet 65929970480 und ist wichtig."

    treffer = recognizer.analyze(text, entities=["STEUER_ID_DE"])

    assert treffer == []


def test_steuer_id_recognizer_laesst_sich_durch_kontextwort_nicht_taeuschen():
    # Presidio erhoeht den Score, wenn eines der CONTEXT-Woerter in der Naehe
    # steht. Entscheidend ist, dass dieser Bonus die Pruefziffernvalidierung
    # nicht aushebelt: Auch mit dem Wort "Identifikationsnummer" direkt davor
    # muss eine Zahl mit falscher Pruefziffer weiterhin verworfen werden.
    recognizer = SteuerIdRecognizer()
    text = "Die Identifikationsnummer 65929970480 wurde erfasst."

    treffer = recognizer.analyze(text, entities=["STEUER_ID_DE"])

    assert treffer == []


def test_personalausweisnummer_recognizer_erkennt_gueltige_nummer_im_satz():
    recognizer = PersonalausweisnummerRecognizer()
    text = "Die Dokumentennummer des Personalausweises ist L01X00T471."

    treffer = recognizer.analyze(text, entities=["PERSONALAUSWEISNUMMER_DE"])

    assert len(treffer) == 1
    assert text[treffer[0].start : treffer[0].end] == "L01X00T471"


def test_personalausweisnummer_recognizer_verwirft_falsche_pruefziffer():
    recognizer = PersonalausweisnummerRecognizer()
    text = "Die Dokumentennummer des Personalausweises ist L01X00T470."

    treffer = recognizer.analyze(text, entities=["PERSONALAUSWEISNUMMER_DE"])

    assert treffer == []


def test_personalausweisnummer_recognizer_lehnt_nicht_erlaubten_buchstaben_ab():
    # "A" gehoert nicht zum fuer den ersten Buchstaben zulaessigen Alphabet
    # (verwechslungsanfaellige Buchstaben wie A, B, D, I, O, Q, S, U sind
    # ausgeschlossen), daher darf der Regex hier gar nicht erst greifen.
    recognizer = PersonalausweisnummerRecognizer()
    text = "Die Dokumentennummer des Personalausweises ist A01X00T471."

    treffer = recognizer.analyze(text, entities=["PERSONALAUSWEISNUMMER_DE"])

    assert treffer == []


def test_rentenversicherungsnummer_recognizer_erkennt_gueltige_nummer_im_satz():
    recognizer = RentenversicherungsnummerRecognizer()
    text = "Die Rentenversicherungsnummer lautet 15070649C103."

    treffer = recognizer.analyze(text, entities=["SVNR_DE"])

    assert len(treffer) == 1
    assert text[treffer[0].start : treffer[0].end] == "15070649C103"


def test_rentenversicherungsnummer_recognizer_verwirft_falsche_pruefziffer():
    recognizer = RentenversicherungsnummerRecognizer()
    text = "Die Rentenversicherungsnummer lautet 15070649C104."

    treffer = recognizer.analyze(text, entities=["SVNR_DE"])

    assert treffer == []


def test_rentenversicherungsnummer_recognizer_verwirft_unplausibles_geburtsdatum():
    # 32 ist kein gueltiger Tag; die Pruefziffernfunktion selbst faengt das
    # bereits ab, hier wird zusaetzlich geprueft, dass der Recognizer diesen
    # Fall genauso konsequent verwirft wie eine falsche Pruefziffer.
    recognizer = RentenversicherungsnummerRecognizer()
    text = "Die Rentenversicherungsnummer lautet 32070649C103."

    treffer = recognizer.analyze(text, entities=["SVNR_DE"])

    assert treffer == []
