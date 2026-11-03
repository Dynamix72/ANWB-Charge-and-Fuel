# ANWB Charge & Fuel

Home Assistant-integratie voor ANWB-laadlocaties en brandstofprijzen. De integratie zoekt laadpunten en tankstations bij je huidige locatie of langs een route naar een bestemming. Resultaten worden gerangschikt op prijs.

> De integratie gebruikt de locatie van een Home Assistant-`device_tracker`. Voor routeberekening naar een bestemming is een API-sleutel van [OpenRouteService](https://openrouteservice.org/) nodig. Zonder die sleutel zoekt de integratie bij je huidige locatie.

## Installatie

### Via HACS (aanbevolen)

1. Open **HACS → Integraties** in Home Assistant.
2. Open het menu rechtsboven en kies **Aangepaste repositories**.
3. Voeg `https://github.com/Dynamix72/ANWB-Charge-and-Fuel` toe en kies als categorie **Integration**.
4. Zoek in HACS naar **ANWB Charge & Fuel** en installeer de integratie.
5. Herstart Home Assistant.
6. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar **ANWB Charge & Fuel**.

### Handmatig

1. Download of clone deze repository.
2. Kopieer de map `custom_components/anwb_charge_and_fuel` naar `<configuratiemap>/custom_components/anwb_charge_and_fuel`.
3. Herstart Home Assistant.
4. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar **ANWB Charge & Fuel**.

Als de map `custom_components` nog niet bestaat, maak deze dan aan in je Home Assistant-configuratiemap.

## Configuratie

Bij het toevoegen kies je:

- **Device tracker**: de tracker die de huidige positie levert. Deze moet `latitude`- en `longitude`-attributen hebben.
- **Datamodus**: `charge` (alleen laden), `fuel` (alleen brandstof) of `both` (beide; standaard).
- **OpenRouteService API-sleutel**: optioneel. Nodig om een ingevulde bestemming via een route op te zoeken. Maak een sleutel aan via [OpenRouteService](https://openrouteservice.org/).

Je kunt de tracker, datamodus en API-sleutel later aanpassen via de opties van de integratie. Na het wijzigen van de datamodus kan een herstart nodig zijn om de bijbehorende entiteiten opnieuw aan te maken of te verwijderen.

## Bestemming en zoekafstand

De integratie vernieuwt de gegevens periodiek en ook wanneer je een instelling wijzigt.

### Zonder bestemming

Laat **Bestemming** leeg. De integratie zoekt laadpunten en/of tankstations rond de positie van de gekozen device tracker. De zoekafstand bepaalt de ingestelde afstand; de ANWB-zoekopdracht is momenteel begrensd op maximaal 10 km. Bij een grotere ingestelde afstand wordt deze in deze modus teruggezet naar 10 km.

### Met bestemming

Vul bij **Bestemming** een plaats of adres in en configureer een OpenRouteService API-sleutel. De integratie berekent een route vanaf de actuele trackerpositie en plaatst een zoekpunt op de route, op de ingestelde afstand vanaf het begin van de route (of bij de bestemming als de route korter is). Daarna zoekt ANWB binnen maximaal 10 km van dat zoekpunt. De zoekafstand bepaalt dus hoe ver langs de route het zoekpunt komt; het is niet de straal van een zoekcirkel rond de volledige route.

De afstand die bij een resultaat wordt getoond, is de hemelsbrede afstand vanaf de actuele trackerpositie, niet de afstand langs de route. Zonder geldige API-sleutel of wanneer routeberekening mislukt, wordt de route niet gebruikt en zoekt de integratie rond de actuele locatie.

## Entiteiten

Entiteiten worden afhankelijk van de gekozen datamodus aangemaakt.

### Sensoren voor laden

- **ANWB Charger Count**: aantal gevonden laadlocaties met bruikbare prijsinformatie.
- **ANWB Top Charger 1–10**: de tien goedkoopste gevonden laadopties. De sensorwaarde is de prijs; attributen bevatten onder andere afstand in km, maximaal vermogen in kW, beschikbare en totale aansluitingen, coördinaten en de ruwe locatiegegevens. Een rangnummer zonder resultaat heeft geen waarde.

### Sensoren voor brandstof

- **ANWB Fuel Count**: aantal gevonden tankstations met een prijs voor de geselecteerde brandstof.
- **ANWB Top Fuel 1–10**: de tien goedkoopste resultaten voor de geselecteerde brandstof. De sensorwaarde is de prijs; attributen bevatten onder andere brandstoftype, afstand in km, coördinaten en de ruwe stationgegevens. Een rangnummer zonder resultaat heeft geen waarde.

### Route- en gecombineerde sensoren

- **ANWB Results**: status van de laatste update. Attributen bevatten de actieve filters, bestemming en de volledige lijsten met laad- en brandstofresultaten.
- **ANWB Route**: geeft aan of routegegevens beschikbaar zijn; de GeoJSON-route staat in de attributen.
- **ANWB Route Marker**: afstand vanaf het begin van de route tot het gebruikte zoekpunt, met coördinaten.

### Instellingen en filters

- **Zoekafstand** (km): stelt de zoekafstand in. Zonder bestemming is de ANWB-zoekradius maximaal 10 km. Met bestemming bepaalt deze instelling de positie van het zoekpunt langs de route; de zoekradius rondom dat punt is maximaal 10 km.
- **Bestemming**: tekstveld voor een adres of plaatsnaam. Laat leeg om rond de huidige locatie te zoeken.
- **Brandstof**: selecteer `euro95`, `diesel`, `superplus` of `lpg`. Alleen tankstations met een prijs voor het gekozen type worden meegenomen.
- **Laadpaaltype**: selecteer `all`, `ac` (minder dan 50 kW), `fast` (50 tot minder dan 100 kW) of `ultrafast` (100 kW of meer).

De brandstof- en laadpaaltypekeuze zijn alleen beschikbaar in de relevante datamodus. De instellingen en filters zijn configureerbare Home Assistant-entiteiten; voeg ze desgewenst toe aan een dashboard.

## Problemen oplossen

- **Geen resultaten**: controleer of de device tracker een geldige positie heeft en of de gekozen brandstof of het laadpaaltype beschikbaar is.
- **Geen route**: controleer de OpenRouteService API-sleutel en de bestemming. Zonder route wordt er rond je huidige locatie gezocht.
- **Entiteiten ontbreken na moduswijziging**: herstart Home Assistant nadat je de datamodus hebt gewijzigd.

## Bijdragen en wijzigingen

Bijdragen zijn welkom via issues en pull requests. Zie [CONTRIBUTING.md](CONTRIBUTING.md) en [CHANGELOG.md](CHANGELOG.md).
