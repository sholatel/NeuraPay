import { Injectable, Logger } from '@nestjs/common';
import { SendNotificationRequest } from './interfaces/notification-provider.interface';
import { EmailProvider } from './providers/email.provider';

@Injectable()
export class NotificationService {
  private readonly logger = new Logger(NotificationService.name);

  constructor(private readonly emailProvider: EmailProvider) {}

  async sendNotification(request: SendNotificationRequest) {
    const deliveries = request.notifications.map((notification) => {
      switch (notification.channel) {
        case 'email':
          return this.emailProvider.send({
            to: notification.to,
            subject: notification.subject,
            text: notification.text,
          });
        default:
          this.logger.warn(`Unsupported notification channel: ${String(notification)}`);
          return Promise.resolve();
      }
    });

    const result = await Promise.allSettled(deliveries);

    result.forEach((entry) => {
      if (entry.status === 'rejected') {
        this.logger.error(entry.reason);
      }
    });
  }
}