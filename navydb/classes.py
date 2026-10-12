"""Curated list of active combatant classes: (country, type, wikipedia page).

Types: carrier, cruiser, destroyer, frigate, corvette, patrol, submarine, amphibious, mcm.
Built from the harvested list-page candidates plus manual review; entries are verified
against the API (page exists + has an infobox) by navydb/fetch.py.
"""
C = []
def add(country, typ, *pages):
    C.extend((country, typ, p) for p in pages)

# --- United States
add("US", "carrier", "Nimitz-class aircraft carrier", "Gerald R. Ford-class aircraft carrier")
add("US", "cruiser", "Ticonderoga-class cruiser")
add("US", "destroyer", "Arleigh Burke-class destroyer", "Zumwalt-class destroyer")
add("US", "corvette", "Freedom-class littoral combat ship", "Independence-class littoral combat ship")
add("US", "submarine", "Ohio-class submarine", "Los Angeles-class submarine", "Seawolf-class submarine", "Virginia-class submarine")
add("US", "amphibious", "America-class amphibious assault ship", "Wasp-class amphibious assault ship",
    "San Antonio-class amphibious transport dock", "Whidbey Island-class dock landing ship",
    "Harpers Ferry-class dock landing ship", "Blue Ridge-class command ship")
add("US", "mcm", "Avenger-class mine countermeasures ship")
# --- China
add("CN", "carrier", "Chinese aircraft carrier Liaoning", "Chinese aircraft carrier Shandong", "Chinese aircraft carrier Fujian")
add("CN", "destroyer", "Type 055 destroyer", "Type 052D destroyer", "Type 052C destroyer", "Type 052B destroyer",
    "Type 051C destroyer", "Chinese destroyer Shenzhen", "Sovremenny-class destroyer", "Type 052 destroyer")
add("CN", "frigate", "Type 054A frigate", "Type 054B frigate", "Type 054 frigate", "Type 053H3 frigate")
add("CN", "corvette", "Type 056 corvette", "Type 022 missile boat", "Type 037 corvette")
add("CN", "submarine", "Type 094 submarine", "Type 093 submarine", "Type 091 submarine", "Type 039 submarine",
    "Type 039A submarine", "Type 035 submarine", "Kilo-class submarine")
add("CN", "amphibious", "Type 075 landing helicopter dock", "Type 071 amphibious transport dock",
    "Type 072A landing ship", "Type 072III landing ship", "Type 074A landing ship")
add("CN", "mcm", "Type 081 mine countermeasure vessel")
# --- Russia
add("RU", "carrier", "Russian aircraft carrier Admiral Kuznetsov")
add("RU", "cruiser", "Kirov-class battlecruiser", "Slava-class cruiser")
add("RU", "destroyer", "Udaloy-class destroyer", "Sovremenny-class destroyer")
add("RU", "frigate", "Admiral Gorshkov-class frigate", "Admiral Grigorovich-class frigate", "Neustrashimy-class frigate",
    "Krivak-class frigate", "Gepard-class frigate")
add("RU", "corvette", "Steregushchiy-class corvette", "Buyan-class corvette", "Karakurt-class corvette",
    "Grisha-class corvette", "Nanuchka-class corvette", "Tarantul-class corvette", "Dergach-class corvette")
add("RU", "submarine", "Borei-class submarine", "Delta IV-class submarine", "Yasen-class submarine", "Akula-class submarine",
    "Oscar-class submarine", "Sierra-class submarine", "Victor-class submarine", "Kilo-class submarine", "Lada-class submarine")
add("RU", "amphibious", "Ivan Gren-class landing ship", "Ropucha-class landing ship", "Alligator-class landing ship")
add("RU", "mcm", "Alexandrit-class minesweeper", "Natya-class minesweeper", "Gorya-class minesweeper")
# --- Japan
add("JP", "carrier", "Izumo-class destroyer", "Hyūga-class helicopter destroyer")
add("JP", "destroyer", "Kongō-class destroyer", "Atago-class destroyer", "Maya-class destroyer", "Asahi-class destroyer",
    "Akizuki-class destroyer (2010)", "Takanami-class destroyer", "Murasame-class destroyer (1994)", "Asagiri-class destroyer")
