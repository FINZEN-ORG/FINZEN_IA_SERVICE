import { Injectable } from '@nestjs/common';
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class SqsService {
  private sqs: SQSClient;

  constructor(private config: ConfigService) {
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
  }

  async sendToQueue(message: any, queueUrl?: string) {
    const url = queueUrl || this.config.get('SQS_QUEUE_URL');

    console.log('[SqsService] Sending to queue URL:', url);
    console.log('[SqsService] Message:', JSON.stringify(message, null, 2));

    const command = new SendMessageCommand({
      QueueUrl: url,
      MessageBody: JSON.stringify(message),
    });
    return this.sqs.send(command);
  }
}
