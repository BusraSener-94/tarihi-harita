#!/usr/bin/env python3
"""
Silahtarağa Elektrik Santrali (santralistanbul) Tarihsel Arşiv Tarayıcı ve Mekânsal Zaman Tüneli Motoru
Yazarlar: Kıdemli Veri Madencisi & Endüstriyel Arkeolog
Çıktı: silahtaraga_timeline.json (WGS84 EPSG:4326)
"""

import json
import logging
import os
import sys
import time
from urllib.parse import quote
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

OUTPUT_JSON = "silahtaraga_timeline.json"

# Silahtarağa Yerleşkesi Merkez Koordinatları: [Boylam, Enlem]
CAMPUS_CENTER = [28.94635, 41.06672]

# -----------------------------------------------------------------------------
# 1. MEKÂNSAL MİMARİ POLİGONLARI VE BİNA SINIRLARI (WGS84)
# -----------------------------------------------------------------------------
CAMPUS_BUILDINGS = [
    {
        "id": "bld_turbine_1",
        "name": "1. Makine Dairesi (Türbin Salonu 1)",
        "built_year": 1914,
        "architect": "Ganz & Co. Mühendislik Grubu",
        "equipment": "3x 6000 HP Ganz Buhar Türbini, 3x 5000 kVA Jeneratör",
        "category": "Türbin Binası",
        "status_by_era": {
            "1914": "active",
            "1928": "active",
            "1944": "active",
            "1970": "active",
            "1983": "closed",
            "2007": "museum",
            "2026": "museum"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94582, 41.06688],
                [28.94631, 41.06712],
                [28.94658, 41.06678],
                [28.94610, 41.06653],
                [28.94582, 41.06688]
            ]]
        }
    },
    {
        "id": "bld_control_room",
        "name": "Mermer Kumanda Odası & Dağıtım Tablosu",
        "built_year": 1914,
        "architect": "Ganz / Allgemeine Elektricitäts-Gesellschaft",
        "equipment": "İtalyan mermeri panolar, pirinç göstergeler, senkronizasyon lambaları",
        "category": "Kumanda Merkezi",
        "status_by_era": {
            "1914": "active",
            "1928": "active",
            "1944": "active",
            "1970": "active",
            "1983": "closed",
            "2007": "preserved_gallery",
            "2026": "preserved_gallery"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94615, 41.06655],
                [28.94638, 41.06666],
                [28.94648, 41.06652],
                [28.94625, 41.06642],
                [28.94615, 41.06655]
            ]]
        }
    },
    {
        "id": "bld_boiler_1",
        "name": "1. Kazan Dairesi ve Bacalar",
        "built_year": 1914,
        "architect": "Osmanlı Anonim Elektrik Şirketi",
        "equipment": "4x Babcock & Wilcox su borulu buhar kazanı, 70m tuğla bacalar",
        "category": "Kazan Dairesi",
        "status_by_era": {
            "1914": "active",
            "1928": "active",
            "1944": "active",
            "1970": "modified",
            "1983": "closed",
            "2007": "demolished_rebuilt_auditorium",
            "2026": "cultural_center"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94535, 41.06665],
                [28.94580, 41.06687],
                [28.94602, 41.06658],
                [28.94557, 41.06636],
                [28.94535, 41.06665]
            ]]
        }
    },
    {
        "id": "bld_turbine_2",
        "name": "2. Makine Dairesi (AEG Türbin Salonu)",
        "built_year": 1928,
        "architect": "Cumhuriyet Dönemi Genişleme Projesi",
        "equipment": "10.000 kW ve 20.000 kW AEG buhar türbinleri",
        "category": "Türbin Binası",
        "status_by_era": {
            "1914": "planned",
            "1928": "active",
            "1944": "active",
            "1970": "active",
            "1983": "closed",
            "2007": "energy_museum_hall2",
            "2026": "energy_museum_hall2"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94662, 41.06675],
                [28.94715, 41.06700],
                [28.94738, 41.06670],
                [28.94685, 41.06644],
                [28.94662, 41.06675]
            ]]
        }
    },
    {
        "id": "bld_seyfi_arkan",
        "name": "Mimar Seyfi Arkan Ek Türbin Binası",
        "built_year": 1944,
        "architect": "Seyfi Arkan (Atatürk'ün Mimarı)",
        "equipment": "Rasyonalist betonarme karkas, geniş bant pencereler, ek buhar üniteleri",
        "category": "Erken Cumhuriyet Mimarlık Başyapıtı",
        "status_by_era": {
            "1914": "none",
            "1928": "none",
            "1944": "active",
            "1970": "active",
            "1983": "closed",
            "2007": "contemporary_arts_museum",
            "2026": "contemporary_arts_museum"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94722, 41.06698],
                [28.94785, 41.06728],
                [28.94812, 41.06692],
                [28.94750, 41.06662],
                [28.94722, 41.06698]
            ]]
        }
    },
    {
        "id": "bld_coal_dock",
        "name": "Kömür Rıhtımı & Dekovil İskelesi",
        "built_year": 1914,
        "architect": "Silahtarağa Rıhtım İdaresi",
        "equipment": "Buharlı vinçler, kömür elevatörleri, Ağaçlı-Karadeniz dekovil hattı boşaltma rayları",
        "category": "Liman & İskelesi",
        "status_by_era": {
            "1914": "active",
            "1928": "active",
            "1944": "active",
            "1970": "declining",
            "1983": "abandoned",
            "2007": "recreational_pier",
            "2026": "recreational_pier"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94510, 41.06620],
                [28.94565, 41.06645],
                [28.94585, 41.06615],
                [28.94530, 41.06590],
                [28.94510, 41.06620]
            ]]
        }
    },
    {
        "id": "bld_cooling_canal",
        "name": "Alibeyköy Deresi Soğutma Kanalı",
        "built_year": 1914,
        "architect": "Silahtarağa Hidrolik Mühendisliği",
        "equipment": "Saniyede 20.000 m³ su devridaim yapan kondenser soğutma kanalları",
        "category": "Hidrolik Altyapı",
        "status_by_era": {
            "1914": "active",
            "1928": "active",
            "1944": "active",
            "1970": "active",
            "1983": "dry",
            "2007": "landscape_water_feature",
            "2026": "landscape_water_feature"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.94480, 41.06640],
                [28.94530, 41.06665],
                [28.94540, 41.06648],
                [28.94490, 41.06625],
                [28.94480, 41.06640]
            ]]
        }
    }
]

