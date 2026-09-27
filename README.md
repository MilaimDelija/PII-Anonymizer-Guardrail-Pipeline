# PII Anonymizer & Guardrail-Pipeline

Dieses Repository enthält eine Pipeline, die personenbezogene Angaben in einem Text erkennt und durch Platzhalter ersetzt, bevor der Text an eine externe KI-Anwendung mit eigener Programmierschnittstelle übergeben wird — etwa an einen Chatbot-Dienst, dessen Anbieter außerhalb der eigenen Infrastruktur liegt. Es entstand als Arbeitsprobe im Rahmen einer Ausbildung zum zertifizierten Datenschutzbeauftragten (TÜV) und adressiert ein Szenario, das in Unternehmen beim Einsatz generativer KI regelmäßig auftritt: Beschäftigte fügen einer Anfrage unbedacht Namen, Kontaktdaten oder Kennnummern bei, die dadurch an einen Auftragsverarbeiter oder, je nach Vertragslage, an einen Dritten außerhalb der eigenen Kontrolle gelangen. Eine solche vorgeschaltete Filterung ist eine von mehreren möglichen technischen Maßnahmen im Sinne von Art. 25 Abs. 1 DSGVO (Datenschutz durch Technikgestaltung); sie ersetzt keine der übrigen Voraussetzungen einer zulässigen Verarbeitung, etwa eine tragfähige Rechtsgrundlage oder einen bestehenden Auftragsverarbeitungsvertrag.

## Aufbau

`src/checksums_de.py` enthält die Prüfziffernverfahren für vier Kennungen: die IBAN nach dem international genutzten Mod-97-Verfahren, die Steuerliche Identifikationsnummer nach dem in § 139b AO vorgesehenen Verfahren (ISO/IEC 7064, Mod 11,10), die Dokumentennummer des Personalausweises im Format seit November 2010 (Gewichtung 7-3-1) und die zwölfstellige Rentenversicherungsnummer. Jede Funktion prüft ausschließlich die mathematische Gültigkeit einer Zeichenkette mit passendem Format, nicht deren tatsächliche Zuteilung an eine reale Person.

`src/recognizers_de.py` bindet drei dieser Verfahren als eigene Presidio-Recognizer ein: für die Steuer-ID, die Personalausweisnummer und die Rentenversicherungsnummer. Für die IBAN wurde bewusst kein eigener Recognizer angelegt, weil Microsoft Presidio bereits einen länderübergreifenden, korrekt validierten IBAN-Recognizer mitliefert; ein zusätzlicher deutscher Recognizer dafür wäre Doppelarbeit gewesen und hätte das Risiko widersprüchlicher Treffer auf derselben Textstelle geschaffen.

`src/anonymizer.py` verbindet diese Recognizer mit dem deutschen spaCy-Modell (Namenserkennung) und den mitgelieferten Presidio-Recognizern für E-Mail-Adressen, Telefonnummern und Kreditkartennummern zu einer einzigen Analyse- und Ersetzungsfunktion. Kreditkarten werden dabei ausdrücklich mit `supported_language="de"` registriert, da Presidios eigener `CreditCardRecognizer` standardmäßig nur für Englisch aktiviert ist, obwohl die zugrunde liegende Luhn-Prüfung sprachunabhängig funktioniert. Weil dieselbe Textstelle mitunter von mehr als einem Recognizer erfasst wird — eine elfstellige Steuer-ID passt zufällig auch auf das allgemeine Muster einer Telefonnummer —, werden überlappende Treffer vor der Ausgabe auf den jeweils höher bewerteten reduziert.

`app.py` stellt diese Pipeline als Streamlit-Oberfläche mit editierbarem Eingabefeld, wählbaren Kategorien, anonymisiertem Ausgabetext und einer Liste der erkannten Angaben samt Score bereit.

`tests/` enthält automatisierte Tests für die Prüfziffernverfahren, die einzelnen Recognizer, die zusammengeführte Pipeline und — über `streamlit.testing.v1.AppTest` — für das Verhalten der Oberfläche, ohne dass dafür ein Browser erforderlich ist.

## Verwendung

Voraussetzung ist Python 3.11 oder neuer. Das deutsche spaCy-Modell wird über die in `requirements.txt` angegebene Paket-URL automatisch mitinstalliert.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Die Anwendung ist danach unter `http://localhost:8501` erreichbar. Für die Verwendung als vorgeschalteter Filter in einem eigenen Skript reicht der direkte Aufruf der Kernfunktion:

```python
from src.anonymizer import anonymisiere

ergebnis = anonymisiere("Mein Name ist Anna Beispiel, erreichbar unter anna@beispiel.de.")
print(ergebnis.anonymisierter_text)
```

## Tests

```bash
pip install -r requirements.txt
pytest
```

## Einschränkungen

Die Namenserkennung stützt sich auf ein statistisches Sprachmodell und ist damit weder vollständig noch fehlerfrei: Sie kann einzelne Namen übersehen, und im Deutschen führt die Großschreibung aller Substantive gelegentlich dazu, dass eine unauffällige Wortfolge am Satzanfang fälschlich als Name eingeordnet wird. Bei der Steuer-ID wird ausschließlich das Prüfziffernverfahren selbst abgebildet; die zusätzliche Vergaberegel des Bundeszentralamts für Steuern, wonach unter den ersten zehn Ziffern genau eine Ziffer zwei- oder unter bestimmten Bedingungen dreifach vorkommen muss, wird nicht geprüft. Eine Zahl kann die Prüfziffer erfüllen, ohne tatsächlich als Steuer-ID vergeben worden zu sein, und umgekehrt kann eine echte, aber im eingegebenen Text fehlerhaft abgeschriebene Nummer verworfen werden. Für keine der vier Kennungen wird geprüft, ob sie tatsächlich existiert oder einer bestimmten Person zugeordnet ist; geprüft wird ausschließlich die rechnerische Gültigkeit des Formats.

Die von der Oberfläche angezeigte Liste der Erkennungen enthält bewusst die ursprünglichen, noch nicht anonymisierten Werte, damit die Ersetzung im Einzelfall nachvollziehbar bleibt. In einem produktiven Einsatz sollte diese Liste aus genau diesem Grund nicht protokolliert oder dauerhaft gespeichert werden, da sie sonst selbst zu einer zusätzlichen Ablage personenbezogener Daten würde, die die vorgeschaltete Filterung eigentlich vermeiden soll.

## Verwendete Bibliotheken

Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`) für die Erkennungs- und Ersetzungslogik, spaCy mit dem deutschen Modell `de_core_news_sm` für die Namenserkennung, Streamlit für die Oberfläche.

## Lizenz

MIT-Lizenz, siehe `LICENSE`.
