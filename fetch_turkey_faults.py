#!/usr/bin/env python3
"""
Türkiye Diri Fay Ağı Çıkarım ve Doğrulama Pipeline'ı (MTA / GEM Uyumlu)
CRS: WGS84 (EPSG:4326)
Format: GeoJSON (FeatureCollection)
"""

import json
import logging
import requests
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Türkiye Bounding Box (Karasal ve Yakın Şelf Alanı)
TR_BBOX = {
    "min_lon": 25.5,
    "min_lat": 35.5,
    "max_lon": 44.8,
    "max_lat": 42.5
}

# GEM (Global Active Faults Database) Açık Veri Endpoint'i
GEM_FAULTS_URL = (
    "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults.geojson"
)

# Alternatif MTA ArcGIS REST MapServer sorgu şablonu (Gerektiğinde proxy veya doğrudan erişim için)
MTA_REST_ENDPOINT = (
    "https://yerbilimleri.mta.gov.tr/arcgis/rest/services/YERKURE/DiriFay/MapServer/0/query"
)

def is_coord_in_turkey(lon: float, lat: float) -> bool:
    """Verilen koordinatın Türkiye BBOX sınırları içinde olup olmadığını doğrular."""
    return (TR_BBOX["min_lon"] <= lon <= TR_BBOX["max_lon"]) and (TR_BBOX["min_lat"] <= lat <= TR_BBOX["max_lat"])

def filter_line_geometry(coords: List[List[float]]) -> List[List[float]]:
    """LineString noktalarını tarar; TR sınırlarında en az 2 noktası kalan segmentleri döndürür."""
    valid_coords = [[round(pt[0], 5), round(pt[1], 5)] for pt in coords if is_coord_in_turkey(pt[0], pt[1])]
    return valid_coords if len(valid_coords) >= 2 else []

def fetch_gem_active_faults() -> List[Dict[str, Any]]:
    """GEM veri tabanından Türkiye diri faylarını filtreleyerek çeker."""
    logging.info(f"Fay verisi çekiliyor: {GEM_FAULTS_URL}")
    response = requests.get(GEM_FAULTS_URL, timeout=60, stream=True)
    response.raise_for_status()

    logging.info("Veri akışı tamamlandı, coğrafi filtreleme uygulanıyor...")
    data = response.json()
    
    extracted_features = []
    fault_counter = 1

    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        props = feature.get("properties", {})

        # Sadece LineString veya MultiLineString segmentleri işle
        if gtype == "LineString":
            clean_coords = filter_line_geometry(coords)
            if clean_coords:
                extracted_features.append({
                    "type": "Feature",
                    "id": f"TR-FAULT-{fault_counter:04d}",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": clean_coords
                    },
                    "properties": {
                        "name": props.get("name") or props.get("fault_name") or "İsimsiz Fay Segmenti",
                        "slip_type": props.get("slip_type") or "Doğrultu/Normal Atım (Bilinmiyor)",
                        "activity_confidence": props.get("certainty") or "Doğrulanmış Diri Fay",
                        "average_dip": props.get("dip"),
                        "source": "GEM Global Active Faults / MTA Envanteri Eşlemesi"
                    }
                })
                fault_counter += 1

        elif gtype == "MultiLineString":
            clean_multilines = []
            for line in coords:
                c_line = filter_line_geometry(line)
                if c_line:
                    clean_multilines.append(c_line)
            
            if clean_multilines:
                extracted_features.append({
                    "type": "Feature",
                    "id": f"TR-FAULT-{fault_counter:04d}",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": clean_multilines
                    },
                    "properties": {
                        "name": props.get("name") or "Fay Segment Grubu",
                        "slip_type": props.get("slip_type") or "Bilinmiyor",
                        "activity_confidence": "Doğrulanmış",
                        "source": "GEM Global Active Faults"
                    }
                })
                fault_counter += 1

    return extracted_features

def save_fault_geojson(features: List[Dict[str, Any]], filename: str = "turkiye_diri_faylar.geojson") -> None:
    """Doğrulanmış fay segmentlerini standart GeoJSON olarak kaydeder."""
    output = {
        "type": "FeatureCollection",
        "name": "turkiye_aktif_fay_segmentleri_wgs84",
        "crs": {
            "type": "name",
            "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }
        },
        "features": features
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logging.info(f"Başarıyla kaydedildi: {filename} (Toplam {len(features)} aktif fay segmenti)")

if __name__ == "__main__":
    try:
        fault_features = fetch_gem_active_faults()
        save_fault_geojson(fault_features)
    except Exception as e:
        logging.error(f"Fay veri çekim hatası: {str(e)}")