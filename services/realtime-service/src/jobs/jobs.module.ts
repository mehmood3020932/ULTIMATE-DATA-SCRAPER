// services/realtime-service/src/jobs/jobs.module.ts

import { Module } from '@nestjs/common';
import { JobsController } from './jobs.controller';
import { JobsService } from './jobs.service';
import { EventsModule } from '../events/events.module';

@Module({
  imports: [EventsModule],
  controllers: [JobsController],
  providers: [JobsService],
})
export class JobsModule {}