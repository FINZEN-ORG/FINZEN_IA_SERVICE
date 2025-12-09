
import sys
import os
import json
import time
import traceback
from typing import Dict, Any

# Check for optional AWS dependency and provide a clear error if missing
try:
    import boto3
    from botocore.config import Config
except Exception:
    print("Missing required package 'boto3' or 'botocore'.")
    print("Install with: 'pip install boto3' or 'pip install -r requirements.txt'")
    sys.exit(1)

# Import the local agent handler to produce IA results
try:
    from goal_agent.agent import handle as agent_handle
except Exception:
    # Fallback to relative import if running in-package
    try:
        from .agent import handle as agent_handle
    except Exception:
        agent_handle = None

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
    goals_queue = os.environ.get("SQS_GOALS_QUEUE_URL")
    # Prefer the callback-specific env var if provided, fall back to older name for compatibility
    orchestrator_queue = os.environ.get("SQS_ORCHESTRATOR_CALLBACK_QUEUE") or os.environ.get("SQS_ORCHESTRATOR_QUEUE_URL")

    if not goals_queue:
        raise RuntimeError("SQS_GOALS_QUEUE_URL is not set in environment")

    print(f"Listening only on goals queue: {goals_queue}")
    if orchestrator_queue:
        print(f"Forwarding to orchestrator queue: {orchestrator_queue}")
    else:
        print("No SQS_ORCHESTRATOR_QUEUE_URL configured — will not forward to orchestrator.\n" \
              "If incoming messages include MessageAttributes.reply_queue_url, a response will be sent there.")

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl=goals_queue,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # long poll
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )

            messages = resp.get("Messages", [])
            if not messages:
                # no messages, continue polling
                continue

            for msg in messages:
                receipt_handle = msg.get("ReceiptHandle")
                body = msg.get("Body", "")
                msg_attrs = msg.get("MessageAttributes") or {}

                # Validate JSON body
                if not is_json(body):
                    print("Skipping non-JSON message, deleting to avoid reprocessing.")
                    # Option: move to DLQ instead of delete in production
                    try:
                        sqs.delete_message(QueueUrl=goals_queue, ReceiptHandle=receipt_handle)
                    except Exception:
                        print("Failed to delete non-JSON message:")
                        traceback.print_exc()
                    continue

                payload = json.loads(body)

                # Optionally add metadata about source
                forward_body = {
                    "source": "goals_queue",
                    "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "payload": payload,
                }

                # Prepare message attributes to forward
                send_attrs: Dict[str, Any] = {}
                for k, v in (msg_attrs or {}).items():
                    # boto3 expects specific structure for MessageAttributes
                    try:
                        send_attrs[k] = {
                            "DataType": v.get("DataType", "String"),
                            "StringValue": v.get("StringValue"),
                            "BinaryValue": v.get("BinaryValue"),
                        }
                    except Exception:
                        # ignore malformed attributes
                        continue

                # Determine reply_url if provided in message attributes
                reply_url = None
                try:
                    if isinstance(msg_attrs, dict):
                        ra = msg_attrs.get("reply_queue_url") or msg_attrs.get("reply_url")
                        if ra and isinstance(ra, dict):
                            # Standard SQS MessageAttribute structure uses 'StringValue'
                            reply_url = ra.get("StringValue") or ra.get("String")
                        elif isinstance(ra, str):
                            reply_url = ra
                except Exception:
                    # ignore parsing errors and leave reply_url as None
                    reply_url = None

                # If an orchestrator callback queue is configured, call the local agent
                # to produce the result and send that result to the orchestrator callback queue.
                forwarded = False
                orchestrator_result_body = None
                if orchestrator_queue:
                    try:
                        if agent_handle is None:
                            # Agent handler not available; send an error payload instead
                            orchestrator_result_body = {
                                "source": "goals_queue",
                                "received_at": forward_body["received_at"],
                                "error": "agent handler not available",
                                "original_payload": payload,
                            }
                        else:
                            # Run the agent synchronously to get the processed result
                            try:
                                agent_result = agent_handle(payload)
                            except Exception as e:
                                print("Agent handler raised exception while processing payload:")
                                traceback.print_exc()
                                agent_result = {"status": "error", "error": str(e)}

                            orchestrator_result_body = {
                                "source": "goals_queue",
                                "received_at": forward_body["received_at"],
                                "result": agent_result,
                                "original_payload": payload,
                            }

                        # Send the agent result to the orchestrator callback queue
                        sqs.send_message(
                            QueueUrl=orchestrator_queue,
                            MessageBody=json.dumps(orchestrator_result_body),
                            MessageAttributes=send_attrs or {},
                        )
                        forwarded = True
                        print("Sent agent result to orchestrator callback queue for message id:", msg.get("MessageId"))
                    except Exception:
                        print("Failed to send agent result to orchestrator callback queue:")
                        traceback.print_exc()

                # If a reply queue URL was provided by the requester, run the local agent to produce the IA result and send it back
                if reply_url:
                    if agent_handle is None:
                        # Agent not importable; send an error response
                        try:
                            sqs.send_message(
                                QueueUrl=reply_url,
                                MessageBody=json.dumps({
                                    "status": "error",
                                    "error": "agent handler not available on worker",
                                }),
                            )
                        except Exception:
                            print("Failed to send error reply to requester queue:")
                            traceback.print_exc()
                    else:
                        try:
                            # Call the agent synchronously with the payload
                            result = agent_handle(payload)
                        except Exception as e:
                            print("Agent handler raised an exception:")
                            traceback.print_exc()
                            result = {"status": "error", "error": str(e)}

                        # Send the IA result back to the requester
                        try:
                            sqs.send_message(
                                QueueUrl=reply_url,
                                MessageBody=json.dumps({"status": "ok", "result": result}),
                            )
                            print("Sent IA result to requester queue:", reply_url)
                        except Exception:
                            print("Failed to send IA result to requester queue:")
                            traceback.print_exc()

                    # Delete original message after replying
                    try:
                        sqs.delete_message(QueueUrl=goals_queue, ReceiptHandle=receipt_handle)
                        print("Deleted original message id:", msg.get("MessageId"))
                    except Exception:
                        print("Failed to delete message after replying:")
                        traceback.print_exc()
                else:
                    # No reply_url provided. If we forwarded to orchestrator we already handled deletion.
                    if forwarded:
                        try:
                            sqs.delete_message(QueueUrl=goals_queue, ReceiptHandle=receipt_handle)
                            print("Deleted original message id:", msg.get("MessageId"))
                        except Exception:
                            print("Failed to delete message after forwarding:")
                            traceback.print_exc()
                    else:
                        # Nothing to do: delete to avoid endless reprocessing or optionally move to DLQ
                        print("No reply_url and no orchestrator configured; deleting message to avoid reprocessing.")
                        try:
                            sqs.delete_message(QueueUrl=goals_queue, ReceiptHandle=receipt_handle)
                        except Exception:
                            print("Failed to delete message:")
                            traceback.print_exc()

        except KeyboardInterrupt:
            print("Interrupted by user, exiting")
            return
        except Exception:
            print("Unexpected error in forward loop:")
            traceback.print_exc()
            # Small backoff to avoid tight error loop
            time.sleep(5)


if __name__ == "__main__":
    forward_messages()
