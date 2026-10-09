import os
import time
import json
import requests

DEST_DIR = r"C:\Users\busra.sener\Desktop\tarihi-harita\assets\routes"
os.makedirs(DEST_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'TarihiHaritaBot/2.0 (contact: busra@tarihiharita.org)'}

SEARCH_ITEMS = {
    # İlber Ortaylı Sur İçi Rotası
    "ortayli_eminonu": "Eminönü Yeni Cami Istanbul",
    "ortayli_riza_pasa": "Grand Bazaar Mercan Istanbul",
    "ortayli_suleymaniye": "Süleymaniye Mosque Istanbul",
    "ortayli_kucukpazar": "Suleymaniye from Golden Horn Istanbul",
    "ortayli_zeyrek": "Zeyrek Mosque Istanbul",
    "ortayli_fatih": "Fatih Mosque Istanbul",
    "ortayli_balat": "Balat Istanbul colourful houses",
    "ortayli_ayvansaray": "Tekfur Palace Istanbul",
    "ortayli_edirnekapi": "Theodosian Walls Istanbul",
    "ortayli_kariye": "Chora Church Istanbul",
    "ortayli_yedikule": "Yedikule Fortress Istanbul",
    "ortayli_cerrahpasa": "Cerrahpasa Mosque Istanbul",
    "ortayli_beyazit": "Istanbul University main gate Beyazit",
    "ortayli_sultanahmet": "Sultanahmet Square Istanbul",

    # Evliya Çelebi Rotası
    "celebi_ahi": "Ahi Celebi Mosque Istanbul",
    "celebi_galata": "Galata Tower Istanbul",
    "celebi_eyup": "Eyüp Sultan Mosque courtyard",
    "celebi_mevlevi": "Galata Mevlevihanesi Istanbul",
    "celebi_uskudar": "Mihrimah Sultan Mosque Uskudar",
    "celebi_silahtaraga": "santralistanbul Bilgi University",

    # Likya Yolu
    "likya_kayakoy": "Kayaköy Fethiye",
    "likya_patara": "Patara Bouleuterion Assembly Hall",
    "likya_kas": "Antiphellos theatre Kas",
    "likya_kekova": "Simena Castle Kekova",
    "likya_myra": "Myra rock cut tombs Demre",
    "likya_olympos": "Olympos ruins Antalya",
    "likya_phaselis": "Phaselis aqueduct Antalya",

    # Kadim Anadolu Parkurları (Hitit & Frig)
    "hitit_hattusa": "Lion Gate Hattusa",
    "hitit_yazilikaya": "Yazilikaya reliefs Hattusa",
    "hitit_alacahoyuk": "Alacahöyük sphinx gate",
    "frig_midas": "Midas monument Yazilikaya",
    "frig_ayazini": "Ayazini church Afyon"
}

print(f"Starting harvest for {len(SEARCH_ITEMS)} stops...")

downloaded = {}
for key, query in SEARCH_ITEMS.items():
    filename = f"{key}.jpg"
    target_path = os.path.join(DEST_DIR, filename)
    
    # If already downloaded and > 10KB, skip
    if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
        print(f"[EXISTS] {key} ({os.path.getsize(target_path)} bytes)")
        downloaded[key] = f"assets/routes/{filename}"
        continue

    try:
        api_url = (
            "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={requests.utils.quote(query)}&gsrnamespace=6&gsrlimit=1"
            "&prop=imageinfo&iiprop=url&iiurlwidth=960&format=json"
        )
        r = requests.get(api_url, headers=HEADERS, timeout=12)
        d = r.json()
        pages = d.get('query', {}).get('pages', {})
        if not pages:
            print(f"[NOT FOUND] {key}: {query}")
            continue
            
        page = next(iter(pages.values()))
        ii = page.get('imageinfo', [{}])[0]
        thumb_url = ii.get('thumburl') or ii.get('url')
        
        if thumb_url:
            r_img = requests.get(thumb_url, headers=HEADERS, timeout=15)
            if r_img.status_code == 200 and len(r_img.content) > 5000:
                with open(target_path, 'wb') as f:
                    f.write(r_img.content)
                print(f"[OK] {key} -> {filename} ({len(r_img.content)} bytes)")
                downloaded[key] = f"assets/routes/{filename}"
            else:
                print(f"[HTTP FAIL] {key}: {r_img.status_code}")
        time.sleep(0.3)
    except Exception as e:
        print(f"[ERR] {key}: {e}")

print(f"\nCompleted! Harvested {len(downloaded)}/{len(SEARCH_ITEMS)} images.")
