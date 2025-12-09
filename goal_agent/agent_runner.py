
import argparse
import json
from .crew import create_agent
from .utils.logging import get_logger

logger = get_logger("agent_runner")


EXAMPLES = {
  "discover_goals": {
    "action": "DISCOVER_GOALS",
    "user_id": "123",

    "semantic_memory": {
      "motivation_profile": {
        "preferred_tone": "encouragement_challenge"
      },
      "spending_habits": [
        "daily small expenses",
        "higher weekend discretionary spending"
      ],
      "risk_attitude": "moderate"
    },

    "financial_context": {
      "income": {
        "monthly_average": 2500000,
        "stability": "stable"
      },
      "expenses": {
        "fixed_monthly": 1800000,
        "variable_monthly_avg": 400000
      },
      "surplus": {
        "monthly": 300000,
        "trend": "stable"
      },
      "savings": {
        "current_balance": 420000,
        "savings_rate": 0.12
      }
    },

    "analysis_context": {
      "ants": [
        {
          "category": "entertainment",
          "monthly_estimated_loss": 120000,
          "pattern": "frequent small outings"
        }
      ],
      "repetitive": [],
      "health": {
        "score": 72,
        "status": "healthy"
      },
      "leaks": []
    },

    "transactions": [
      {
        "id": "6009",
        "date": "2025-11-20",
        "type": "expense",
        "amount": 90000,
        "category": "entertainment",
        "description": "Cine + Crispetas"
      }
    ],

    "existing_goals": [
      {
        "id": "8000",
        "name": "Viaje Cartagena",
        "saved_amount": 420000,
        "target_amount": 1200000,
        "due_date": "2025-06-20"
      },
      {
        "id": "8001",
        "name": "Fondo de Emergencia",
        "saved_amount": 350000,
        "target_amount": 2000000,
        "due_date": "2025-12-30"
      }
    ]
  },

  "evaluate_goal": {
    "action": "EVALUATE_GOAL",
    "user_id": "123",

    "new_goal_proposal": {
      "name": "Comprar Laptop",
      "target_amount": 1500000,
      "due_date": "2026-06-01",
      "priority": "medium",
      "category": "education_work"
    },

    "financial_context": {
      "income": {
        "monthly_average": 2500000
      },
      "surplus": {
        "monthly": 200000
      }
    },

    "analysis_context": {
      "health": {
        "score": 70,
        "status": "healthy"
      }
    },

    "semantic_memory": {
      "motivation_profile": {
        "preferred_tone": "encouragement_challenge"
      }
    },

    "existing_goals": [
      {
        "id": "8001",
        "name": "Fondo de Emergencia",
        "saved_amount": 350000,
        "target_amount": 2000000,
        "priority": "high"
      }
    ]
  },

  "adjust_goals": {
    "action": "ADJUST_GOALS",
    "user_id": "123",

    "financial_context": {
      "surplus": {
        "monthly": 300000
      }
    },

    "analysis_context": {
      "health": {
        "status": "healthy"
      }
    },

    "goals": [
      {
        "id": 8000,
        "name": "Viaje Cartagena",
        "saved_amount": 420000,
        "target_amount": 1200000,
        "created_at": "2025-11-28",
        "due_date": "2025-06-20",
        "priority": "medium"
      },
      {
        "id": 8001,
        "name": "Fondo de Emergencia",
        "saved_amount": 350000,
        "target_amount": 2000000,
        "created_at": "2025-11-28",
        "due_date": "2025-12-30",
        "priority": "high"
      }
    ],

    "semantic_memory": {
      "motivation_profile": {
        "preferred_tone": "encouragement_challenge"
      }
    }
  },

  "adjust_100k": {
    "action": "ADJUST_GOALS",
    "user_id": "123",

    "financial_context": {
      "surplus": {
        "monthly": 100000
      }
    },

    "analysis_context": {
      "health": {
        "status": "warning"
      }
    },

    "goals": [
      {
        "id": 8000,
        "name": "Viaje Cartagena",
        "saved_amount": 420000,
        "target_amount": 1200000,
        "due_date": "2026-06-20",
        "priority": "low"
      },
      {
        "id": 8001,
        "name": "Fondo de Emergencia",
        "saved_amount": 350000,
        "target_amount": 2000000,
        "due_date": "2025-12-30",
        "priority": "critical"
      }
    ],

    "semantic_memory": {
      "risk_attitude": "conservative"
    }
  },

  "track_goal": {
    "action": "TRACK_GOAL",
    "user_id": "123",

    "goal_id": "8000",

    "financial_context": {
      "income": {
        "monthly_average": 2500000
      },
      "surplus": {
        "monthly": 300000
      }
    },

    "analysis_context": {
      "ants": [
        {
          "monthly_estimated_loss": 120000
        }
      ]
    },

    "semantic_memory": {
      "motivation_profile": {
        "preferred_tone": "encouragement_challenge"
      }
    },

    "goals": [
      {
        "id": "8000",
        "name": "Viaje Cartagena",
        "saved_amount": 420000,
        "target_amount": 1200000,
        "due_date": "2025-06-20"
      }
    ],

    "recent_transactions": [
      {
        "id": "6009",
        "date": "2025-11-20",
        "type": "expense",
        "amount": 90000,
        "category": "entertainment"
      }
    ]
  }
  ,
  "build_goal_context": {
    "action": "BUILD_GOAL_CONTEXT",
    "user_id": "123",
    "financial_context": {
      "income": {"monthly_average": 2500000},
      "surplus": {"monthly": 300000},
      "expenses": {"fixed_monthly": 1800000, "variable_monthly_avg": 400000}
    },
    "semantic_memory": {"motivation_profile": {"preferred_tone": "encouragement_challenge"}},
    "goals": [
      {"id": "8000", "name": "Viaje Cartagena", "saved_amount": 420000, "target_amount": 1200000, "due_date": "2026-06-20", "created_at": "2025-11-01"},
      {"id": "8001", "name": "Fondo de Emergencia", "saved_amount": 350000, "target_amount": 2000000, "due_date": "2025-12-30", "created_at": "2025-01-01"}
    ]
  }
}
  


def run_examples(selected: list[str] | None = None) -> None:
  handler = create_agent()
  keys = list(EXAMPLES.keys()) if not selected else selected
  for k in keys:
    sample = EXAMPLES.get(k)
    if sample is None:
      print(f"No example named {k}")
      continue
    print("\n=== Running example:", k, "===")
    try:
      out = handler(sample)
      print(json.dumps(out, indent=2, ensure_ascii=False))
    except Exception as e:
      logger.exception("Example %s failed", k)
      print(f"Example {k} failed: {e}")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--examples", "-e", action="store_true", help="Run builtin example inputs for each action")
  parser.add_argument("--which", "-w", nargs="*", help="Run only selected examples by key (discover_goals evaluate_goal adjust_goals track_goal)")
  args = parser.parse_args()

  if args.examples:
    run_examples(args.which)
  else:
    print("Run with --examples to execute builtin example inputs, or edit the file to add more tests.")


if __name__ == "__main__":
  main()
