from flask import Blueprint, request, jsonify
from models import Database
from utils import CryptoVerifier
from config import config
import json

vault_bp = Blueprint('vault', __name__)
db = None

def get_db():
    global db
    if db is None:
        db = Database()
    return db

def validate_username(username: str) -> bool:
    if not username or len(username) > config.MAX_USERNAME_LENGTH:
        return False
    return username.isalnum()

def create_error_response(message: str, status_code: int):
    return jsonify({"error": message}), status_code

@vault_bp.route('/vaults/<username>/exists', methods=['GET'])
def check_vault_exists(username):
    """Check if a vault exists for the given username. No authentication required."""
    if not validate_username(username):
        return create_error_response("Invalid username", 400)
    
    try:
        vault = get_db().get_vault(username)
        return jsonify({
            "exists": vault is not None
        }), 200
        
    except Exception as e:
        return create_error_response("Internal server error", 500)

@vault_bp.route('/vaults/<username>/retrieve', methods=['POST'])
def get_vault(username):
    """Retrieve vault contents. Uses POST for authentication data."""
    if not validate_username(username):
        return create_error_response("Invalid username", 400)
    
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid request body", 400)
        
        public_key = data.get('public_key')
        signing_key = data.get('signing_key')
        timestamp = data.get('timestamp')
        signature = data.get('signature')
        
        if not all([public_key, signing_key, timestamp, signature]):
            return create_error_response("Missing required fields", 400)
        
        if not isinstance(timestamp, int):
            return create_error_response("Invalid timestamp", 400)
        
        vault = get_db().get_vault(username)
        if not vault:
            return create_error_response("Vault not found", 404)
        
        if vault['public_key'] != public_key:
            return create_error_response("Unauthorized", 401)
        
        if not CryptoVerifier.verify_vault_get(vault['public_key'], signing_key, signature, timestamp):
            return create_error_response("Invalid signature", 401)
        
        return jsonify({
            "vault_blob": vault['vault_blob']
        }), 200
        
    except Exception as e:
        return create_error_response("Internal server error", 500)

@vault_bp.route('/vaults/<username>', methods=['PUT'])
def put_vault(username):
    if not validate_username(username):
        return create_error_response("Invalid username", 400)
    
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid request body", 400)
        
        public_key = data.get('public_key')
        signing_key = data.get('signing_key')
        timestamp = data.get('timestamp')
        vault_blob = data.get('vault_blob')
        signature = data.get('signature')
        create_if_missing = data.get('create_if_missing', False)
        
        if not all([public_key, signing_key, timestamp, vault_blob, signature]):
            return create_error_response("Missing required fields", 400)
        
        if not isinstance(timestamp, int):
            return create_error_response("Invalid timestamp", 400)
        
        if len(vault_blob) > config.MAX_VAULT_SIZE:
            return create_error_response("Vault too large", 400)
        
        existing_vault = get_db().get_vault(username)
        if existing_vault and existing_vault['public_key'] != public_key:
            return create_error_response("Username already exists", 409)
        
        # Check if vault exists and handle creation logic
        if existing_vault:
            stored_public_key = existing_vault['public_key']
        else:
            # Vault doesn't exist - check if creation is allowed
            if not create_if_missing:
                return create_error_response("Vault does not exist. Use create_if_missing=true to create new vault.", 404)
            stored_public_key = public_key  # For new vault creation
            
        if not CryptoVerifier.verify_vault_put(stored_public_key, signing_key, signature, vault_blob, timestamp):
            return create_error_response("Invalid signature", 401)
        
        success = get_db().upsert_vault(username, public_key, vault_blob)
        if not success:
            return create_error_response("Failed to save vault", 500)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Server error in put_vault: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"Internal server error: {str(e)}", 500)

@vault_bp.route('/vaults/<username>/delete', methods=['POST'])
def delete_vault(username):
    if not validate_username(username):
        return create_error_response("Invalid username", 400)
    
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid request body", 400)
        
        public_key = data.get('public_key')
        signing_key = data.get('signing_key')
        timestamp = data.get('timestamp')
        signature = data.get('signature')
        
        if not all([public_key, signing_key, timestamp, signature]):
            return create_error_response("Missing required fields", 400)
        
        if not isinstance(timestamp, int):
            return create_error_response("Invalid timestamp", 400)
        
        vault = get_db().get_vault(username)
        if not vault:
            return create_error_response("Vault not found", 404)
        
        if vault['public_key'] != public_key:
            return create_error_response("Unauthorized", 401)
        
        if not CryptoVerifier.verify_vault_delete(vault['public_key'], signing_key, signature, timestamp):
            return create_error_response("Invalid signature", 401)
        
        success = get_db().delete_vault(username, public_key)
        if not success:
            return create_error_response("Failed to delete vault", 500)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        return create_error_response("Internal server error", 500)