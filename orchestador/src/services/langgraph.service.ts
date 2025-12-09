import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class LangGraphService {
  constructor(private config: ConfigService) {}

  async decideFlow(event: any, context: any): Promise<any> {
    let agent: string;
    let queueUrl: string;
    let finalData: any = {
      event,
      context,
      timestamp: new Date().toISOString(),
    };

    switch (event.type) {
      // --- Financial Insight Agent ---
      case 'NEW_TRANSACTION':
      case 'TRANSACTION_UPDATED':
      case 'ANOMALY_DETECTION_REQUEST':
      case 'FINANCIAL_SUMMARY_REQUEST':
      case 'ANT_EXPENSES_PROMPT':
      case 'REPETITIVE_EXPENSES_PROMPT':
      case 'HEALTH_PROMPT':
      case 'LEAKS_PROMPT':
      case 'FULL_ANALYSIS_PROMPT':
        agent = 'financial-insight';
        queueUrl =
          this.config.get('SQS_FINANCIAL_INSIGHT_QUEUE_URL') ||
          'https://sqs.us-east-1.amazonaws.com/default/financial-insight-queue';

        finalData = this.formatFinancialPayload(event, context);
        break;

      // --- Goals Agent ---
      case 'NEW_GOAL_CREATED': // Could map to track or evaluate depending on intent, keeping default for now
      case 'GOAL_UPDATED':
      case 'GOAL_VIABILITY_CHECK':
      case 'GOAL_DISCOVERY_REQUEST':
      case 'GOAL_ADJUSTMENT_REQUEST':
      case 'GOAL_PROGRESS_UPDATE':
        agent = 'goals';
        queueUrl =
          this.config.get('SQS_GOALS_QUEUE_URL') ||
          'https://sqs.us-east-1.amazonaws.com/default/goals-queue';

        // Apply specific formatting for Goals Agent
        finalData = this.formatGoalsPayload(event, context);
        break;

      // --- Budget Balancer Agent ---
      case 'BUDGET_UPDATE_REQUEST':
      case 'BUDGET_REBALANCE':
      case 'SPENDING_LIMIT_EXCEEDED':
        agent = 'budget-balancer';
        queueUrl =
          this.config.get('SQS_BUDGET_BALANCER_QUEUE_URL') ||
          'https://sqs.us-east-1.amazonaws.com/default/budget-balancer-queue';
        break;

      // --- Motivational Coach Agent ---
      case 'MILESTONE_REACHED':
      case 'MOTIVATION_REQUEST':
      case 'GOAL_REJECTED':
        agent = 'motivational-coach';
        queueUrl =
          this.config.get('SQS_MOTIVATIONAL_COACH_QUEUE_URL') ||
          'https://sqs.us-east-1.amazonaws.com/default/motivational-coach-queue';
        break;

      default:
        agent = 'financial-insight';
        queueUrl =
          this.config.get('SQS_FINANCIAL_INSIGHT_QUEUE_URL') ||
          'https://sqs.us-east-1.amazonaws.com/default/financial-insight-queue';
    }

    return {
      agent,
      queueUrl,
      data: finalData,
      id: `${event.userId}-${Date.now()}`,
    };
  }

  private formatFinancialPayload(event: any, context: any): any {
    const { userId, type } = event;
    const { semantic, transactions, goals } = context;

    // Default financial context if missing
    const financialContext = {
      monthly_income: semantic?.financial_summary?.monthly_income || 0,
      fixed_expenses: semantic?.financial_summary?.fixed_expenses_monthly || 0,
      variable_expenses: semantic?.financial_summary?.variable_expenses || 0,
      savings: semantic?.financial_summary?.savings || 0,
      month_surplus: semantic?.financial_summary?.excedente_mensual || 0,
    };

    let mode = 'all';
    switch (type) {
      case 'ANT_EXPENSES_PROMPT':
        mode = 'ants';
        break;
      case 'REPETITIVE_EXPENSES_PROMPT':
        mode = 'repetitive';
        break;
      case 'HEALTH_PROMPT':
        mode = 'health'; // Or 'single' based on intent, defaulting to health
        break;
      case 'LEAKS_PROMPT':
        mode = 'leaks';
        break;
      case 'FULL_ANALYSIS_PROMPT':
        mode = 'all';
        break;
      default:
        mode = 'default';
    }

    return {
      mode,
      event_type: type,
      user_id: userId, // Keeping as string/number based on input, usually string in this system
      semantic_memory: {
        habits: semantic?.spending_patterns?.habit_patterns || [],
        subscriptions: semantic?.spending_patterns?.subscriptions || [],
        financial_summary: semantic?.financial_summary || {},
        recent_events: semantic?.episodic_summary || [], // Assuming this exists or empty
      },
      financial_context: financialContext,
      transactions: transactions || [],
      goals: goals || [],
    };
  }

  private formatGoalsPayload(event: any, context: any): any {
    const { userId, type, data } = event;
    const { semantic, transactions, goals, episodic } = context;

    // Helper to extract financial context from semantic memory or calculate it
    const financialContext = {
      monthly_income: semantic?.financial_summary?.monthly_income || 0,
      excedente_mensual: semantic?.financial_summary?.excedente_mensual || 0,
      fixed_expenses_monthly:
        semantic?.financial_summary?.fixed_expenses_monthly || 0,
      monthly_surplus: semantic?.financial_summary?.excedente_mensual || 0, // Alias for adjust/track
    };

    switch (type) {
      case 'GOAL_DISCOVERY_REQUEST':
        return {
          action: 'DISCOVER_GOALS',
          user_id: userId,
          semantic_memory: {
            financial_summary: semantic?.financial_summary || {},
            spending_patterns: semantic?.spending_patterns || {},
          },
          financial_context: {
            monthly_income: financialContext.monthly_income,
            excedente_mensual: financialContext.excedente_mensual,
            fixed_expenses_monthly: financialContext.fixed_expenses_monthly,
          },
          transactions: transactions || [],
          existing_goals: goals || [],
        };

      case 'GOAL_VIABILITY_CHECK':
        return {
          action: 'EVALUATE_GOAL',
          user_id: userId,
          new_goal_proposal: data?.proposed_goal || {},
          financial_context: {
            monthly_income: financialContext.monthly_income,
            excedente_mensual: financialContext.excedente_mensual,
            fixed_expenses_monthly: financialContext.fixed_expenses_monthly,
          },
          semantic_memory: {
            motivation_profile: semantic?.motivation_profile || {},
          },
          existing_goals: goals || [],
        };

      case 'GOAL_ADJUSTMENT_REQUEST':
        return {
          action: 'ADJUST_GOALS',
          user_id: userId,
          financial_context: {
            monthly_surplus: financialContext.monthly_surplus,
          },
          goals: goals || [],
          semantic_memory: {
            motivation_profile: semantic?.motivation_profile || {},
          },
        };

      case 'GOAL_PROGRESS_UPDATE':
        return {
          action: 'TRACK_GOAL',
          user_id: userId,
          goal_id: data?.goalId,
          goals: goals || [],
          financial_context: {
            monthly_income: financialContext.monthly_income,
            monthly_surplus: financialContext.monthly_surplus,
          },
          semantic_memory: {
            financial_summary: semantic?.financial_summary || {},
          },
          recent_transactions: transactions || [],
        };

      default:
        // Default fallback
        return {
          action: 'UNKNOWN_GOAL_ACTION',
          user_id: userId,
          event_type: type,
          data,
          context,
        };
    }
  }
}
