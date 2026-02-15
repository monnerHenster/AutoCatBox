#!/usr/bin/env python3
"""
涂鸦消息订阅：code=excretion_time_day 时触发追觅划区清扫。
带简单 Web 调试页：可手动点击按钮测试启动追觅。
"""
import json
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pulsar
import requests

from config import (
    ACCESS_ID,
    ACCESS_KEY,
    HA_BASE_URL,
    HA_TOKEN,
    MQ_ENV,
    PULSAR_SERVER_URL,
    SUBSCRIPTION_NAME,
    VACUUM_ENTITY_ID,
    VACUUM_SEGMENTS,
)
from message_util import decrypt_message, message_id
from mq_authentication import get_authentication

TRIGGER_CODE = "excretion_time_day"
DEBUG_PORT = 8099
shutdown = False


def _on_signal(_sig, _frame):
    global shutdown
    shutdown = True


def _has_trigger_code(obj: dict) -> bool:
    biz_data = obj.get("bizData") or {}
    for p in biz_data.get("properties") or []:
        if p.get("code") == TRIGGER_CODE:
            return True
    for s in obj.get("status") or []:
        if s.get("code") == TRIGGER_CODE:
            return True
    return False


def call_dreame_vacuum():
    """调用 HA 追觅划区清扫。返回 (成功与否, 说明文字)。"""
    if not HA_BASE_URL or not HA_TOKEN:
        msg = f"[触发] 未配置 HA_BASE_URL/HA_TOKEN，跳过调用追觅"
        print(msg)
        return False, msg
    url = f"{HA_BASE_URL}/api/services/dreame_vacuum/vacuum_clean_segment"
    payload = {"entity_id": VACUUM_ENTITY_ID, "segments": VACUUM_SEGMENTS}
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        msg = f"[触发] 已调用追觅划区清扫: {VACUUM_ENTITY_ID} segments={VACUUM_SEGMENTS}"
        print(msg)
        return True, msg
    except requests.RequestException as e:
        msg = f"[触发] 调用 HA 失败: {e}"
        print(msg, file=sys.stderr)
        return False, str(e)


class DebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DEBUG_HTML.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/trigger":
            ok, msg = call_dreame_vacuum()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": ok, "message": msg}, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


DEBUG_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>追觅涂鸦触发 - 调试</title>
<style>body{font-family:sans-serif;max-width:360px;margin:2em auto;padding:1em;background:#1c1c1e;color:#eee;}
h1{font-size:1.1em;color:#0a84ff;} button{width:100%;padding:12px;font-size:16px;background:#0a84ff;color:#fff;border:none;border-radius:8px;cursor:pointer;}
button:hover{background:#409cff;} button:disabled{opacity:0.6;cursor:not-allowed;} #result{margin-top:1em;padding:0.8em;border-radius:8px;font-size:14px;white-space:pre-wrap;}
#result.ok{background:#2d4a2d;color:#8ae08a;} #result.err{background:#4a2d2d;color:#e08a8a;}
</style></head><body>
<h1>追觅涂鸦触发</h1>
<p>手动测试调用追觅划区清扫（与 excretion_time_day 触发逻辑一致）。</p>
<button id="btn">测试启动追觅</button>
<div id="result"></div>
<script>
var btn=document.getElementById('btn'), result=document.getElementById('result');
btn.onclick=function(){
  btn.disabled=true; result.textContent='请求中…'; result.className='';
  fetch('/trigger',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
    result.textContent=(d.ok?'成功: ':'失败: ')+d.message; result.className=d.ok?'ok':'err';
  }).catch(function(e){ result.textContent='请求失败: '+e; result.className='err'; })
  .finally(function(){ btn.disabled=false; });
};
</script></body></html>
"""


def handle_message(pulsar_message, decrypt_msg: str, msg_id: str) -> None:
    print(f"[msg_id={msg_id}] 解密内容:")
    try:
        obj = json.loads(decrypt_msg)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        if _has_trigger_code(obj):
            print(f"[触发] 检测到 code={TRIGGER_CODE}，执行追觅联动")
            call_dreame_vacuum()
    except json.JSONDecodeError:
        print(decrypt_msg)


def _run_debug_server():
    server = HTTPServer(("0.0.0.0", DEBUG_PORT), DebugHandler)
    server.serve_forever()


def main() -> int:
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    if not ACCESS_ID or not ACCESS_KEY:
        print("错误: 未配置 tuya_access_id / tuya_access_key", file=sys.stderr)
        return 1

    # 启动调试 Web 页（端口 8099），可手动点击按钮测试追觅
    debug_thread = threading.Thread(target=_run_debug_server, daemon=True)
    debug_thread.start()
    print(f"调试页: http://<本机IP>:{DEBUG_PORT}/  （可点击「测试启动追觅」验证 HA 调用）")

    topic = f"{ACCESS_ID}/out/{MQ_ENV}"
    print(f"连接 Pulsar: {PULSAR_SERVER_URL}")
    print(f"Topic: {topic}, 订阅: {SUBSCRIPTION_NAME}")
    print("等待消息（code=excretion_time_day 时触发追觅）...\n")

    client = pulsar.Client(
        PULSAR_SERVER_URL,
        authentication=get_authentication(ACCESS_ID, ACCESS_KEY),
        tls_allow_insecure_connection=True,
    )
    consumer = client.subscribe(
        topic, SUBSCRIPTION_NAME, consumer_type=pulsar.ConsumerType.Failover
    )

    try:
        while not shutdown:
            try:
                pulsar_message = consumer.receive(timeout_millis=3000)
            except Exception as e:
                if "Timeout" in str(type(e).__name__) or "timeout" in str(e).lower():
                    continue
                raise
            msg_id = message_id(pulsar_message.message_id())
            print(f"--- 收到 message_id: {msg_id}")
            try:
                decrypted = decrypt_message(pulsar_message, ACCESS_KEY)
                print(f"解密: {decrypted[:200]}{'...' if len(decrypted) > 200 else ''}")
                handle_message(pulsar_message, decrypted, msg_id)
            except Exception as e:
                print(f"解密/处理失败: {e}", file=sys.stderr)
            consumer.acknowledge_cumulative(pulsar_message)
    except pulsar.Interrupted:
        print("接收已中断")
    finally:
        consumer.close()
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
