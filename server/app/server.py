from flask import Flask, jsonify
import logging
import sys
from config import config
from api import vault_bp
from utils.middleware import setup_middleware
from version import get_version

def create_app():
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Disable Flask's default logging to prevent IP logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Register blueprints
    app.register_blueprint(vault_bp)
    
    # Setup middleware
    setup_middleware(app, config)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            "name": "UPass Server",
            "version": get_version(),
            "message": "Zero-knowledge password manager"
        }), 200
    
    return app

def run_server(port=None):
    app = create_app()
    
    # Use provided port or fall back to config
    server_port = port if port is not None else config.PORT
    
    # Print UPass branding banner
    print(f"🔐 UPass Server v{get_version()} - Zero-Knowledge Password Manager")
    print(f"🚀 Starting server on http://127.0.0.1:{server_port}")
    
    # Suppress Flask startup messages by redirecting stdout temporarily
    import os
    import sys
    from contextlib import redirect_stdout
    
    # Redirect stdout to devnull during Flask startup
    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(devnull):
            app.run(
                host='127.0.0.1',  # Bind to localhost only for security
                port=server_port,
                debug=config.DEBUG,
                use_reloader=config.DEBUG
            )

if __name__ == '__main__':
    run_server()