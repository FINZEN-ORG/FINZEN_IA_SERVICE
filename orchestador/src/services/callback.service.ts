import {
  Injectable,
  OnModuleInit,
  OnModuleDestroy,
  Logger,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { SqsService } from './sqs.service'; // Assuming SqsService is in the same directory or adjust import
import {
  SQSClient,
  ReceiveMessageCommand,
  DeleteMessageCommand,
} from '@aws-sdk/client-sqs';

@Injectable()
export class CallbackService implements OnModuleInit, OnModuleDestroy {
  private sqs: SQSClient;
  private queueUrl: string;
  private isPolling = false;
  private readonly logger = new Logger(CallbackService.name);
  private pollingInterval: NodeJS.Timeout;

  constructor(
    private config: ConfigService,
    private eventEmitter: EventEmitter2,
  ) {
    const region = this.config.get<string>('AWS_REGION') || 'us-east-1';
    const accessKeyId = this.config.get<string>('AWS_ACCESS_KEY_ID');
    const secretAccessKey = this.config.get<string>('AWS_SECRET_ACCESS_KEY');
    const sessionToken = this.config.get<string>('AWS_SESSION_TOKEN');

    this.sqs = new SQSClient({
      region,
      ...(accessKeyId && secretAccessKey
        ? {
            credentials: {
              accessKeyId,
              secretAccessKey,
              ...(sessionToken ? { sessionToken } : {}),
            },
          }
        : {}),
    });

    this.queueUrl =
      this.config.get<string>('SQS_ORCHESTRATOR_CALLBACK_QUEUE') || '';
  }

  onModuleInit() {
    if (this.queueUrl) {
      this.logger.log(`Starting SQS Callback Polling on: ${this.queueUrl}`);
      this.startPolling();
    } else {
      this.logger.warn(
        'SQS_ORCHESTRATOR_CALLBACK_QUEUE not defined. Callback polling disabled.',
      );
    }
  }

  onModuleDestroy() {
    this.stopPolling();
  }

  private startPolling() {
    this.isPolling = true;
    this.poll();
  }

  private stopPolling() {
    this.isPolling = false;
    if (this.pollingInterval) {
      clearTimeout(this.pollingInterval);
    }
  }

  private async poll() {
    if (!this.isPolling) return;

    try {
      const command = new ReceiveMessageCommand({
        QueueUrl: this.queueUrl,
        MaxNumberOfMessages: 10,
        WaitTimeSeconds: 20, // Long polling
        VisibilityTimeout: 30,
      });

      const response = await this.sqs.send(command);

      if (response.Messages && response.Messages.length > 0) {
        for (const message of response.Messages) {
          await this.handleMessage(message);
        }
      }
    } catch (error) {
      this.logger.error('Error polling SQS:', error);
    } finally {
      // Schedule next poll immediately
      if (this.isPolling) {
        this.pollingInterval = setTimeout(() => this.poll(), 0);
      }
    }
  }

  private async handleMessage(message: any) {
    try {
      this.logger.log(`Received Callback Message: ${message.Body}`);

      const body = JSON.parse(message.Body);

      // Extract userId from original_payload based on user example
      // Example: {"original_payload": {"user_id": "123", ...}, "result": ...}
      const userId = body.original_payload?.user_id || body.user_id;

      if (userId) {
        this.logger.log(`Emitting event: agent.response.${userId}`);
        this.eventEmitter.emit(`agent.response.${userId}`, body);
      } else {
        this.logger.warn(
          'Received callback message without userId, cannot route response.',
        );
      }

      console.log('\n--- 📩 AGENT RESPONSE RECEIVED 📩 ---');
      console.log(message.Body);
      console.log('-------------------------------------\n');

      // Delete message after processing
      await this.sqs.send(
        new DeleteMessageCommand({
          QueueUrl: this.queueUrl,
          ReceiptHandle: message.ReceiptHandle,
        }),
      );
    } catch (error) {
      this.logger.error('Error handling message:', error);
    }
  }
}