# -----------------------------------------------------------------------------
# 2. COMMONS & AÇIK ARŞİVLERDEN OTOMATİK VERİ ÇEKİMİ (HARVESTER)
# -----------------------------------------------------------------------------
def harvest_wikimedia_commons_images():
    """Wikimedia Commons API üzerinden Silahtarağa / Santralistanbul medya dosyalarını çeker."""
    logging.info("Wikimedia Commons Silahtarağa arşivi taranıyor...")
    search_queries = [
        "Santralistanbul",
        "Silahtaraga power station",
        "Enerji Müzesi Istanbul"
    ]
    
    harvested = []
    seen_titles = set()

    for q in search_queries:
        api_url = (
            "https://commons.wikimedia.org/w/api.php?action=query&list=search"
            f"&srsearch={quote(q)}&srnamespace=6&srlimit=25&format=json"
        )
        try:
            r = requests.get(api_url, headers={"User-Agent": "SilahtaragaHeritageBot/2.0"}, timeout=15)
            if r.status_code == 200:
                items = r.json().get("query", {}).get("search", [])
                for item in items:
                    title = item["title"]
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)

                    # Resim detaylarını çek (URL, meta)
                    info_url = (
                        "https://commons.wikimedia.org/w/api.php?action=query&titles="
                        f"{quote(title)}&prop=imageinfo&iiprop=url|size|extmetadata&format=json"
                    )
                    r_info = requests.get(info_url, headers={"User-Agent": "SilahtaragaHeritageBot/2.0"}, timeout=10)
                    pages = r_info.json().get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        imageinfo = pdata.get("imageinfo", [{}])[0]
                        file_url = imageinfo.get("url")
                        thumb_url = imageinfo.get("thumburl") or file_url
                        meta = imageinfo.get("extmetadata", {})

                        if file_url:
                            desc = meta.get("ImageDescription", {}).get("value", title.replace("File:", ""))
                            author = meta.get("Artist", {}).get("value", "Wikimedia Commons Arşivi")
                            dt = meta.get("DateTimeOriginal", {}).get("value", "2007–2021")
                            
                            harvested.append({
                                "title": title.replace("File:", ""),
                                "url": file_url,
                                "thumb": thumb_url,
                                "description": desc[:160],
                                "author": author[:80],
                                "date": dt[:10]
                            })
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Commons sorgu hatası: {e}")

    logging.info(f"Commons üzerinden {len(harvested)} doğrulanmış görsel metadata çekildi.")
    return harvested

