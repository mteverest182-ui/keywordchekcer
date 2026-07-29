# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app)  # Izinkan akses dari mana saja

# ============================================================
# GOOGLE SEARCH SCRAPER
# ============================================================
class GoogleSearchScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Setup ChromeDriver dengan opsi headless"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        
        # Untuk Render, gunakan Chrome yang sudah tersedia
        # Atau install ChromeDriver otomatis
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ ChromeDriver berhasil diinisialisasi")
        return self.driver
    
    def search(self, query, num_results=10):
        if not self.driver:
            self.setup_driver()
        
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
        print(f"🔍 Mencari: {query}")
        
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
            print(f"❌ Error: {e}")
            return []
    
    def close(self):
        if self.driver:
            self.driver.quit()

# ============================================================
# SCRAPER INSTANCE
# ============================================================
scraper = None

def get_scraper():
    global scraper
    if scraper is None:
        scraper = GoogleSearchScraper(headless=True)
        scraper.setup_driver()
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
        scraper = get_scraper()
        results = scraper.search(query, num_results=limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Google Search API with Headless Chrome'})

@app.route('/')
def index():
    return jsonify({
        'name': 'Google Search API',
        'status': 'running',
        'endpoints': {
            '/search': 'GET - Cari di Google (parameter: q, limit)',
            '/health': 'GET - Cek status server'
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
    print(f"🚀 Google Search API dengan Headless Chrome")
    print(f"📡 Server berjalan di port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
