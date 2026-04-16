import { Module } from '@nestjs/common';
import { EmailProvider } from './providers/email.provider';
import { NotificationService } from './notification.service';

@Module({
  providers: [NotificationService, EmailProvider],
  exports: [NotificationService],
})
export class NotificationModule {}