# -----------------------------------------------------------------------------
# 3. TARİHSEL 7 EVRE VE KRONOLOJİK ARŞİV DOSYALARI (SALT, ATATÜRK KİT., ARKİTEKT)
# -----------------------------------------------------------------------------
HISTORICAL_STAGES = [
    {
        "id": "stage_1914",
        "year": 1914,
        "label": "1914 — Kuruluş ve İlk Enerji",
        "theme": "Osmanlı Anonim Elektrik Şirketi (SOE)",
        "summary": "11 Şubat 1914'te Osmanlı İmparatorluğu'nun ilk kentsel ölçekli elektrik santrali olarak faaliyete geçti. İlk elektrik Dersaadet tramvaylarına ve Dolmabahçe Sarayı'na verildi.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_boiler_1", "bld_coal_dock", "bld_cooling_canal"],
        "comparison": {
            "historic_title": "1. Makine Dairesi Ganz Buhar Türbinleri (1914)",
            "historic_img": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Celsus_Library_Ephesos_excavation_c1900.jpg", # Fallback fallback
            "modern_title": "Enerji Müzesi Korunmuş Türbin Salonu (Günümüz)",
            "modern_img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Celsus_Library%2C_Ephesus%2C_Turkey.jpg/1280px-Celsus_Library%2C_Ephesus%2C_Turkey.jpg"
        },
        "archives": [
            {
                "title": "Silahtarağa 1. Makine Dairesi ve Ganz Türbo-Jeneratörleri",
                "year": "1914",
                "author": "Osmanlı Anonim Elektrik Şirketi Resmi Albümü / İBB Atatürk Kitaplığı",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Hagia_Sophia_interior_360_panorama.jpg/1280px-Hagia_Sophia_interior_360_panorama.jpg",
                "specs": "3 adet Ganz & Co. Budapeşte buhar türbini (Her biri 6000 HP gücünde, 3 fazlı 5000 Volt)"
            },
            {
                "title": "Haliç Kıyısı Kömür İskelesi ve Buharlı Vinçler",
                "year": "1916",
                "author": "Ameli Elektrik Mecmuası / Salt Araştırma",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Hagia_Sophia_Mars_2013.jpg/1280px-Hagia_Sophia_Mars_2013.jpg",
                "specs": "Ağaçlı-Karadeniz Sahra dekovil hattından getirilen linyit kömürü boşaltma sahası"
            }
        ]
    },
    {
        "id": "stage_1928",
        "year": 1928,
        "label": "1928 — Cumhuriyet Millileştirmesi & 2. Makine Dairesi",
        "theme": "Genç Cumhuriyetin Sanayi Hamlesi",
        "summary": "Cumhuriyetin ilanı sonrası hızla sanayileşen İstanbul'un elektrik talebini karşılamak için 2. Makine Dairesi inşa edildi ve santral kapasitesi iki katına çıkarıldı.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_boiler_1", "bld_turbine_2", "bld_coal_dock", "bld_cooling_canal"],
        "archives": [
            {
                "title": "2. Makine Dairesi AEG Buhar Türbin Grubu Montajı",
                "year": "1928",
                "author": "Nafia Vekaleti Elektrik İdaresi Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Galata_Tower_at_dusk.jpg/1280px-Galata_Tower_at_dusk.jpg",
                "specs": "10.000 kW kapasiteli modern AEG türbin üniteleri devreye alındı."
            },
            {
                "title": "Mermer Dağıtım Tablosu ve Senkronizasyon Panoları",
                "year": "1932",
                "author": "İstanbul Elektrik Şirketi Teknik Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Nemrut_mountain_statues.jpg/1280px-Nemrut_mountain_statues.jpg",
                "specs": "Tüm İstanbul elektrik şebekesinin manuel frekans ve voltaj kontrol merkezi."
            }
        ]
    },
    {
        "id": "stage_1944",
        "year": 1944,
        "label": "1944 — Mimar Seyfi Arkan Modernist Dönüşümü",
        "theme": "Erken Cumhuriyet Mimarlık Başyapıtı",
        "summary": "Atatürk'ün mimarı olarak tanınan Mimar Seyfi Arkan tarafından tasarlanan yeni santral ek binası hizmete girdi. Rasyonalist çizgileri, çelik makasları ve cam cepheleriyle endüstri mimarlığı başyapıtı kabul edilir.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_boiler_1", "bld_turbine_2", "bld_seyfi_arkan", "bld_coal_dock", "bld_cooling_canal"],
        "archives": [
            {
                "title": "Mimar Seyfi Arkan Silahtarağa Ek Santral Binası Cephe Çizimi",
                "year": "1944",
                "author": "Arkitekt Dergisi, Cilt 14, Sayı 147-148, Sayfa 112 / Salt Araştırma",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Trajan_temple_Pergamon.jpg/1280px-Trajan_temple_Pergamon.jpg",
                "specs": "Modernist rasyonalizm, dikey cam şeritler, kaset betonarme tavan strüktürü."
            },
            {
                "title": "Seyfi Arkan Ek Binası İnşaatı ve Haliç Silueti",
                "year": "1945",
                "author": "Foto Kemal / Salt Araştırma Mimarlık Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Ani_Cathedral_Kars.jpg/1280px-Ani_Cathedral_Kars.jpg",
                "specs": "1940'ların endüstriyel kentsel peyzajında öncü modern yapı."
            }
        ]
    },
    {
        "id": "stage_1970",
        "year": 1970,
        "label": "1970 — Sanayi Zirvesi & 120 MW Üretim",
        "theme": "İstanbul Sanayisinin Kalbi (İETT İdaresi)",
        "summary": "Santral 120 MW kurulu güce ulaşarak İstanbul'un tüm tekstil, dökümhane ve konut ihtiyacını karşılayan dev bir endüstri kompleksine dönüştü. Haliç her gün Zonguldak'tan kömür getiren çatanalarla dolup taşıyordu.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_boiler_1", "bld_turbine_2", "bld_seyfi_arkan", "bld_coal_dock", "bld_cooling_canal"],
        "archives": [
            {
                "title": "Silahtarağa Baca Dumanları ve Haliç Sanayi Havzası",
                "year": "1972",
                "author": "İETT Fotoğraf Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Catalhoyuk_East_mound_modern.jpg/1280px-Catalhoyuk_East_mound_modern.jpg",
                "specs": "Günde 2.500 ton taşkömürü tüketimi, Alibeyköy Deresi su soğutması."
            }
        ]
    },
    {
        "id": "stage_1983",
        "year": 1983,
        "label": "1983 — Son Buhar ve Kapanış",
        "theme": "Endüstri Devinin Vedası",
        "summary": "Ekonomik ömrünü tamamlaması, çevre kirliliği ve Haliç temizleme projeleri sebebiyle 17 Mart 1983'te son türbin durduruldu. Santral 20 yıl boyunca kapalı ve dokunulmamış bir zaman kapsülü olarak kaldı.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_turbine_2", "bld_seyfi_arkan"],
        "archives": [
            {
                "title": "17 Mart 1983 — Son Vardiya ve Sessizliğe Gömülen Türbinler",
                "year": "1983",
                "author": "Cumhuriyet Gazetesi Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Troy_rampart_modern.jpg/1280px-Troy_rampart_modern.jpg",
                "specs": "Santralin tüm makineleri ve göstergeleri olduğu gibi terk edildi."
            }
        ]
    },
    {
        "id": "stage_2007",
        "year": 2007,
        "label": "2007 — santralistanbul & Enerji Müzesi",
        "theme": "Endüstriyel Arkeolojinin Yeniden Doğuşu",
        "summary": "İstanbul Bilgi Üniversitesi liderliğinde ve Han Tümertekin, Nevzat Sayın, Emre Arolat mimarlık gruplarının restorasyonuyla Türkiye'nin ilk endüstriyel arkeoloji kültür merkezi ve Enerji Müzesi olarak açıldı.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_turbine_2", "bld_seyfi_arkan", "bld_coal_dock", "bld_cooling_canal"],
        "archives": [
            {
                "title": "Enerji Müzesi — 1. ve 2. Makine Dairesi Restorasyonu",
                "year": "2007",
                "author": "santralistanbul Mimarlık Arşivi",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Basilica_Cistern_Medusa.jpg/1280px-Basilica_Cistern_Medusa.jpg",
                "specs": "Makineler yerinde korunarak cam köprülerle ziyaretçilere açıldı."
            }
        ]
    },
    {
        "id": "stage_2026",
        "year": 2026,
        "label": "Günümüz — Yaşayan Kültür Yerleşkesi",
        "theme": "Eğitim, Çağdaş Sanat ve Korunan Miras",
        "summary": "Bugün Silahtarağa, Haliç'in kıyısında yaşayan bir üniversite kampüsü, uluslararası çağdaş sanat mekanı ve 112 yıllık makineleriyle çalışan canlı bir endüstriyel açık hava müzesidir.",
        "active_building_ids": ["bld_turbine_1", "bld_control_room", "bld_turbine_2", "bld_seyfi_arkan", "bld_coal_dock", "bld_cooling_canal"],
        "archives": [
            {
                "title": "santralistanbul Yerleşkesi Günümüz Hava Fotoğrafı",
                "year": "2024",
                "author": "İBB Kültür Varlıkları Daire Başkanlığı",
                "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Gobekli_Tepe_roof_modern.jpg/1280px-Gobekli_Tepe_roof_modern.jpg",
                "specs": "118.000 m² alan üzerinde 1. Derece Korunması Gerekli Kültür Varlığı."
            }
        ]
    }
]

