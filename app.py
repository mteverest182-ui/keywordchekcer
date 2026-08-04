from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
import sys
import traceback

app = Flask(__name__)
CORS(app) 

SCRAPE_DO_TOKEN = 'dc3b8dd0348b41f39e156831fb1885de7976fe4b6e2' 

# ============================================================
# FUNGSI PENCARIAN GOOGLE (SEARCH)
# ============================================================
def search_google(query, num_results=10):
    """
    Mencari di Google menggunakan Scrape.do API
    Mengembalikan list of dict: {url, title, snippet}
    """
    
    if not SCRAPE_DO_TOKEN or SCRAPE_DO_TOKEN == 'YOUR_SCRAPE_DO_TOKEN':
        print("⚠️ API Key Scrape.do belum diisi!")
        return []
    
    url = "https://api.scrape.do/plugin/google/search"
    
    params = {
        'token': SCRAPE_DO_TOKEN,
        'q': query,
        'gl': 'id',     
        'hl': 'id',     
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
        
        print(f"📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        results = []
        
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
            print("⚠️ Tidak ada 'organic_results', mencoba struktur lain...")
            
            if 'results' in data:
                for item in data['results'][:num_results]:
                    results.append({
                        'url': item.get('url', ''),
                        'title': item.get('title', 'No Title'),
                        'snippet': item.get('description', '')
                    })
            
            elif 'organic' in data:
                for item in data['organic'][:num_results]:
                    results.append({
                        'url': item.get('link', ''),
                        'title': item.get('title', 'No Title'),
                        'snippet': item.get('snippet', '')
                    })
        
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
# FUNGSI TRENDING (BARU!)
# ============================================================
def get_trending_indonesia(limit=10, hours=24):
    """
    Mengambil topik trending di Indonesia menggunakan Scrape.do API
    Mengembalikan list of dict: {title, search_volume, growth_percentage, ...}
    """
    
    if not SCRAPE_DO_TOKEN or SCRAPE_DO_TOKEN == 'YOUR_SCRAPE_DO_TOKEN':
        print("⚠️ API Key Scrape.do belum diisi!")
        return []
    
    url = "https://api.scrape.do/plugin/google/trending"
    
    params = {
        'token': SCRAPE_DO_TOKEN,
        'geo': 'ID',         # Indonesia
        'hl': 'id',          # Bahasa Indonesia
        'hours': hours,      # 4, 24, 48, 168
        'cat': 0             # 0 = All categories
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print(f"🔥 Mengambil trending di Indonesia...")
        print(f"📡 URL: {url}")
        print(f"📋 Params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return []
        
        data = response.json()
        
        print(f"📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        results = []
        
        # Ambil dari 'trends'
        if 'trends' in data:
            trends = data['trends']
            print(f"✅ Trending found: {len(trends)}")
            for item in trends[:limit]:
                results.append({
                    'title': item.get('title', ''),
                    'search_volume': item.get('search_volume', 0),
                    'growth_percentage': item.get('growth_percentage', ''),
                    'started_at': item.get('started_at', ''),
                    'status': item.get('status', ''),
                    'url': f"https://www.google.com/search?q={item.get('title', '')}"
                })
        else:
            print("⚠️ Tidak ada 'trends' dalam response")
            print(f"📄 Response: {json.dumps(data, indent=2)[:500]}...")
        
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
            '/trending': 'GET - Trending Indonesia (parameter: limit, hours)',
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
    """Endpoint untuk pencarian"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Parameter "q" diperlukan'}), 400
    
    if limit > 50:
        limit = 50 
    
    try:
        print(f"📥 Request: query='{query}', limit={limit}")
        results = search_google(query, num_results=limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'source': 'scrape.do',
            'type': 'search',
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
# ROUTE TRENDING (BARU!)
# ============================================================
@app.route('/trending')
def trending_endpoint():
    """Endpoint untuk trending di Indonesia"""
    limit = int(request.args.get('limit', 10))
    hours = int(request.args.get('hours', 24))
    
    if limit > 50:
        limit = 50
    
    if hours not in [4, 24, 48, 168]:
        hours = 24
    
    try:
        print(f"📥 Request: trending, limit={limit}, hours={hours}")
        results = get_trending_indonesia(limit=limit, hours=hours)
        
        return jsonify({
            'trending': results,
            'total': len(results),
            'source': 'scrape.do',
            'type': 'trending',
            'geo': 'Indonesia',
            'hours': hours,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Error di /trending: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
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
    print("📌 Endpoints:")
    print("  /search?q=keyword&limit=10  - Pencarian Google")
    print("  /trending?limit=10&hours=24 - Trending Indonesia")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
