import requests

API_URL = "http://10.6.20.153:8000"
OPENAPI_URL = f"{API_URL}/openapi.json"
TEST_USER = {
    "username": "Kaval123",  # <- değiştir!
    "password": "LNnc0jnflnD2"          # <- değiştir!
}

# 1. Token al
def get_token():
    data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{API_URL}/auth/token", data=data, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Token alınamadı!", response.text)
        return None

# 2. Swagger endpointlerini çek
def get_openapi():
    resp = requests.get(OPENAPI_URL)
    return resp.json()

# 3. Endpointlere test isteği at
def test_endpoints(token, openapi_json):
    headers = {"Authorization": f"Bearer {token}"}
    for path, path_item in openapi_json["paths"].items():
        for method, details in path_item.items():
            url = API_URL + path.replace("{", "1").replace("}", "")  # path paramlarına örnek 1 yaz
            m = method.upper()
            print(f"\n==> {m} {url}")

            if method == "get":
                r = requests.get(url, headers=headers)
            elif method == "post":
                # Gövdede JSON isteği gerekiyorsa basit bir dummy veri gönder
                json_body = {}
                if details.get("requestBody") and "application/json" in details["requestBody"]["content"]:
                    # Hangi schema gerekiyor, basit boş obje/dummy ile doldur
                    schema = list(details["requestBody"]["content"].keys())[0]
                    if "UserCreate" in str(details["requestBody"]["content"]):
                        json_body = {
                            "username": "test_user", "first_name": "Test", "last_name": "User",
                            "email": "test@example.com", "password": "123456"
                        }
                    elif "PromptCreate" in str(details["requestBody"]["content"]):
                        json_body = {"content": "test prompt", "is_public": True}
                    else:
                        json_body = {}
                r = requests.post(url, headers=headers, json=json_body)
            elif method == "put":
                r = requests.put(url, headers=headers, json={})
            elif method == "delete":
                r = requests.delete(url, headers=headers)
            else:
                continue

            print("Status:", r.status_code, "| Body:", r.text[:200])

# Çalıştır
if __name__ == "__main__":
    openapi = get_openapi()
    token = get_token()
    if token:
        test_endpoints(token, openapi)