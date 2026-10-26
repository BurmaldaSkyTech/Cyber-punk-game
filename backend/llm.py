# backend/llm.py
import json, requests

CHAT_URL = "http://localhost:11434/api/chat"
GEN_URL  = "http://localhost:11434/api/generate"


def _fmt_chat_payload(messages, model, temperature):
    return {"model": model, "messages": messages, "stream": False,
            "format": "json", "options": {"temperature": temperature,
                                           "num_ctx": 8192, "repeat_penalty": 1.15}}


def _fmt_generate_payload(messages, model, temperature):
    system, user = "", ""
    for m in messages:
        if m["role"] == "system":
            system += m["content"] + "\n"
        elif m["role"] == "user":
            user = m["content"]
    prompt = f"{system}\nUSER:\n{user}\nASSISTANT:\n"
    return {"model": model, "prompt": prompt, "stream": False, "format": "json",
            "options": {"temperature": temperature, "num_ctx": 8192, "repeat_penalty": 1.15}}


def _strip(txt):
    txt = (txt or "").strip()
    if txt.startswith("```"):
        first_nl = txt.find("\n")
        if first_nl > 0:
            txt = txt[first_nl:]
        if txt.endswith("```"):
            txt = txt[:-3]
    return txt.strip()


def _call(url, payload, timeout=300):
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if "message" in data:
        return data["message"].get("content", "")
    return data.get("response", "")


def chat_json(messages, model="qwen2.5:7b-instruct", temperature=0.7, retries=2):
    last = None
    for _ in range(retries + 1):
        try:
            try:
                txt = _call(CHAT_URL, _fmt_chat_payload(messages, model, temperature))
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code in (404, 405):
                    txt = _call(GEN_URL, _fmt_generate_payload(messages, model, temperature))
                else:
                    raise
            return json.loads(_strip(txt))
        except Exception as e:
            last = e
    raise ValueError(f"LLM JSON failed: {last}")