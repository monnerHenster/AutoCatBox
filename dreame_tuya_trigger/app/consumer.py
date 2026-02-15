#!/usr/bin/env python3
"""
涂鸦消息订阅：code=excretion_time_day 时触发追觅划区清扫。
"""
import json
import signal
import sys

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


def call_dreame_vacuum() -> None:
    if not HA_BASE_URL or not HA_TOKEN:
        print(f"[触发] 检测到 {TRIGGER_CODE}，未配置 HA，跳过调用追觅")
        return
    url = f"{HA_BASE_URL}/api/services/dreame_vacuum/vacuum_clean_segment"
    payload = {"entity_id": VACUUM_ENTITY_ID, "segments": VACUUM_SEGMENTS}
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"[触发] 已调用追觅划区清扫: {VACUUM_ENTITY_ID} segments={VACUUM_SEGMENTS}")
    except requests.RequestException as e:
        print(f"[触发] 调用 HA 失败: {e}", file=sys.stderr)


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


def main() -> int:
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    if not ACCESS_ID or not ACCESS_KEY:
        print("错误: 未配置 tuya_access_id / tuya_access_key", file=sys.stderr)
        return 1

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
