from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({'message': 'Hello from Flask!', 'status': 'healthy'})

@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@main_bp.route('/api/info')
def info():
    return jsonify({
        'app': 'Flask Demo App',
        'version': '1.0.0',
        'description': 'A simple Flask app with CI/CD to Azure'
    })
