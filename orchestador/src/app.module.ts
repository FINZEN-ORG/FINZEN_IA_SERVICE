import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { EventEmitterModule } from '@nestjs/event-emitter';
import { EventsController } from './controllers/events.controller';
import { EventsService } from './services/events.service';
import { SqsService } from './services/sqs.service';
import { LangGraphService } from './services/langgraph.service';
import { CallbackService } from './services/callback.service';
import { PostgresEpisodicService } from './memory/postgres-episodic.service';
import { PostgresSemanticService } from './memory/postgres-semantic.service';
import { TransactionsDbService } from './memory/transactions-db.service';
import { GoalsDbService } from './memory/goals-db.service';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    EventEmitterModule.forRoot(),
  ],
  controllers: [EventsController],
  providers: [
    EventsService,
    SqsService,
    LangGraphService,
    CallbackService,
    PostgresEpisodicService,
    PostgresSemanticService,
    TransactionsDbService,
    GoalsDbService,
  ],
})
export class AppModule {}
