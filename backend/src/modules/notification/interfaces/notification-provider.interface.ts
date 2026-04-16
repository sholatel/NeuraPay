export type NotificationChannel = 'email';

export interface NotificationMessage {
  to: string;
  subject: string;
  text: string;
}

export interface NotificationConfig {
  channel: NotificationChannel;
  [key: string]: string;
}

export interface EmailNotificationConfig extends NotificationConfig {
  channel: 'email';
  to: string;
  subject: string;
  text: string;
}


export interface SendNotificationRequest {
  notifications: NotificationConfig[];
}

export interface NotificationProvider {
  readonly name: string;
  send(message: NotificationMessage): Promise<void>;
}