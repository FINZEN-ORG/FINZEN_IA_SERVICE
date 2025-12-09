import sys
import json
from financial_agent.db import query_episodic_by_user


def main():
    if len(sys.argv) < 2:
        print("Usage: python list_episodes.py <user_id> [limit]")
        sys.exit(1)
    user_id = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    rows = query_episodic_by_user(user_id, limit=limit)
    print(json.dumps(rows, default=str, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
