# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json

app = Flask(__name__)
CORS(app)

# ============================================================
# KONFIGURASI SERPER.DEV
# ============================================================
SERPER_API_KEY = '5eba4712b596a478b034be1809caffbc8f767f47'  # Ganti dengan API Key Anda

# ============================================================
# FUNGSI PENCARIAN
# ============================================================
def search_google(query, num_results=10):
    """Mencari di Google menggunakan Serper.dev API"""
    
    if not SERPER_API_KEY or SERPER_API_KEY == '5eba4712b596a478b034be1809caffbc8f767f47':
        print("⚠️ API Key Serper.dev belum diisi!")
        return []
    
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": query,
        "num": num_results,
        "gl": "id",      # Indonesia
        "hl": "id"       # Bahasa Indonesia
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Mencari: {query}")
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        data = response.json()
        
        if response.status_code != 200:
            print(f"❌ API Error: {data}")
            return []
        
        results = []
        
        # Ambil dari organic results
        for item in data.get('organic', [])[:num_results]:
            results.append({
                'url': item.get('link', ''),
                'title': item.get('title', 'No Title'),
                'snippet': item.get('snippet', '')
            })
        
        # Jika tidak ada organic, coba dari answer_box
        if not results and 'answerBox' in data:
            answer = data['answerBox']
            results.append({
                'url': data.get('searchParameters', {}).get('q', ''),
                'title': answer.get('title', 'Hasil Pencarian'),
                'snippet': answer.get('snippet', answer.get('answer', ''))
            })
        
        return results
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Server Serper.dev tidak merespon")
        return []
    except Exception as e:
        print(f"❌ Error Serper.dev: {e}")
        return []

# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def index():
    return jsonify({
        'name': 'Google Search API',
        'status': 'running',
        'source': 'Serper.dev',
        'endpoints': {
            '/search': 'GET - Cari di Google (parameter: q, limit)',
            '/health': 'GET - Cek status server'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Google Search API running with Serper.dev',
        'api_configured': bool(SERPER_API_KEY and SERPER_API_KEY != '5eba4712b596a478b034be1809caffbc8f767f47')
    })

@app.route('/search')
def search_endpoint():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Parameter "q" diperlukan'}), 400
    
    if limit > 50:
        limit = 50  # Batasi maksimal 50
    
    try:
        results = search_google(query, num_results=limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'source': 'serper.dev'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'error': str(e),
            'query': query
        }), 500

# ============================================================
# START SERVER
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("🚀 Google Search API with Serper.dev")
    print(f"📡 Port: {port}")
    print(f"🔑 API Key: {'✅' if SERPER_API_KEY else '❌'}")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
