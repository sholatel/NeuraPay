import { Module, forwardRef } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AccountStatusGuard } from '../../common/guards/account-status.guard';
import { LedgerModule } from '../ledger/ledger.module';
import { NotificationModule } from '../notification/notification.module';
import { TransactionModule } from '../transaction/transaction.module';
import { UserModule } from '../user/user.module';
import { WalletTransaction } from '../transaction/transaction.entity';
import { WalletController } from './wallet.controller';
import { Wallet } from './wallet.entity';
import { WalletService } from './wallet.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([Wallet, WalletTransaction]),
    UserModule,
    forwardRef(() => LedgerModule),
    forwardRef(() => TransactionModule),
    NotificationModule,
  ],
  controllers: [WalletController],
  providers: [WalletService, AccountStatusGuard],
  exports: [WalletService, TypeOrmModule],
})
export class WalletModule {}