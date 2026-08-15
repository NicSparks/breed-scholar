import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)
BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'
THUMBS_DIR = BASE_DIR / 'static' / 'thumbs'
FULL_DIR = BASE_DIR / 'static' / 'full'
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
FULL_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/breeds/all')
def all_breeds():
    db = get_db()
    cursor = db.execute('''
        SELECT b.id, b.name, b.group_name, b.rank, b.country, b.size,
               b.fci_group, b.fact, b.tips, b.image_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM breeds b
        LEFT JOIN breed_registries br ON b.id = br.breed_id
        LEFT JOIN registries r ON br.registry_id = r.id
        GROUP BY b.id
        ORDER BY b.name ASC
    ''')
    breeds = [dict(row) for row in cursor.fetchall()]
    db.close()
    return jsonify({'breeds': breeds, 'total': len(breeds)})


@app.route('/api/breeds')
def list_breeds():
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '').strip().lower()
    registry = request.args.get('registry', '').lower()
    group = request.args.get('group', '').strip().lower()

    base_where = 'WHERE 1=1'
    base_params = []

    if search:
        base_where += ' AND LOWER(b.name) LIKE ?'
        base_params.append(f'%{search}%')

    if registry:
        base_where += ' AND r.code = ?'
        base_params.append(registry)

    if group:
        base_where += ' AND LOWER(b.group_name) LIKE ?'
        base_params.append(f'%{group}%')

    query = f'''
        SELECT b.id, b.name, b.group_name, b.rank, b.country, b.size,
               b.fci_group, b.fact, b.tips, b.image_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM breeds b
        LEFT JOIN breed_registries br ON b.id = br.breed_id
        LEFT JOIN registries r ON br.registry_id = r.id
        {base_where}
        GROUP BY b.id
        ORDER BY b.name ASC
        LIMIT ? OFFSET ?
    '''
    offset = (page - 1) * per_page
    cursor = db.execute(query, base_params + [per_page, offset])
    breeds = [dict(row) for row in cursor.fetchall()]

    count_query = f'SELECT COUNT(DISTINCT b.id) FROM breeds b LEFT JOIN breed_registries br ON b.id = br.breed_id LEFT JOIN registries r ON br.registry_id = r.id {base_where}'
    total = db.execute(count_query, base_params).fetchone()[0]

    db.close()

    return jsonify({
        'breeds': breeds,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/breeds/<int:breed_id>')
def get_breed(breed_id):
    db = get_db()
    cursor = db.execute('''
        SELECT b.id, b.name, b.group_name, b.rank, b.country, b.size,
               b.fci_group, b.fact, b.tips, b.image_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM breeds b
        LEFT JOIN breed_registries br ON b.id = br.breed_id
        LEFT JOIN registries r ON br.registry_id = r.id
        WHERE b.id = ?
        GROUP BY b.id
    ''', (breed_id,))
    breed = cursor.fetchone()
    db.close()

    if breed:
        return jsonify(dict(breed))
    return jsonify({'error': 'Breed not found'}), 404


@app.route('/api/stats')
def get_stats():
    db = get_db()

    total = db.execute('SELECT COUNT(*) FROM breeds').fetchone()[0]
    akc = db.execute('''
        SELECT COUNT(DISTINCT b.id) FROM breeds b
        JOIN breed_registries br ON b.id = br.breed_id
        JOIN registries r ON br.registry_id = r.id WHERE r.code = 'akc'
    ''').fetchone()[0]
    fci = db.execute('''
        SELECT COUNT(DISTINCT b.id) FROM breeds b
        JOIN breed_registries br ON b.id = br.breed_id
        JOIN registries r ON br.registry_id = r.id WHERE r.code = 'fci'
    ''').fetchone()[0]
    non = db.execute('''
        SELECT COUNT(DISTINCT b.id) FROM breeds b
        JOIN breed_registries br ON b.id = br.breed_id
        JOIN registries r ON br.registry_id = r.id WHERE r.code = 'non'
    ''').fetchone()[0]

    top_breeds = db.execute('''
        SELECT b.name, b.rank FROM breeds b
        WHERE b.rank IS NOT NULL
        ORDER BY b.rank ASC
        LIMIT 10
    ''').fetchall()

    db.close()

    return jsonify({
        'total': total,
        'akc': akc,
        'fci': fci,
        'non': non,
        'top_breeds': [dict(row) for row in top_breeds]
    })


@app.route('/api/rebuild', methods=['POST'])
def rebuild_database():
    import subprocess
    try:
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'rebuild_database.py')],
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Rebuild timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/static/thumbs/<filename>')
def serve_thumb(filename):
    thumb_path = THUMBS_DIR / filename
    if thumb_path.exists():
        return send_file(str(thumb_path), mimetype='image/jpeg')
    placeholder = BASE_DIR / 'static' / 'placeholder.jpg'
    if placeholder.exists():
        return send_file(str(placeholder), mimetype='image/jpeg')
    return jsonify({'error': 'Not found'}), 404


@app.route('/static/full/<filename>')
def serve_full(filename):
    full_path = FULL_DIR / filename
    if full_path.exists():
        return send_file(str(full_path))
    return jsonify({'error': 'Image not cached'}), 404


@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Breed Scholar",
        "short_name": "BreedScholar",
        "description": "Learn every dog breed with photos, flashcards, and quizzes",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0a0f",
        "theme_color": "#f1c40f",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
