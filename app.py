import os
import json
import time
import requests
from flask import Flask, request, jsonify
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

# ❌ حذف users.json نهائياً - سيتم استخدام متغير مؤقت أو قاعدة بيانات خارجية
# سنستخدم dict مؤقت (سيتحذف مع كل إعادة تشغيل)
temp_storage = {}

def fetch_token(uid, password):
    url = f"https://jwt-drab.vercel.app/token?uid={uid}&password={password}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "").strip()
            return token
    except Exception as e:
        print(f"Token error: {e}")
    return None

def request_add_friend(player_id, jwt_token):
    if not jwt_token:
        return {"success": False, "error": "No token provided"}
    try:
        encrypted_id = Encrypt_ID(str(player_id))
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        payload_bytes = bytes.fromhex(encrypt_api(payload))
        
        url = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB53",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(payload_bytes)),
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
            "Connection": "close",
        }
        
        response = requests.post(url, headers=headers, data=payload_bytes, timeout=15)
        if response.status_code == 200:
            return {"success": True, "status_code": response.status_code}
        return {"success": False, "error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def remove_friend(player_id, jwt_token):
    if not jwt_token:
        return {"success": False, "error": "No token provided"}
    try:
        encrypted_id = Encrypt_ID(str(player_id))
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        payload_bytes = bytes.fromhex(encrypt_api(payload))
        
        url = "https://clientbp.ggpolarbear.com/RemoveFriend"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB53",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(payload_bytes)),
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
            "Connection": "close",
        }
        
        response = requests.post(url, headers=headers, data=payload_bytes, timeout=15)
        if response.status_code == 200:
            return {"success": True, "status_code": response.status_code}
        return {"success": False, "error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/add', methods=['GET'])
def add_friend():
    uid = request.args.get('uid')
    password = request.args.get('pass')
    target_id = request.args.get('id')
    
    if not uid or not password or not target_id:
        return jsonify({
            "success": False,
            "error": "Missing parameters. Required: uid, pass, id"
        }), 400
    
    jwt_token = fetch_token(uid, password)
    if not jwt_token:
        return jsonify({
            "success": False,
            "error": "Failed to get authentication token."
        }), 401
    
    result = request_add_friend(target_id, jwt_token)
    
    if result["success"]:
        # تخزين مؤقت بدلاً من ملف
        temp_storage[f"{uid}_{target_id}"] = time.time()
        return jsonify({
            "success": True,
            "message": "Friend request sent successfully",
            "data": {
                "added_by": uid,
                "target_id": target_id,
                "status": "pending_acceptance"
            }
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error"),
        }), 500

@app.route('/remove', methods=['GET'])
def remove_friend_endpoint():
    uid = request.args.get('uid')
    password = request.args.get('pass')
    target_id = request.args.get('id')
    
    if not uid or not password or not target_id:
        return jsonify({
            "success": False,
            "error": "Missing parameters."
        }), 400
    
    jwt_token = fetch_token(uid, password)
    if not jwt_token:
        return jsonify({
            "success": False,
            "error": "Failed to get authentication token."
        }), 401
    
    result = remove_friend(target_id, jwt_token)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "message": f"Friend {target_id} removed successfully",
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Unknown error"),
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Friend Management API",
        "timestamp": time.time()
    }), 200

# ✅ هذا هو الـ Handler الخاص بـ Vercel
def handler(event, context):
    return app(event, context)

# هذا السطر لن يتم استخدامه في Vercel
if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000)
