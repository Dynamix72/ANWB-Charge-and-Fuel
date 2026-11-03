# ANWB Charge & Fuel — documentatie

Deze map is de Home Assistant-integratie. Voor de volledige installatiehandleiding, configuratie, uitleg van sensoren, bestemming en zoekafstand, zie de [repositorydocumentatie](https://github.com/Dynamix72/ANWB-Charge-and-Fuel#readme).

## Installatie in het kort

Installeer via HACS als aangepaste repository (`https://github.com/Dynamix72/ANWB-Charge-and-Fuel`, categorie **Integration**) of kopieer `custom_components/anwb_charge_and_fuel` naar de map `custom_components` in je Home Assistant-configuratie. Herstart Home Assistant en voeg **ANWB Charge & Fuel** toe via **Instellingen → Apparaten en diensten → Integratie toevoegen**.

Selecteer bij de configuratie een device tracker met locatiegegevens. Kies desgewenst de datamodus. Een OpenRouteService API-sleutel is alleen nodig voor zoeken langs een route naar een ingevulde bestemming.
