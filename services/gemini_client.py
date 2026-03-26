import os, time, json, urllib.request, urllib.error
from config import key_pool, GEMINI_MODEL

def call_gemini(prompt, max_retries=3):
    if key_pool is None:
        raise Exception("API Key 未配置")
    retries = min(max_retries, key_pool.total)
    last_error = None
    for attempt in range(retries):
        api_key = key_pool.next_key()
        print("[调试] Gemini 第 %d 次, 模型: %s" % (attempt+1, GEMINI_MODEL))
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (GEMINI_MODEL, api_key)
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                print("[调试] 成功, 长度: %d" % len(result))
                print("[调试] 前500字: %s" % result[:500])
                return result
        except urllib.error.HTTPError as e:
            eb = e.read().decode("utf-8", errors="replace")
            last_error = "HTTP %d" % e.code
            print("[错误] HTTP %d: %s" % (e.code, eb[:300]))
            if e.code == 429:
                key_pool.mark_failed(api_key)
                time.sleep(3)
            elif e.code in (401, 403):
                key_pool.mark_failed(api_key)
            else:
                time.sleep(2)
        except Exception as e:
            last_error = str(e)
            print("[错误] %s" % e)
            time.sleep(2)
    raise Exception("API 调用失败: %s" % last_error)
