import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHealth() {
    return {
      name: 'wallet-ledger-system',
      status: 'ok',
      timestamp: new Date().toISOString(),
    };
  }
}
