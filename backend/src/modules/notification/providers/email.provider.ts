import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';
import {
  NotificationMessage,
  NotificationProvider,
} from '../interfaces/notification-provider.interface';

@Injectable()
export class EmailProvider implements NotificationProvider {
  readonly name = 'email';

  private readonly logger = new Logger(EmailProvider.name);
  private readonly transporter: nodemailer.Transporter | null;
  private readonly fromAddress: string;

  constructor(configService: ConfigService) {
    const user = configService.get<string>('SMTP_USER');
    const pass = configService.get<string>('SMTP_PASS');
    this.fromAddress = configService.get<string>('SMTP_FROM', user ?? 'noreply@example.com');

    this.transporter = user && pass
      ? nodemailer.createTransport({
          service: 'gmail',
          auth: {
            user,
            pass,
          },
        })
      : null;
  }

  async send(message: NotificationMessage) {
    if (!this.transporter) {
      this.logger.warn('SMTP credentials are missing. Email notification skipped.');
      return;
    }

    await this.transporter.sendMail({
      from: this.fromAddress,
      to: message.to,
      subject: message.subject,
      text: message.text,
    });
  }
}