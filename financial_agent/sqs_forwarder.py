import sys
import os
import json
import time
import traceback
from typing import Dict, Any

try:
    import boto3
    from botocore.config import Config
except Exception:
    print("Missing required package 'boto3' or 'botocore'.\nInstall with: 'pip install boto3' or 'pip install -r requirements.txt'")
    sys.exit(1)

from .agent import handle_message
from .utils.logging import get_logger

logger = get_logger("financial_sqs")

SQS_FINANCIAL_INSIGHT_QUEUE_URL = os.environ.get("SQS_FINANCIAL_INSIGHT_QUEUE_URL")
SQS_ORCHESTRATOR_CALLBACK_QUEUE = os.environ.get("SQS_ORCHESTRATOR_CALLBACK_QUEUE") or os.environ.get("SQS_ORCHESTRATOR_QUEUE_URL")


def get_sqs_client():
    region = os.environ.get("AWS_REGION")
    session = boto3.Session()
    config = Config(region_name=region) if region else None
    return session.client("sqs", config=config) if config else session.client("sqs")


def is_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def forward_messages():
    sqs = get_sqs_client()
    queue_url = SQS_FINANCIAL_INSIGHT_QUEUE_URL

    if not queue_url:
        raise RuntimeError("SQS_FINANCIAL_INSIGHT_QUEUE_URL is not set in environment")

    print(f"Listening on financial insight queue: {queue_url}")
    if SQS_ORCHESTRATOR_CALLBACK_QUEUE:
        print(f"Forwarding to orchestrator callback queue: {SQS_ORCHESTRATOR_CALLBACK_QUEUE}")
    else:
        print("No SQS_ORCHESTRATOR_CALLBACK_QUEUE configured — will not forward to orchestrator.")

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )

            messages = resp.get("Messages", [])
            if not messages:
                continue

            for msg in messages:
                receipt_handle = msg.get("ReceiptHandle")
                body = msg.get("Body", "")
                msg_attrs = msg.get("MessageAttributes") or {}

                if not is_json(body):
                    print("Skipping non-JSON message, deleting to avoid reprocessing.")
                    try:
                        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                    except Exception:
                        print("Failed to delete non-JSON message:")
                        traceback.print_exc()
                    continue

                payload = json.loads(body)

                # Determine reply_url if provided in message attributes
                reply_url = None
                try:
                    ra = msg_attrs.get("reply_queue_url") or msg_attrs.get("reply_url")
                    if ra and isinstance(ra, dict):
                        reply_url = ra.get("StringValue") or ra.get("String")
                    elif isinstance(ra, str):
                        reply_url = ra
                except Exception:
                    reply_url = None

                forwarded = False

                # If an orchestrator callback queue is configured, call the agent and send result there
                if SQS_ORCHESTRATOR_CALLBACK_QUEUE:
                    try:
                        try:
                            result = handle_message(payload)
                        except Exception as e:
                            print("Agent handler raised exception while processing payload:")
                            traceback.print_exc()
                            result = {"status": "error", "error": str(e)}

                        orchestrator_result_body = {
                            "source": "financial_insight_queue",
                            "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "result": result,
                            "original_payload": payload,
                        }

                        sqs.send_message(
                            QueueUrl=SQS_ORCHESTRATOR_CALLBACK_QUEUE,
                            MessageBody=json.dumps(orchestrator_result_body),
                        )
                        forwarded = True
                        print("Sent agent result to orchestrator callback queue for message id:", msg.get("MessageId"))
                    except Exception:
                        print("Failed to send agent result to orchestrator callback queue:")
                        traceback.print_exc()

                # If reply_url provided, send result back there
                if reply_url:
                    try:
                        try:
                            result = handle_message(payload)
                        except Exception as e:
                            print("Agent handler raised an exception:")
                            traceback.print_exc()
                            result = {"status": "error", "error": str(e)}

                        sqs.send_message(
                            QueueUrl=reply_url,
                            MessageBody=json.dumps({"status": "ok", "result": result}),
                        )
                        print("Sent IA result to requester queue:", reply_url)
                    except Exception:
                        print("Failed to send IA result to requester queue:")
                        traceback.print_exc()

                    try:
                        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                        print("Deleted original message id:", msg.get("MessageId"))
                    except Exception:
                        print("Failed to delete message after replying:")
                        traceback.print_exc()
                else:
                    if forwarded:
                        try:
                            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                            print("Deleted original message id:", msg.get("MessageId"))
                        except Exception:
                            print("Failed to delete message after forwarding:")
                            traceback.print_exc()
                    else:
                        # delete to avoid reprocessing
                        try:
                            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                        except Exception:
                            print("Failed to delete message:")
                            traceback.print_exc()

        except KeyboardInterrupt:
            print("Interrupted by user, exiting")
            return
        except Exception:
            print("Unexpected error in forward loop:")
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    forward_messages()
