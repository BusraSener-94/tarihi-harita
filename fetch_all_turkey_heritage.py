#!/usr/bin/env python3
"""
Türkiye Arkeolojik Miras ve Tarihi Yapılar Tam Envanter ETL Script'i
Hedef: Türkiye sınırları (ISO3166-1=TR) içerisindeki tüm tescilli tarihi ve antik noktaları toplamak.
Çıktı: turkiye_tum_tarihi_yapilar.geojson (WGS84 EPSG:4326)
"""

import json
import logging
import math
import os
import re
import sys
import time
from typing import Dict, Any, List, Optional, Tuple, Set
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("heritage_etl.log", encoding="utf-8")
    ]
)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

OUTPUT_FILE = "turkiye_tum_tarihi_yapilar.geojson"

# Türkiye sınırları (BBOX doğrulama)
TR_BOUNDS = {
    "min_lat": 35.8,
    "max_lat": 42.4,
    "min_lon": 25.6,
    "max_lon": 44.9
}

# 6 Bölgesel BBOX Parçası (Sunucu bellek taşmasını ve zaman aşımını engellemek için)
REGIONS = [
    {"name": "Marmara & Trakya & Çanakkale", "bbox": "39.8,25.8,42.2,30.5"},
    {"name": "Ege & Karya & İyonya", "bbox": "36.6,26.0,39.8,29.5"},
    {"name": "Akdeniz & Likya & Kilikya", "bbox": "35.8,29.0,37.8,36.5"},
    {"name": "İç Anadolu & Hitit & Frig", "bbox": "37.5,29.5,40.5,36.0"},
    {"name": "Karadeniz Sahili & Pontus", "bbox": "40.2,30.5,42.3,42.0"},
    {"name": "Doğu & Güneydoğu & Mezopotamya", "bbox": "36.6,36.0,41.5,44.8"}
]

HISTORIC_TAG_REGEX = "^(archaeological_site|castle|fort|ruins|tomb|aqueduct|cistern|monument|memorial|city_gate|manor|palace)$"

def build_overpass_query(bbox: str) -> str:
    return f"""
    [out:json][timeout:180][maxsize:536870912];
    (
      node["historic"~"{HISTORIC_TAG_REGEX}"]({bbox});
      way["historic"~"{HISTORIC_TAG_REGEX}"]({bbox});
      relation["historic"~"{HISTORIC_TAG_REGEX}"]({bbox});
      
      // TAY Projesi veya Resmi Tescil Kodu olan alanlar
      node["ref:tay"]({bbox});
      way["ref:tay"]({bbox});
      node["heritage"]({bbox});
      way["heritage"]({bbox});
    );
    out center tags qt;
    """

def query_overpass_with_fallback(query: str, region_name: str) -> List[Dict[str, Any]]:
    for server in OVERPASS_SERVERS:
        for attempt in range(1, 4):
            try:
                logging.info(f"[{region_name}] Sorgulanıyor ({server}) - Deneme {attempt}/3...")
                resp = requests.post(
                    server,
                    data={"data": query},
                    headers={"User-Agent": "AntikAtlasGIS/3.0 (Heritage Preservation Project)"},
                    timeout=200
                )
                if resp.status_code == 200:
                    data = resp.json()
                    elements = data.get("elements", [])
                    logging.info(f"[{region_name}] Başarılı! {len(elements)} kayıt alındı.")
                    return elements
                elif resp.status_code in [429, 504, 502]:
                    wait_time = attempt * 10
                    logging.warning(f"Sunucu meşgul (HTTP {resp.status_code}), {wait_time}s bekleniyor...")
                    time.sleep(wait_time)
                else:
                    logging.warning(f"HTTP Hata Kodu: {resp.status_code}")
                    break
            except Exception as e:
                logging.warning(f"İstek hatası: {e}")
                time.sleep(5)
    logging.error(f"[{region_name}] Tüm denemeler başarısız oldu!")
    return []

