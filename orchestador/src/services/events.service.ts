import { Injectable, HttpException, HttpStatus } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { PostgresEpisodicService } from '../memory/postgres-episodic.service';
import { PostgresSemanticService } from '../memory/postgres-semantic.service';
import { TransactionsDbService } from '../memory/transactions-db.service';
import { GoalsDbService } from '../memory/goals-db.service';
import { SqsService } from '../services/sqs.service';
import { LangGraphService } from '../services/langgraph.service';
import { firstValueFrom, fromEvent, timeout, catchError, of } from 'rxjs';

@Injectable()
export class EventsService {
  constructor(
    private postgresEpisodic: PostgresEpisodicService,
    private postgresSemantic: PostgresSemanticService,
    private transactionsDb: TransactionsDbService,
    private goalsDb: GoalsDbService,
    private sqsService: SqsService,
    private langGraphService: LangGraphService,
    private eventEmitter: EventEmitter2,
  ) {}

  async processEvent(event: any) {
    const userId = event?.userId;

    console.log('DEBUG: Services check', {
      episodic: !!this.postgresEpisodic,
      semantic: !!this.postgresSemantic,
      transactions: !!this.transactionsDb,
      goals: !!this.goalsDb,
      sqs: !!this.sqsService,
      langGraph: !!this.langGraphService,
    });

    try {
      if (!userId) throw new Error('Missing userId in event payload');

      console.log(
        `[EventsService] Processing event: ${event.type} for user ${userId}`,
      );

      const episodic = (await this.postgresEpisodic.getEpisodic(userId)) || [];
      const semantic = (await this.postgresSemantic.getSemantic(userId)) || {};

      const transactions = await this.transactionsDb
        .getRecentTransactions(userId, 20)
        .catch((err) => {
          console.warn(
            '[EventsService] transactionsDb error:',
            err?.message ?? err,
          );
          return [];
        });
      const goals = await this.goalsDb.getGoalsByUser(userId).catch((err) => {
        console.warn('[EventsService] goalsDb error:', err?.message ?? err);
        return [];
      });

      const context = { episodic, semantic, transactions, goals };

      const decision = await this.langGraphService.decideFlow(event, context);

      console.log(
        `[EventsService] Decision: agent=${decision?.agent}, queueUrl=${decision?.queueUrl}`,
      );

      await this.sqsService
        .sendToQueue(decision.data, decision.queueUrl)
        .catch((err) => {
          console.warn('[EventsService] SQS send error:', err?.message ?? err);
        });

      try {
        await this.postgresEpisodic.storeEpisodic(userId, {
          event_type: event.type || 'UNKNOWN',
          description: event.description || null,
          payload_out: decision.data || null,
          payload_in: null,
          agent: decision.agent || null,
          status: 'success',
        });
      } catch (e) {
        console.warn(
          '[EventsService] Failed to store episodic record',
          e?.message || e,
        );
      }

      // Wait for response from agent via Callback Queue
      console.log(`[EventsService] Waiting for response for user ${userId}...`);
      const response = await this.waitForResponse(userId);

      if (response) {
        return {
          status: 'completed',
          correlationId: decision?.id || null,
          agentResponse: response,
        };
      } else {
        return {
          status: 'processed_async',
          message:
            'Agent is processing the request. Response will be handled asynchronously.',
          correlationId: decision?.id || null,
        };
      }
    } catch (err: any) {
      console.error(
        '[EventsService] processEvent error:',
        err?.stack ?? err?.message ?? err,
      );
      throw new HttpException(
        {
          status: 'error',
          message: err?.message ?? 'Unknown error in processEvent',
        },
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  private async waitForResponse(userId: string): Promise<any> {
    // Wait for 15 seconds for the agent.response.{userId} event
    try {
      return await firstValueFrom(
        fromEvent(this.eventEmitter, `agent.response.${userId}`).pipe(
          timeout(15000), // 15 seconds timeout
          catchError(() => of(null)), // Return null on timeout
        ),
      );
    } catch (error) {
      return null;
    }
  }

  async getContext(userId: string) {
    const episodic = (await this.postgresEpisodic.getEpisodic(userId)) || [];
    const semantic = (await this.postgresSemantic.getSemantic(userId)) || {};
    const transactions = await this.transactionsDb
      .getRecentTransactions(userId, 50)
      .catch(() => []);
    const goals = await this.goalsDb.getGoalsByUser(userId).catch(() => []);

    return { episodic, semantic, transactions, goals };
  }
}
