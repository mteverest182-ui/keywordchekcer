# app.py - Update fungsi search_google
def search_google(query, num_results=10):
    """Mencari di Google menggunakan Serper.dev API"""
    
    if not SERPER_API_KEY or SERPER_API_KEY == '5eba4712b596a478b034be1809caffbc8f767f47':
        print("⚠️ API Key Serper.dev belum diisi!")
        return []
    
    url = "https://google.serper.dev/search"
    
    # Serper.dev tidak mendukung parameter 'num' langsung
    # Gunakan 'page' untuk kontrol hasil
    payload = json.dumps({
        "q": query,
        "gl": "id",      # Indonesia
        "hl": "id",      # Bahasa Indonesia
        "autocorrect": True,
        "page": 1        # Halaman 1
    })
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Mencari: {query}")
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return []
        
        data = response.json()
        
        # DEBUG: Tampilkan struktur response
        print(f"📋 Response keys: {list(data.keys())}")
        
        results = []
        
        # ===== CEK BERBAGAI KEMUNGKINAN STRUKTUR =====
        
        # 1. Organic results (yang paling umum)
        if 'organic' in data and data['organic']:
            print(f"✅ Organic results found: {len(data['organic'])}")
            for item in data['organic'][:num_results]:
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', 'No Title'),
                    'snippet': item.get('snippet', '')
                })
        
        # 2. Answer box (jika ada)
        if not results and 'answerBox' in data:
            answer = data['answerBox']
            print("✅ Answer box found")
            results.append({
                'url': data.get('searchParameters', {}).get('q', ''),
                'title': answer.get('title', 'Hasil Pencarian'),
                'snippet': answer.get('snippet', answer.get('answer', ''))
            })
        
        # 3. Knowledge graph (jika ada)
        if not results and 'knowledgeGraph' in data:
            kg = data['knowledgeGraph']
            print("✅ Knowledge graph found")
            results.append({
                'url': kg.get('link', ''),
                'title': kg.get('title', 'Hasil Pencarian'),
                'snippet': kg.get('description', '')
            })
        
        # 4. People also ask (jika ada)
        if not results and 'peopleAlsoAsk' in data:
            print("✅ People also ask found")
            for item in data['peopleAlsoAsk'][:num_results]:
                results.append({
                    'url': '',
                    'title': item.get('question', 'Pertanyaan Terkait'),
                    'snippet': item.get('snippet', '')
                })
        
        # 5. Related searches (jika ada)
        if not results and 'relatedSearches' in data:
            print("✅ Related searches found")
            for item in data['relatedSearches'][:num_results]:
                results.append({
                    'url': '',
                    'title': item.get('query', 'Pencarian Terkait'),
                    'snippet': ''
                })
        
        # Jika tetap kosong, berikan link ke Google langsung
        if not results:
            print("⚠️ Tidak ada hasil, memberikan link ke Google")
            results.append({
                'url': f'https://www.google.com/search?q={query}',
                'title': f'Cari "{query}" di Google',
                'snippet': 'Klik link ini untuk melihat hasil langsung di Google.'
            })
        
        return results
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Server Serper.dev tidak merespon")
        return []
    except Exception as e:
        print(f"❌ Error Serper.dev: {e}")
        import traceback
        traceback.print_exc()
        return []
