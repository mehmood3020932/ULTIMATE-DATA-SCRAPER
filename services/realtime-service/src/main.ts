// services/realtime-service/src/main.ts
// Realtime Service Entry Point

import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ConfigService } from '@nestjs/config';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);
  
  const port = configService.get<number>('PORT', 3000);
  
  app.enableCors({
    origin: '*',
    credentials: true,
  });
  
  await app.listen(port);
  logger.log(`Realtime service running on port ${port}`);
}

bootstrap();