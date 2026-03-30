// services/realtime-service/src/health/health.controller.ts

import { Controller, Get } from '@nestjs/common';

@Controller('health')
export class HealthController {
  @Get()
  check() {
    return {
      status: 'healthy',
      service: 'realtime-service',
      timestamp: new Date().toISOString(),
    };
  }
}