add("JP", "frigate", "Mogami-class frigate", "Abukuma-class destroyer escort")
add("JP", "submarine", "Sōryū-class submarine", "Taigei-class submarine", "Oyashio-class submarine")
add("JP", "amphibious", "Ōsumi-class tank landing ship")
add("JP", "mcm", "Uraga-class mine countermeasure vessel", "Awaji-class minesweeper", "Sugashima-class minesweeper",
    "Hirashima-class minesweeper", "Enoshima-class minesweeper")
# --- United Kingdom
add("GB", "carrier", "Queen Elizabeth-class aircraft carrier")
add("GB", "destroyer", "Type 45 destroyer")
add("GB", "frigate", "Type 23 frigate")
add("GB", "submarine", "Vanguard-class submarine", "Astute-class submarine")
add("GB", "amphibious", "Albion-class landing platform dock")
add("GB", "patrol", "River-class patrol vessel")
add("GB", "mcm", "Hunt-class mine countermeasures vessel", "Sandown-class minehunter")
# --- France
add("FR", "carrier", "French aircraft carrier Charles de Gaulle")
add("FR", "destroyer", "Horizon-class frigate")
add("FR", "frigate", "FREMM multipurpose frigate", "La Fayette-class frigate", "Floréal-class frigate",
    "Amiral Ronarc'h-class frigate", "D'Estienne d'Orves-class aviso")
add("FR", "submarine", "Triomphant-class submarine", "Suffren-class submarine", "Rubis-class submarine")
add("FR", "amphibious", "Mistral-class amphibious assault ship")
add("FR", "mcm", "Tripartite-class minehunter")
# --- South Korea
add("KR", "destroyer", "Sejong the Great-class destroyer", "Chungmugong Yi Sun-sin-class destroyer", "Gwanggaeto the Great-class destroyer")
add("KR", "frigate", "Incheon-class frigate", "Daegu-class frigate", "Ulsan-class frigate", "Chungnam-class frigate")
add("KR", "corvette", "Pohang-class corvette", "Gumdoksuri-class patrol vessel")
add("KR", "submarine", "Chang Bogo-class submarine", "Son Won-il-class submarine", "Dosan Ahn Changho-class submarine")
add("KR", "amphibious", "Dokdo-class amphibious assault ship", "Cheon Wang Bong-class LST")
add("KR", "mcm", "Yangyang-class minesweeper", "Ganggyeong-class minehunter")
# --- India
add("IN", "carrier", "INS Vikramaditya", "Vikrant-class aircraft carrier")
add("IN", "destroyer", "Delhi-class destroyer", "Kolkata-class destroyer", "Visakhapatnam-class destroyer", "Rajput-class destroyer")
add("IN", "frigate", "Shivalik-class frigate", "Talwar-class frigate", "Brahmaputra-class frigate", "Godavari-class frigate",
    "Nilgiri-class frigate (2019)")
add("IN", "corvette", "Kamorta-class corvette", "Kora-class corvette", "Khukri-class corvette", "Veer-class corvette", "Abhay-class corvette")
add("IN", "submarine", "Arihant-class submarine", "Kalvari-class submarine (2015)", "Sindhughosh-class submarine", "Shishumar-class submarine")
add("IN", "amphibious", "Magar-class amphibious warfare vessel", "Shardul-class tank landing ship", "INS Jalashwa")
# --- Turkey
add("TR", "carrier", "TCG Anadolu")
add("TR", "frigate", "Yavuz-class frigate", "Barbaros-class frigate", "G-class frigate", "Oliver Hazard Perry-class frigate", "Istanbul-class frigate")
add("TR", "corvette", "Ada-class corvette", "Hisar-class offshore patrol vessel", "Burak-class corvette")
add("TR", "submarine", "Preveze-class submarine", "Atılay-class submarine (1974)", "Gür-class submarine", "Reis-class submarine")
add("TR", "patrol", "Rüzgar-class fast attack craft", "Kılıç-class fast attack craft", "Doğan-class fast attack craft",
    "Yıldız-class fast attack craft", "Tuzla-class patrol boat")
add("TR", "amphibious", "Bayraktar-class tank landing ship")
add("TR", "mcm", "A-class minehunter")
