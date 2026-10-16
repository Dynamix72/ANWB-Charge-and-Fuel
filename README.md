# ANWB Charge & Fuel

Nieuwe Home Assistant integratie voor het vinden van ANWB laadlocaties en brandstofprijzen.

Dit repository bevat een schone start (from-scratch) implementatie van de integratie met:
- custom_components/anwb_charge_and_fuel — hoofdpackage
- basis config flow en sensor stubs
- README, LICENSE en .gitignore

Installatie (lokale test)
1. Clone dit repo.
2. Kopieer `custom_components/anwb_charge_and_fuel` naar je Home Assistant `config/custom_components/` map.
3. Herstart Home Assistant en voeg de integratie toe via Instellingen → Apparaten en Diensten → Integratie toevoegen.

Opmerkingen
- Dit is een frisse, minimale basis. Vul API logica, error handling en tests aan voordat je publiceert.
