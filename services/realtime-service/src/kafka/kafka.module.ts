// services/realtime-service/src/kafka/kafka.module.ts

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { KafkaService } from './kafka.service';
import { KafkaConsumer } from './kafka.consumer';
import { JobsModule } from '../jobs/jobs.module';

@Module({
  imports: [ConfigModule, JobsModule],
  providers: [KafkaService, KafkaConsumer],
  exports: [KafkaService],
})
export class KafkaModule {}