# Tipolojik ve Kronolojik Sınıflandırma
def classify_category(tags: Dict[str, str]) -> str:
    h = tags.get("historic", "")
    site_type = tags.get("site_type", "").lower()
    name = tags.get("name", "").lower()

    if h == "archaeological_site":
        if "tell" in site_type or "tumulus" in site_type or "höyük" in name or "tepe" in name:
            return "Höyük / Tümülüs"
        return "Antik Kent / Ören Yeri"
    elif h in ["castle", "fort"]:
        return "Kale / Hisar / Tahkimat"
    elif h == "ruins":
        return "Harabe / Antik Kalıntı"
    elif h == "tomb":
        return "Kaya Mezarı / Lahit / Tümülüs"
    elif h == "aqueduct":
        return "Tarihi Su Kemeri"
    elif h == "cistern":
        return "Antik Sarnıç"
    elif h in ["monument", "memorial"]:
        return "Antik Anıt / Dikilitaş"
    elif h in ["palace", "manor"]:
        return "Saray / Kasır / Konak"
    elif tags.get("ref:tay"):
        return "Arkeolojik Yerleşme (TAY)"
    return "Tarihi Kültür Varlığı"

def classify_period_epoch(tags: Dict[str, str]) -> Tuple[str, str]:
    period = tags.get("period") or tags.get("heritage:period") or tags.get("era")
    start_date = tags.get("start_date") or tags.get("historic:civilization")
    dating = str(start_date).strip() if start_date else "Bilinmiyor"

    if period:
        return period, dating

    name_lower = tags.get("name", "").lower()
    
    # Sayısal yıl eşleştirme
    year = None
    m = re.search(r"(-?\d{3,4})", dating)
    if m:
        try:
            year = int(m.group(1))
        except ValueError:
            pass

    if year is not None:
        if year < -3000:
            return "Neolitik / Kalkolitik", dating
        elif -3000 <= year < -1200:
            return "Tunç Çağı / Hitit", dating
        elif -1200 <= year < -330:
            return "Demir Çağı / Klasik (Frig / Lidya / Urartu)", dating
        elif -330 <= year < 0:
            return "Helenistik Dönem", dating
        elif 0 <= year < 395:
            return "Roma İmparatorluğu", dating
        elif 395 <= year < 1071:
            return "Bizans (Doğu Roma)", dating
        elif 1071 <= year < 1453:
            return "Selçuklu / Anadolu Beylikleri", dating
        elif 1453 <= year < 1923:
            return "Osmanlı Dönemi", dating

    # İsim ve bağlam bazlı çıkarım
    if any(k in name_lower for k in ["höyük", "çatalhöyük", "göbeklitepe", "neolitik"]):
        return "Neolitik / Kalkolitik", dating
    if any(k in name_lower for k in ["hitit", "hattusa", "alacahöyük", "kaneş"]):
        return "Hitit / Tunç Çağı", dating
    if any(k in name_lower for k in ["tepe", "tümülüs", "nekropol", "kaya mezar"]):
        return "Klasik / Helenistik", dating
    if any(k in name_lower for k in ["tiyatro", "agora", "stadyum", "odeon", "hamam", "su kemeri", "sarnıç", "roma"]):
        return "Roma İmparatorluğu", dating
    if any(k in name_lower for k in ["surlar", "bazilika", "manastır", "şapel", "bizans", "kale"]):
        return "Bizans (Doğu Roma)", dating
    if any(k in name_lower for k in ["selçuklu", "medrese", "kervansaray", "kümbet", "han"]):
        return "Selçuklu / Beylikler", dating
    if any(k in name_lower for k in ["osmanlı", "cami", "köşk", "hisar", "tabya", "saray"]):
        return "Osmanlı Dönemi", dating

    return "Antik / Tarihi Dönem", dating

