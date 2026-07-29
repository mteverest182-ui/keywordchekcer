# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import sys
import json

app = Flask(__name__)
CORS(app)  # Izinkan akses dari mana saja

# ============================================================
# OPSI 1: MENGGUNAKAN SELENIUM + CHROME (JIWA TERSEDIA)
# ============================================================
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from bs4 import BeautifulSoup
    SELENIUM_AVAILABLE = True
    print("✅ Selenium tersedia")
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium tidak tersedia, menggunakan fallback")

# ============================================================
# OPSI 2: FALLBACK - GOOGLESEARCH-PYTHON (TANPA CHROME)
# ============================================================
try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
    print("✅ googlesearch-python tersedia")
except ImportError:
    GOOGLESEARCH_AVAILABLE = False
    print("⚠️ googlesearch-python tidak tersedia")

# ============================================================
# SCRAPER CLASS (SELENIUM VERSION)
# ============================================================
class GoogleSearchScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        if not SELENIUM_AVAILABLE:
            return None
        
        options = Options()
        
        # Mode headless
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        
        # Opsi penting untuk Render
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Opsi tambahan
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        
        # Cari Chrome di berbagai path
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/opt/render/project/src/.chrome/chrome",
            "/opt/render/.cache/chrome/chrome",
            "/opt/chrome/chrome",
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                print(f"✅ Menggunakan Chrome di: {chrome_path}")
                break
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ ChromeDriver berhasil diinisialisasi")
            return self.driver
        except Exception as e:
            print(f"❌ ChromeDriver error: {e}")
            return None
    
    def search(self, query, num_results=10):
        if not self.driver:
            if self.setup_driver() is None:
                return []
        
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
        print(f"🔍 Mencari (Selenium): {query}")
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            if "captcha" in self.driver.page_source.lower() or "sorry" in self.driver.page_source.lower():
                print("⚠️ Google meminta CAPTCHA!")
                return []
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            results = []
            
            result_elements = soup.select('div.g')
            if not result_elements:
                result_elements = soup.find_all('div', class_=lambda c: c and 'g' in c)
            
            for element in result_elements[:num_results]:
                try:
                    link_tag = element.find('a')
                    if not link_tag:
                        continue
                    
                    url = link_tag.get('href', '')
                    if not url or url.startswith('/search'):
                        continue
                    
                    title_tag = element.find('h3')
                    title = title_tag.text.strip() if title_tag else 'No Title'
                    
                    snippet_tag = element.find('div', class_=lambda c: c and ('VwiC3b' in c or 'snippet' in c or 'IsZvec' in c))
                    if not snippet_tag:
                        snippet_tag = element.find('div', class_='st')
                    
                    snippet = snippet_tag.text.strip() if snippet_tag else ''
                    
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet[:200] + '...' if len(snippet) > 200 else snippet
                    })
                except Exception as e:
                    continue
            
            return results
        except Exception as e:
            print(f"❌ Selenium error: {e}")
            return []
    
    def close(self):
        if self.driver:
            self.driver.quit()

# ============================================================
# FUNGSI SEARCH FALLBACK (GOOGLESEARCH-PYTHON)
# ============================================================
def search_google_fallback(query, num_results=10):
    """Fallback menggunakan googlesearch-python (tanpa Chrome)"""
    if not GOOGLESEARCH_AVAILABLE:
        return []
    
    print(f"🔍 Mencari (Fallback): {query}")
    
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append({
                'url': url,
                'title': f"Hasil dari Google: {url.split('/')[-1] or 'No Title'}",
                'snippet': f"Hasil pencarian untuk '{query}'"
            })
        return results
    except Exception as e:
        print(f"❌ Fallback error: {e}")
        return []

# ============================================================
# SCRAPER INSTANCE
# ============================================================
scraper = None
use_fallback = False

def get_scraper():
    global scraper, use_fallback
    
    # Jika fallback sudah diaktifkan, gunakan fallback
    if use_fallback:
        return None
    
    if scraper is None and SELENIUM_AVAILABLE:
        scraper = GoogleSearchScraper(headless=True)
        if scraper.setup_driver() is None:
            print("⚠️ Selenium gagal, beralih ke fallback")
            use_fallback = True
            return None
    
    return scraper

# ============================================================
# ROUTES
# ============================================================
@app.route('/search', methods=['GET'])
def search_google():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Parameter "q" diperlukan'}), 400
    
    try:
        # Coba pakai Selenium dulu
        scraper_instance = get_scraper()
        
        if scraper_instance and not use_fallback:
            results = scraper_instance.search(query, num_results=limit)
            if results:
                return jsonify({
                    'query': query,
                    'results': results,
                    'total': len(results),
                    'source': 'selenium'
                })
            else:
                print("⚠️ Selenium tidak menghasilkan hasil, coba fallback...")
        
        # Fallback ke googlesearch-python
        if GOOGLESEARCH_AVAILABLE:
            results = search_google_fallback(query, num_results=limit)
            return jsonify({
                'query': query,
                'results': results,
                'total': len(results),
                'source': 'fallback'
            })
        else:
            return jsonify({
                'query': query,
                'results': [],
                'total': 0,
                'source': 'none',
                'error': 'Tidak ada metode pencarian yang tersedia'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    status = {
        'status': 'ok',
        'message': 'Google Search API running',
        'selenium': SELENIUM_AVAILABLE,
        'googlesearch': GOOGLESEARCH_AVAILABLE,
        'use_fallback': use_fallback
    }
    return jsonify(status)

@app.route('/')
def index():
    return jsonify({
        'name': 'Google Search API',
        'status': 'running',
        'endpoints': {
            '/search': 'GET - Cari di Google (parameter: q, limit)',
            '/health': 'GET - Cek status server'
        },
        'methods': {
            'selenium': SELENIUM_AVAILABLE,
            'googlesearch': GOOGLESEARCH_AVAILABLE
        }
    })

# ============================================================
# CLEANUP
# ============================================================
import atexit
def cleanup():
    if scraper:
        scraper.close()
atexit.register(cleanup)

# ============================================================
# START SERVER
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("🚀 Google Search API dengan Headless Chrome")
    print(f"📡 Server berjalan di port {port}")
    print(f"🔍 Selenium: {'✅' if SELENIUM_AVAILABLE else '❌'}")
    print(f"🔍 googlesearch: {'✅' if GOOGLESEARCH_AVAILABLE else '❌'}")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
