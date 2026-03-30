// services/realtime-service/src/app.module.ts
// Application Root Module

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { EventsModule } from './events/events.module';
import { JobsModule } from './jobs/jobs.module';
import { KafkaModule } from './kafka/kafka.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    EventsModule,
    JobsModule,
    KafkaModule,
    HealthModule,
  ],
})
export class AppModule {}