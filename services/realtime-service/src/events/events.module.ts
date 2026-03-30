// services/realtime-service/src/events/events.module.ts

import { Module } from '@nestjs/common';
import { EventsGateway } from './events.gateway';
import { EventsService } from './events.service';

@Module({
  providers: [EventsGateway, EventsService],
  exports: [EventsGateway, EventsService],
})
export class EventsModule {}