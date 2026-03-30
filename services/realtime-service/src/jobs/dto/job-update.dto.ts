// src/jobs/dto/job-update.dto.ts
export class JobUpdateDto {
  jobId: string;
  status: string;
  progress: number;
  message?: string;
  data?: any;
  timestamp: string;
}