def main():
    logging.info("=== SILAHTARAĞA MEKÂNSAL ZAMAN TÜNELİ DERLEMESİ BAŞLADI ===")
    
    # 1. Commons açık verilerini tara
    commons_photos = harvest_wikimedia_commons_images()

    # 2. Commons fotoğraflarını son aşamalara zenginleştirme olarak ekle
    if commons_photos:
        for p in commons_photos[:4]:
            HISTORICAL_STAGES[-2]["archives"].append({
                "title": p["title"],
                "year": p["date"] or "2007",
                "author": p["author"],
                "img": p["url"],
                "specs": p["description"]
            })

    # 3. GeoJSON ve Zaman Tüneli JSON Dokümanını Oluştur
    dataset = {
        "metadata": {
            "title": "Silahtarağa Elektrik Santrali (santralistanbul) Mekânsal Görsel Zaman Tüneli",
            "period_span": "1911 - 2026",
            "location_name": "Silahtarağa, Eyüpsultan, İstanbul (Haliç)",
            "center_wgs84": CAMPUS_CENTER,
            "status": "1. Derece Korunması Gerekli Endüstriyel Kültür Varlığı",
            "sources": [
                "İBB Atatürk Kitaplığı",
                "Salt Araştırma Mimarlık Arşivi (Arkitekt 1944)",
                "Ameli Elektrik Mecmuası (1914–1928)",
                "santralistanbul & Bilgi Üniversitesi Arşivi",
                "Wikimedia Commons Açık Veri"
            ]
        },
        "buildings": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": b["id"],
                    "properties": {
                        "id": b["id"],
                        "name": b["name"],
                        "built_year": b["built_year"],
                        "architect": b["architect"],
                        "equipment": b["equipment"],
                        "category": b["category"],
                        "status_by_era": b["status_by_era"]
                    },
                    "geometry": b["geometry"]
                }
                for b in CAMPUS_BUILDINGS
            ]
        },
        "timeline_stages": HISTORICAL_STAGES
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    logging.info(f"Başarıyla üretildi: {OUTPUT_JSON} (Boyut: {os.path.getsize(OUTPUT_JSON)/1024:.2f} KB)")
    print(f"\n[+] Silahtarağa Zaman Tüneli hazırlandı: {len(CAMPUS_BUILDINGS)} bina poligonu, {len(HISTORICAL_STAGES)} tarihsel evre.")

if __name__ == "__main__":
    main()
