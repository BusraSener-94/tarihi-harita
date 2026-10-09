#!/usr/bin/env python3
"""
Türkiye Arkeolojik Miras - Diri Fay Sismik Risk Matrisi Analiz Motoru
Yöntem: Jeodezik Nokta-Doğru Segmenti En Kısa Mesafe Algoritması (Orthogonal Distance)
Girdi: Arkeolojik Alanlar GeoJSON + Diri Faylar GeoJSON
Çıktı: Markdown Raporu (stdout/dosya) + risk_analiz_raporu.json
"""

import json
import math
import os
import sys
from typing import Dict, Any, List, Tuple

# 27 Çekirdek Tescilli Alan (Harici dosya yoksa varsayılan girdi)
DEFAULT_HERITAGE_DATA = [
    {"id": "TR-HIST-001", "name": "Göbekli Tepe", "lon": 38.9225, "lat": 37.2232, "epoch": "Çanak Çömleksiz Neolitik"},
    {"id": "TR-HIST-002", "name": "Çatalhöyük", "lon": 32.8273, "lat": 37.6675, "epoch": "Neolitik, Kalkolitik"},
    {"id": "TR-HIST-003", "name": "Hattuşa", "lon": 34.6153, "lat": 40.0197, "epoch": "Hitit İmparatorluk"},
    {"id": "TR-HIST-004", "name": "Efes", "lon": 27.3411, "lat": 37.9409, "epoch": "Klasik, Helenistik, Roma"},
    {"id": "TR-HIST-005", "name": "Nemrut Dağı", "lon": 38.7408, "lat": 37.9806, "epoch": "Helenistik (Kommagene)"},
    {"id": "TR-HIST-006", "name": "Troya", "lon": 26.2389, "lat": 39.9575, "epoch": "Erken Tunç - Roma"},
    {"id": "TR-HIST-007", "name": "Hierapolis", "lon": 29.1239, "lat": 37.9258, "epoch": "Helenistik, Roma, Bizans"},
    {"id": "TR-HIST-008", "name": "Pergamon Akropolü", "lon": 27.1842, "lat": 39.1325, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-009", "name": "Xanthos", "lon": 29.3181, "lat": 36.3567, "epoch": "Likya, Helenistik, Roma"},
    {"id": "TR-HIST-010", "name": "Letoon", "lon": 29.2897, "lat": 36.3325, "epoch": "Likya, Helenistik, Roma"},
    {"id": "TR-HIST-011", "name": "Aphrodisias", "lon": 28.7236, "lat": 37.7083, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-012", "name": "Ani Harabeleri", "lon": 43.5728, "lat": 40.5075, "epoch": "Bagratuni, Selçuklu"},
    {"id": "TR-HIST-013", "name": "Arslantepe Höyüğü", "lon": 38.3619, "lat": 38.3811, "epoch": "Kalkolitik, Hitit"},
    {"id": "TR-HIST-014", "name": "Gordion", "lon": 31.9861, "lat": 39.6508, "epoch": "Erken Tunç, Frig"},
    {"id": "TR-HIST-015", "name": "Sagalassos", "lon": 30.5208, "lat": 37.6775, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-016", "name": "Perge", "lon": 30.8522, "lat": 36.9606, "epoch": "Tunç Çağı, Roma"},
    {"id": "TR-HIST-017", "name": "Miletos", "lon": 27.2764, "lat": 37.5308, "epoch": "Arkaik, Roma"},
    {"id": "TR-HIST-018", "name": "Priene", "lon": 27.2975, "lat": 37.6594, "epoch": "Geç Klasik, Helenistik"},
    {"id": "TR-HIST-019", "name": "Çayönü Tepesi", "lon": 39.7303, "lat": 38.2178, "epoch": "Çanak Çömleksiz Neolitik"},
    {"id": "TR-HIST-020", "name": "Aizanoi", "lon": 29.6106, "lat": 39.2017, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-021", "name": "Alacahöyük", "lon": 34.6989, "lat": 40.2339, "epoch": "Eski Tunç, Hitit"},
    {"id": "TR-HIST-022", "name": "Kültepe Kaniş-Karum", "lon": 35.6347, "lat": 38.8508, "epoch": "Orta Tunç (Asur)"},
    {"id": "TR-HIST-023", "name": "Sardes", "lon": 28.0403, "lat": 38.4883, "epoch": "Demir Çağı (Lidya), Roma"},
    {"id": "TR-HIST-024", "name": "Stratonikeia", "lon": 28.0644, "lat": 37.3131, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-025", "name": "Zeugma", "lon": 37.8683, "lat": 37.0578, "epoch": "Helenistik, Roma"},
    {"id": "TR-HIST-026", "name": "Karain Mağarası", "lon": 30.5706, "lat": 36.9786, "epoch": "Paleolitik Çağ"},
    {"id": "TR-HIST-027", "name": "Didyma Apollon", "lon": 27.2564, "lat": 37.3850, "epoch": "Arkaik, Roma"}
]

# Varsayılan Diri Fay Ağı Segmentleri (Harici GeoJSON yüklenemezse fallback)
FALLBACK_FAULTS = [
    {
        "name": "Kuzey Anadolu Fayı (KAF Ana Kol)",
        "type": "Sağ Yanal Atımlı",
        "coords": [[26.5, 40.5], [28.5, 40.8], [31.2, 40.72], [34.0, 41.0], [37.2, 40.35], [41.0, 39.3]]
    },
    {
        "name": "Doğu Anadolu Fayı (DAF Ana Kol)",
        "type": "Sol Yanal Atımlı",
        "coords": [[41.0, 39.3], [39.6, 38.6], [38.0, 37.9], [36.6, 36.9], [36.1, 36.2]]
    },
    {
        "name": "Gediz Grabeni Fay Sistemi",
        "type": "Normal Fay",
        "coords": [[27.3, 38.65], [28.04, 38.49], [28.4, 38.38], [28.9, 38.25]]
    },
    {
        "name": "Büyük Menderes Grabeni Fay Sistemi",
        "type": "Normal Fay",
        "coords": [[27.3, 37.75], [28.0, 37.88], [28.72, 37.71], [29.12, 37.93]]
    },
    {
        "name": "Fethiye-Burdur Fay Zonu",
        "type": "Sol Yanal Oblik Normal",
        "coords": [[29.1, 36.65], [29.6, 37.15], [30.2, 37.7], [30.55, 37.9]]
    }
]

def point_to_segment_distance_meters(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """WGS84 derecelerini yerel düzlemsel koordinatlara dönüştürerek noktanın doğru parçasına dik mesafesini hesaplar."""
    mid_lat = math.radians((py + ((y1 + y2) / 2.0)) / 2.0)
    kx = 111320.0 * math.cos(mid_lat)
    ky = 110540.0

    px_m, py_m = px * kx, py * ky
    x1_m, y1_m = x1 * kx, y1 * ky
    x2_m, y2_m = x2 * kx, y2 * ky

    dx = x2_m - x1_m
    dy = y2_m - y1_m

    if dx == 0 and dy == 0:
        return math.hypot(px_m - x1_m, py_m - y1_m)

    # İzdüşüm faktörü t
    t = ((px_m - x1_m) * dx + (py_m - y1_m) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    nearest_x = x1_m + t * dx
    nearest_y = y1_m + t * dy

    return math.hypot(px_m - nearest_x, py_m - nearest_y)

def calculate_min_distance_to_fault(pt_lon: float, pt_lat: float, fault_coords: List[List[float]]) -> float:
    min_dist = float('inf')
    for i in range(len(fault_coords) - 1):
        x1, y1 = fault_coords[i][0], fault_coords[i][1]
        x2, y2 = fault_coords[i+1][0], fault_coords[i+1][1]
        dist = point_to_segment_distance_meters(pt_lon, pt_lat, x1, y1, x2, y2)
        if dist < min_dist:
            min_dist = dist
    return min_dist

def load_faults_from_geojson(geojson_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(geojson_path):
        return FALLBACK_FAULTS

    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    faults = []
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        name = props.get("name") or props.get("fault_name") or "İsimsiz Diri Fay Segmenti"
        ftype = props.get("slip_type") or "Doğrultu/Normal Atım"

        if gtype == "LineString":
            faults.append({"name": name, "type": ftype, "coords": coords})
        elif gtype == "MultiLineString":
            for line in coords:
                faults.append({"name": name, "type": ftype, "coords": line})
    return faults if faults else FALLBACK_FAULTS

def classify_risk(dist_m: float) -> Tuple[str, str]:
    if dist_m < 1000:
        return "KRİTİK RİSK (<1 km)", "Fay izi üzerinde / Doğrudan yüzey kırığı tehlikesi"
    elif dist_m < 5000:
        return "YÜKSEK RİSK (1-5 km)", "Şiddetli yakın-alan yer hareketi maruziyeti"
    elif dist_m < 10000:
        return "ORTA RİSK (5-10 km)", "Kuvvetli yer sarsıntısı ve zemin etkisi"
    else:
        return "DÜŞÜK DOĞRUDAN ETKİ (>10 km)", "Uzak alan dalga yayılımı"

def run_seismic_risk_analysis(heritage_sites: List[Dict[str, Any]], faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for site in heritage_sites:
        slon, slat = site["lon"], site["lat"]
        closest_fault = None
        min_dist_m = float('inf')

        for fault in faults:
            d = calculate_min_distance_to_fault(slon, slat, fault["coords"])
            if d < min_dist_m:
                min_dist_m = d
                closest_fault = fault

        risk_category, impact_desc = classify_risk(min_dist_m)
        dist_km = round(min_dist_m / 1000.0, 2)

        results.append({
            "site_id": site["id"],
            "site_name": site["name"],
            "period_epoch": site.get("epoch", "Belirtilmemiş"),
            "coordinates": [slon, slat],
            "nearest_fault_name": closest_fault["name"],
            "fault_mechanism": closest_fault["type"],
            "distance_meters": round(min_dist_m, 1),
            "distance_km": dist_km,
            "risk_category": risk_category,
            "impact_mechanism": impact_desc
        })

    # Mesafeye göre en riskliden en uzağa sırala
    results.sort(key=lambda x: x["distance_meters"])
    return results

def generate_markdown_table(results: List[Dict[str, Any]]) -> str:
    md = []
    md.append("### SİSMİK RİSK VE FAY MARUZİYETİ ANALİZ RAPORU\n")
    md.append("| No | Arkeolojik Alan | Dönem | En Yakın Diri Fay | Fay Türü | Mesafe (km) | Risk Kategorisi |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        md.append(f"| `{r['site_id']}` | **{r['site_name']}** | {r['period_epoch']} | {r['nearest_fault_name']} | {r['fault_mechanism']} | **{r['distance_km']} km** | {r['risk_category']} |")
    return "\n".join(md)

if __name__ == "__main__":
    faults_path = "turkiye_diri_faylar.geojson"
    faults = load_faults_from_geojson(faults_path)
    
    print(f"[*] Toplam {len(DEFAULT_HERITAGE_DATA)} arkeolojik alan ve {len(faults)} fay segmenti işleniyor...")
    analysis_results = run_seismic_risk_analysis(DEFAULT_HERITAGE_DATA, faults)

    # 1. JSON Çıktısı Kaydet
    output_json = "risk_analiz_raporu.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    print(f"[+] Yapılandırılmış JSON raporu kaydedildi: {output_json}")

    # 2. Markdown Tablosunu Terminale ve Dosyaya Yazdır
    md_report = generate_markdown_table(analysis_results)
    with open("risk_analiz_raporu.md", "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"[+] Markdown raporu kaydedildi: risk_analiz_raporu.md\n")
    print(md_report)