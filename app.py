# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from googlesearch import search

app = Flask(__name__)
CORS(app)

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
        print(f"🔍 Mencari: {query}")
        
        results = []
        for url in search(query, num_results=limit):
            results.append({
                'url': url,
                'title': f"Hasil dari Google",
                'snippet': f"Hasil pencarian untuk '{query}'"
            })
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results),
            'source': 'googlesearch-python'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Google Search API running',
        'source': 'googlesearch-python'
    })

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
# START SERVER
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Google Search API berjalan di port {port}")
    print(f"🔍 Menggunakan googlesearch-python")
    app.run(host='0.0.0.0', port=port, debug=False)
