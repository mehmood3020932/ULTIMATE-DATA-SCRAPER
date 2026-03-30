// services/realtime-service/src/kafka/kafka.consumer.ts

import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { KafkaService } from './kafka.service';
import { JobsService } from '../jobs/jobs.service';

@Injectable()
export class KafkaConsumer implements OnModuleInit {
  private readonly logger = new Logger(KafkaConsumer.name);

  constructor(
    private kafkaService: KafkaService,
    private configService: ConfigService,
    private jobsService: JobsService,
  ) {}

  async onModuleInit() {
    const kafka = this.kafkaService.getKafkaInstance();
    const consumer = kafka.consumer({
      groupId: this.configService.get('KAFKA_GROUP_ID', 'realtime-service'),
    });

    await consumer.connect();
    await consumer.subscribe({ topic: 'scraping.updates', fromBeginning: false });

    await consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        try {
          const update = JSON.parse(message.value.toString());
          this.logger.debug(`Received update: ${update.jobId}`);
          this.jobsService.handleJobUpdate(update);
        } catch (error) {
          this.logger.error('Failed to process message', error);
        }
      },
    });

    this.logger.log('Kafka consumer started');
  }
}