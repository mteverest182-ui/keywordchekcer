# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

app = Flask(__name__)
CORS(app)  # Izinkan akses dari semua origin

# ============================================================
# GOOGLE SEARCH FALLBACK (TANPA GOOGLESEARCH-PYTHON)
# ============================================================
def search_google_fallback(query, num_results=10):
    """Fallback sederhana jika googlesearch-python tidak tersedia"""
    results = []
    try:
        # Coba import googlesearch
        from googlesearch import search
        
        for url in search(query, num_results=num_results):
            results.append({
                'url': url,
                'title': f"Hasil dari Google",
                'snippet': f"Hasil pencarian untuk '{query}'"
            })
        return results
    except ImportError:
        print("⚠️ googlesearch-python tidak terinstall")
        return []
    except Exception as e:
        print(f"❌ Error di googlesearch: {e}")
        return []

# ============================================================
# ROUTES
# ============================================================
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

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Google Search API running',
        'python_version': sys.version,
        'cors_enabled': True
    })

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'Parameter "q" diperlukan'}), 400
    
    try:
        print(f"🔍 Mencari: {query}")
        results = search_google_fallback(query, num_results=limit)
        
        # Jika results kosong, berikan data dummy untuk testing
        if not results:
            print("⚠️ Tidak ada hasil, memberikan data dummy")
            results = [
                {
                    'url': f'https://www.google.com/search?q={query}',
                    'title': f'Hasil pencarian untuk "{query}"',
                    'snippet': 'Coba buka Google untuk melihat hasil lebih lengkap.'
                },
                {
                    'url': 'https://id.wikipedia.org',
                    'title': 'Wikipedia - Ensiklopedia Bebas',
                    'snippet': 'Sumber referensi untuk berbagai topik.'
                }
            ]
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'source': 'google-search-fallback'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'error': str(e),
            'query': query
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
    print("🚀 Google Search API berjalan")
    print(f"📡 Port: {port}")
    print(f"🔍 CORS: Enabled")
    print("="*50)
    app.run(host='0.0.0.0', port=port, debug=False)
