// services/realtime-service/src/jobs/jobs.service.ts

import { Injectable } from '@nestjs/common';
import { Observable, Subject } from 'rxjs';
import { filter, map } from 'rxjs/operators';
import { EventsGateway } from '../events/events.gateway';

@Injectable()
export class JobsService {
  private jobUpdates = new Subject<any>();

  constructor(private eventsGateway: EventsGateway) {}

  getJobUpdates(jobId: string): Observable<MessageEvent> {
    return this.jobUpdates.pipe(
      filter(update => update.jobId === jobId),
      map(update => ({
        data: JSON.stringify(update),
      } as MessageEvent)),
    );
  }

  async getJobStatus(jobId: string): Promise<any> {
    // Would fetch from Redis or database
    return {
      jobId,
      status: 'unknown',
      timestamp: new Date().toISOString(),
    };
  }

  handleJobUpdate(update: any) {
    this.jobUpdates.next(update);
    this.eventsGateway.emitJobUpdate(update.jobId, update);
  }
}