class HeritageETLPipeline:
    def __init__(self):
        self.seen_ids: Set[str] = set()
        self.spatial_index: Dict[Tuple[int, int], List[Tuple[float, float, str]]] = {}
        self.features: List[Dict[str, Any]] = []

    def is_spatial_duplicate(self, lon: float, lat: float, name: str, threshold_m: float = 25.0) -> bool:
        """25 metre içindeki benzer isimli mükerrer nesneleri eler."""
        cell = (int(lon * 100), int(lat * 100))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                neighbor = (cell[0] + dx, cell[1] + dy)
                if neighbor in self.spatial_index:
                    for ex_lon, ex_lat, ex_name in self.spatial_index[neighbor]:
                        d_lon = (lon - ex_lon) * 111320.0 * math.cos(math.radians(lat))
                        d_lat = (lat - ex_lat) * 110540.0
                        dist = math.hypot(d_lon, d_lat)
                        if dist < threshold_m:
                            # Aynı veya çok yakın isim kontrolü
                            n1 = name.lower()
                            n2 = ex_name.lower()
                            if n1 == n2 or n1 in n2 or n2 in n1:
                                return True

        if cell not in self.spatial_index:
            self.spatial_index[cell] = []
        self.spatial_index[cell].append((lon, lat, name))
        return False

    def transform_element(self, elem: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lat = elem.get("lat") or elem.get("center", {}).get("lat")
        lon = elem.get("lon") or elem.get("center", {}).get("lon")

        if lat is None or lon is None:
            return None

        # Sınır denetimi
        if not (TR_BOUNDS["min_lat"] <= lat <= TR_BOUNDS["max_lat"] and 
                TR_BOUNDS["min_lon"] <= lon <= TR_BOUNDS["max_lon"]):
            return None

        osm_id = f"{elem['type'][0].upper()}{elem['id']}"
        if osm_id in self.seen_ids:
            return None

        tags = elem.get("tags", {})
        name = tags.get("name") or tags.get("name:tr") or tags.get("old_name") or tags.get("alt_name")
        if not name:
            cat_label = classify_category(tags)
            name = f"Tescilli {cat_label}"

        if self.is_spatial_duplicate(lon, lat, name):
            return None

        self.seen_ids.add(osm_id)

        category = classify_category(tags)
        period, dating = classify_period_epoch(tags)

        # İdari Bağlılık
        prov = tags.get("addr:province") or ""
        dist = tags.get("addr:district") or ""
        if prov and dist:
            province_district = f"{prov}, {dist}"
        elif prov:
            province_district = prov
        else:
            province_district = "Türkiye"

        feature = {
            "type": "Feature",
            "id": f"TR-HIST-{osm_id}",
            "geometry": {
                "type": "Point",
                "coordinates": [round(lon, 6), round(lat, 6)]
            },
            "properties": {
                "id": f"TR-HIST-{osm_id}",
                "name": name,
                "category": category,
                "period_epoch": period,
                "approx_dating": dating,
                "province_district": province_district,
                "coordinates": [round(lon, 6), round(lat, 6)],
                "protection_status": tags.get("heritage:operator") or tags.get("protection_title") or "T.C. Kültür Envanteri Tescilli",
                "source_citation": f"OSM {elem['type'].upper()} #{elem['id']}" + (f"; TAY Ref: {tags.get('ref:tay')}" if tags.get("ref:tay") else "")
            }
        }
        return feature

    def run(self):
        logging.info("=== TÜRKİYE GENELİ ARKEOLOJİK VE TARİHİ ENVANTER ETL BAŞLATILDI ===")

        for r in REGIONS:
            query = build_overpass_query(r["bbox"])
            raw_elements = query_overpass_with_fallback(query, r["name"])
            count_before = len(self.features)
            for el in raw_elements:
                feat = self.transform_element(el)
                if feat:
                    self.features.append(feat)
            logging.info(f"[{r['name']}] Eklendi: {len(self.features) - count_before} yeni nokta.")
            time.sleep(2.0)

        logging.info(f"Toplam Tekilleştirilmiş Kayıt Sayısı: {len(self.features)}")

        # GeoJSON Kaydetme
        geojson_doc = {
            "type": "FeatureCollection",
            "name": "turkiye_tum_tarihi_yapilar",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
                }
            },
            "features": self.features
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(geojson_doc, f, ensure_ascii=False, indent=2)

        logging.info(f"Başarıyla kaydedildi: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    pipeline = HeritageETLPipeline()
    pipeline.run()
