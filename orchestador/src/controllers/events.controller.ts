import { Controller, Post, Body, Get, Param } from '@nestjs/common';
import { EventsService } from '../services/events.service';

@Controller('events')
export class EventsController {
  constructor(private eventsService: EventsService) {}

  @Post()
  async handleEvent(@Body() event: any) {
    return this.eventsService.processEvent(event);
  }

  @Get('context/:userId')
  async getContext(@Param('userId') userId: string) {
    return this.eventsService.getContext(userId);
  }
}
