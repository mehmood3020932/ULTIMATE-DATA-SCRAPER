// services/realtime-service/src/kafka/kafka.service.ts

import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Kafka, Producer } from 'kafkajs';

@Injectable()
export class KafkaService implements OnModuleInit {
  private readonly logger = new Logger(KafkaService.name);
  private kafka: Kafka;
  private producer: Producer;

  constructor(private configService: ConfigService) {}

  async onModuleInit() {
    const brokers = this.configService.get<string>('KAFKA_BROKERS', 'localhost:9092').split(',');
    
    this.kafka = new Kafka({
      clientId: 'realtime-service',
      brokers,
    });

    this.producer = this.kafka.producer();
    await this.producer.connect();
    this.logger.log('Kafka producer connected');
  }

  async sendEvent(topic: string, message: any) {
    await this.producer.send({
      topic,
      messages: [{ value: JSON.stringify(message) }],
    });
  }

  getKafkaInstance(): Kafka {
    return this.kafka;
  }
}