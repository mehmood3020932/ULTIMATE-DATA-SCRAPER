// services/realtime-service/src/events/events.service.ts
// Events business logic

import { Injectable, Logger } from '@nestjs/common';
import { EventsGateway } from './events.gateway';

@Injectable()
export class EventsService {
  private readonly logger = new Logger(EventsService.name);

  constructor(private readonly eventsGateway: EventsGateway) {}

  publishJobEvent(jobId: string, eventType: string, data: any) {
    this.eventsGateway.emitJobUpdate(jobId, {
      type: eventType,
      ...data,
    });
    this.logger.debug(`Published ${eventType} for job ${jobId}`);
  }

  publishUserEvent(userId: string, eventType: string, data: any) {
    this.eventsGateway.emitToUser(userId, eventType, data);
    this.logger.debug(`Published ${eventType} to user ${userId}`);
  }
}