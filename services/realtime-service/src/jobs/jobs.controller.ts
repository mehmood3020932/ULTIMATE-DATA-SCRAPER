// services/realtime-service/src/jobs/jobs.controller.ts

import { Controller, Get, Param, Sse } from '@nestjs/common';
import { Observable, interval, map } from 'rxjs';
import { JobsService } from './jobs.service';

@Controller('jobs')
export class JobsController {
  constructor(private readonly jobsService: JobsService) {}

  @Sse(':id/stream')
  streamJobUpdates(@Param('id') jobId: string): Observable<MessageEvent> {
    return this.jobsService.getJobUpdates(jobId);
  }

  @Get(':id/status')
  async getJobStatus(@Param('id') jobId: string) {
    return this.jobsService.getJobStatus(jobId);
  }
}