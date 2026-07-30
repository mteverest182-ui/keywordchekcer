# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
import sys
import traceback

app = Flask(__name__)
CORS(app)  # Izinkan akses dari semua domain

# ============================================================
# KONFIGURASI
# ============================================================
# Dapatkan token dari https://scrape.do/signup
SCRAPE_DO_TOKEN = 'YOUR_SCRAPE_DO_TOKEN'  # <-- GANTI DENGAN TOKEN ANDA

# ============================================================
# FUNGSI PENCARIAN DENGAN SCRAPE.DO
# ============================================================
def search_google(query, num_results=10):
    """
    Mencari di Google menggunakan Scrape.do API
    Mengembalikan list of dict: {url, title, snippet}
    """
    
    # Cek apakah token sudah diisi
    if not SCRAPE_DO_TOKEN or SCRAPE_DO_TOKEN == 'YOUR_SCRAPE_DO_TOKEN':
        print("⚠️ API Key Scrape.do belum diisi!")
        return []
    
    # Endpoint Scrape.do untuk Google Search
    url = "https://api.scrape.do/plugin/google/search"
    
    params = {
        'token': SCRAPE_DO_TOKEN,
        'q': query,
        'gl': 'id',      # Indonesia
        'hl': 'id',      # Bahasa Indonesia
        'num': num_results
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print(f"🔍 Mencari: {query}")
        print(f"📡 URL: {url}")
        print(f"📋 Params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return []
        
        data = response.json()
        
        # Debug: lihat struktur data
        print(f"📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        results = []
        
        # Ambil dari organic_results
        if 'organic_results' in data:
            organic = data['organic_results']
            print(f"✅ Organic results found: {len(organic)}")
            for item in organic[:num_results]:
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', 'No Title'),
                    'snippet': item.get('snippet', '')
                })
        else:
            # Coba struktur lain (fallback)
            print("⚠️ Tidak ada 'organic_results', mencoba struktur lain...")
            
            # Coba dari 'results'
            if 'results' in data:
                for item in data['results'][:num_results]:
                    results.append({
                        'url': item.get('url', ''),
                        'title': item.get('title', 'No Title'),
                        'snippet': item.get('description', '')
                    })
            
            # Coba dari 'organic'
            elif 'organic' in data:
                for item in data['organic'][:num_results]:
                    results.append({
                        'url': item.get('link', ''),
                        'title': item.get('title', 'No Title'),
                        'snippet': item.get('snippet', '')
                    })
        
        # Jika tetap tidak ada hasil, berikan link ke Google
        if not results:
            print("⚠️ Tidak ada hasil, memberikan link ke Google")
            results.append({
                'url': f'https://www.google.com/search?q={query}',
                'title': f'Cari "{query}" di Google',
                'snippet': 'Klik link ini untuk melihat hasil langsung di Google.'
            })
        
        return results
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Server Scrape.do tidak merespon")
        return []
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Gagal terhubung ke Scrape.do")
        return []
    except Exception as e:
        print(f"❌ Error Scrape.do: {e}")
        traceback.print_exc()
        return []

# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def index():
    return jsonify({
        'name': 'Google Search API',
        'status': 'running',
        'source': 'Scrape.do',
        'endpoints': {
            '/search': 'GET - Cari di Google (parameter: q, limit)',
            '/health': 'GET - Cek status server'
        },
        'config': {
            'token_configured': bool(SCRAPE_DO_TOKEN and SCRAPE_DO_TOKEN != 'YOUR_SCRAPE_DO_TOKEN')
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Google Search API running with Scrape.do',
        'python_version': sys.version,
        'token_configured': bool(SCRAPE_DO_TOKEN and SCRAPE_DO_TOKEN != 'YOUR_SCRAPE_DO_TOKEN')
    })

@app.route('/search')
def search_endpoint():
    """Endpoint utama untuk pencarian"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    # Validasi
    if not query:
        return jsonify({'error': 'Parameter "q" diperlukan'}), 400
    
    if limit > 50:
        limit = 50  # Batasi maksimal 50
    
    try:
        print(f"📥 Request: query='{query}', limit={limit}")
        results = search_google(query, num_results=limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'source': 'scrape.do',
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Error di /search: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'query': query,
            'status': 'error'
        }), 500

# ============================================================
# ERROR HANDLING
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================
# START SERVER
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("🚀 Google Search API with Scrape.do")
    print(f"📡 Port: {port}")
    print(f"🔑 Token: {'✅ Configured' if SCRAPE_DO_TOKEN and SCRAPE_DO_TOKEN != 'YOUR_SCRAPE_DO_TOKEN' else '❌ Not configured'}")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
