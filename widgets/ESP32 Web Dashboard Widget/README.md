# ESP32 Web Dashboard Widget

Toont de webinterface van een apparaat op je lokale netwerk (bijvoorbeeld
een ESP32-project met een ingebouwde webserver, zoals een klimaatkast,
hydrocultuursysteem, of elk ander zelfgebouwd dashboard) rechtstreeks als
widget op je desktop — altijd zichtbaar, zonder een browservenster te
hoeven openen.

## Functionaliteit

- Voeg één of meerdere systemen toe, elk met een naam en een IP-adres (of
  volledige URL).
- Wissel tussen systemen via de dropdown bovenaan de widget.
- Klik op "Herlaad" om de huidige pagina te verversen.
- De widget onthoudt welk systeem je het laatst bekeek, en de grootte/positie
  van het venster.

## Vereisten

Deze widget gebruikt `QWebEngineView` om webpagina's weer te geven, en heeft
dus naast `PyQt5` ook `PyQtWebEngine` nodig:

```
PyQt5==5.15.6
PyQtWebEngine==5.15.6
```

Als `PyQtWebEngine` niet beschikbaar is, toont de widget een duidelijke
melding in plaats van te crashen.

## Een systeem toevoegen

1. Open de widgetinstellingen (tandwiel-icoon / instellingenknop van de widget).
2. Klik op "Nieuw systeem".
3. Vul een herkenbare naam in (bv. "Klimaatkast") en het lokale IP-adres van
   het apparaat (bv. `192.168.1.50` — met of zonder poortnummer, bv.
   `192.168.1.50:80`).
4. Klik op "Bijwerken" om de naam/IP te bevestigen, en sluit de instellingen
   met "Save" om te bewaren.

## Meerdere dashboards tegelijk zichtbaar

De dropdown laat je wisselen tussen systemen, maar toont er telkens maar
één tegelijk. Wil je bijvoorbeeld je klimaatkast, een 3D-printer en nog
een 3D-printer **allemaal tegelijk** op je scherm, in aparte vensters?

1. Kopieer `esp32_web_dashboard.py` in je widgetmap
   (`Documenten\Imolia Desktop Customizer Widgets`) en geef de kopie een
   andere bestandsnaam (bv. `printer_ad5x.py`).
2. Herstart de app (of klik op "Vernieuwen" in de widgetlijst) — de kopie
   verschijnt als een aparte widget met een eigen naam, gebaseerd op de
   bestandsnaam.
3. Activeer hem via Instellingen en geef hem zijn eigen systeem (naam +
   IP-adres) mee.

Elke kopie krijgt automatisch zijn **eigen, onafhankelijke**
configuratiebestand (zie hieronder) — kopieën beïnvloeden elkaar niet.

## Configuratiebestand

De instellingen worden opgeslagen naast het widget-bestand, in een
bestand genaamd `<bestandsnaam-zonder-.py>_config.json`. Voor
`esp32_web_dashboard.py` is dat dus `esp32_web_dashboard_config.json`;
voor een kopie `printer_ad5x.py` wordt dat `printer_ad5x_config.json`.
Zo krijgt elke kopie automatisch zijn eigen configuratie, ook al staan ze
allemaal in dezelfde map.
