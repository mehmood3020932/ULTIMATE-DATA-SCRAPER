// services/realtime-service/src/events/events.gateway.ts
// WebSocket Gateway for realtime updates

import {
  WebSocketGateway,
  WebSocketServer,
  OnGatewayConnection,
  OnGatewayDisconnect,
  SubscribeMessage,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger, UseGuards } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  namespace: '/events',
})
export class EventsGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(EventsGateway.name);
  private userSockets: Map<string, string[]> = new Map();

  constructor(private configService: ConfigService) {}

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
    
    // Authenticate connection
    const token = client.handshake.auth.token;
    if (!token) {
      client.disconnect();
      return;
    }
    
    // Join user-specific room
    const userId = this.extractUserId(token);
    if (userId) {
      client.join(`user:${userId}`);
      
      if (!this.userSockets.has(userId)) {
        this.userSockets.set(userId, []);
      }
      this.userSockets.get(userId).push(client.id);
      
      this.logger.log(`User ${userId} joined with socket ${client.id}`);
    }
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
    
    // Remove from user sockets
    for (const [userId, sockets] of this.userSockets.entries()) {
      const index = sockets.indexOf(client.id);
      if (index !== -1) {
        sockets.splice(index, 1);
        if (sockets.length === 0) {
          this.userSockets.delete(userId);
        }
        break;
      }
    }
  }

  @SubscribeMessage('subscribe_job')
  handleSubscribeJob(client: Socket, jobId: string) {
    client.join(`job:${jobId}`);
    this.logger.log(`Client ${client.id} subscribed to job ${jobId}`);
    return { status: 'subscribed', jobId };
  }

  @SubscribeMessage('unsubscribe_job')
  handleUnsubscribeJob(client: Socket, jobId: string) {
    client.leave(`job:${jobId}`);
    this.logger.log(`Client ${client.id} unsubscribed from job ${jobId}`);
    return { status: 'unsubscribed', jobId };
  }

  // Emit job update to subscribed clients
  emitJobUpdate(jobId: string, data: any) {
    this.server.to(`job:${jobId}`).emit('job_update', {
      jobId,
      ...data,
      timestamp: new Date().toISOString(),
    });
  }

  // Emit to specific user
  emitToUser(userId: string, event: string, data: any) {
    this.server.to(`user:${userId}`).emit(event, {
      ...data,
      timestamp: new Date().toISOString(),
    });
  }

  private extractUserId(token: string): string | null {
    // JWT decoding would go here
    // Simplified for example
    try {
      const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
      return payload.sub;
    } catch {
      return null;
    }
  }
}