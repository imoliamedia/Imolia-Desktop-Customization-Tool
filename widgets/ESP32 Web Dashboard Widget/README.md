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

## Configuratiebestand

De instellingen worden opgeslagen in `esp32_web_dashboard_widget_config.json`
in dezelfde map als het widget-bestand.
