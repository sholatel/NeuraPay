import {
  BadRequestException,
  ConflictException,
  Injectable,
  Logger,
  NotFoundException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { DataSource, EntityManager, Repository } from 'typeorm';
import { LedgerEntryType } from '../ledger/ledger-entry.entity';
import { LedgerService } from '../ledger/ledger.service';
import { NotificationService } from '../notification/notification.service';
import { User } from '../user/user.entity';
import {
  TransactionStatus,
  TransactionType,
  WalletTransaction,
} from '../transaction/transaction.entity';
import { DepositDto } from './dto/deposit.dto';
import { TransferDto } from './dto/transfer.dto';
import { Wallet } from './wallet.entity';

@Injectable()
export class WalletService {
  private readonly logger = new Logger(WalletService.name);

  constructor(
    private readonly dataSource: DataSource,
    @InjectRepository(Wallet)
    private readonly walletRepository: Repository<Wallet>,
    private readonly ledgerService: LedgerService,
    private readonly notificationService: NotificationService,
  ) {}

  async findUserWalletOrThrow(
    userId: string,
    currency: string,
    manager?: EntityManager,
  ) {
    const repository = manager?.getRepository(Wallet) ?? this.walletRepository;
    const wallet = await repository.findOne({
      where: {
        userId,
        currency,
      },
      relations: {
        user: true,
      },
    });

    if (!wallet) {
      throw new NotFoundException(`Wallet not found for currency ${currency}`);
    }

    return wallet;
  }

  async getWalletsForUser(userId: string) {
    const wallets = await this.walletRepository.find({
      where: { userId },
      order: { createdAt: 'ASC' },
    });

    return Promise.all(
      wallets.map(async (wallet) => ({
        ...wallet,
        balance: await this.ledgerService.getWalletBalance(wallet.id),
      })),
    );
  }

  async getWalletBalanceForUser(userId: string, currency: string) {
    const wallet = await this.findUserWalletOrThrow(userId, currency);
    const balance = await this.ledgerService.getWalletBalance(wallet.id);

    return {
      walletId: wallet.id,
      currency: wallet.currency,
      balance,
    };
  }

  async deposit(userId: string, dto: DepositDto) {
    const { transaction, wallet, balanceAfter } = await this.dataSource.transaction(
      async (manager) => {
        await this.assertReferenceAvailable(dto.reference, dto.amount, dto.currency, manager);

        const wallet = await this.findUserWalletOrThrow(userId, dto.currency, manager);

        const transaction = manager.create(WalletTransaction, {
          type: TransactionType.DEPOSIT,
          status: TransactionStatus.SUCCESS,
          reference: dto.reference,
          fromUserId: null,
          toUserId: userId,
          amount: dto.amount,
          currency: dto.currency,
        });

        const savedTransaction = await manager.save(WalletTransaction, transaction);

        await this.ledgerService.createEntry(manager, {
          walletId: wallet.id,
          transactionId: savedTransaction.id,
          amount: dto.amount,
          type: LedgerEntryType.CREDIT,
        });

        const balanceAfter = await this.ledgerService.getWalletBalance(wallet.id, manager);

        return {
          transaction: savedTransaction,
          wallet,
          balanceAfter,
        };
      },
    );

    this.dispatchNotification(
      wallet.user,
      'Wallet deposit received',
      `A deposit of ${dto.amount} ${dto.currency} was posted with reference ${transaction.reference}.`,
    );

    return {
      transaction,
      walletId: wallet.id,
      balanceAfter,
    };
  }

  async transfer(userId: string, dto: TransferDto) {
    if (dto.toUserId === userId) {
      throw new BadRequestException('Self-transfer is not allowed');
    }

    const result = await this.dataSource.transaction(async (manager) => {
      await this.assertReferenceAvailable(dto.reference, dto.amount, dto.currency, manager);

      const senderWallet = await this.findUserWalletOrThrow(userId, dto.currency, manager);
      const receiverWallet = await this.findUserWalletOrThrow(
        dto.toUserId,
        dto.currency,
        manager,
      );

      const lockedSenderWallet = await manager
        .getRepository(Wallet)
        .createQueryBuilder('wallet')
        .where('wallet.id = :walletId', { walletId: senderWallet.id })
        .setLock('pessimistic_write')
        .getOne();

      if (!lockedSenderWallet) {
        throw new BadRequestException('Unable to lock sender wallet for transfer');
      }

      const senderBalance = await this.ledgerService.getWalletBalance(
        lockedSenderWallet.id,
        manager,
      );
      if (senderBalance < dto.amount) {
        throw new BadRequestException('Insufficient balance');
      }

      const transaction = manager.create(WalletTransaction, {
        type: TransactionType.TRANSFER,
        status: TransactionStatus.SUCCESS,
        reference: dto.reference,
        fromUserId: userId,
        toUserId: dto.toUserId,
        amount: dto.amount,
        currency: dto.currency,
      });

      const savedTransaction = await manager.save(WalletTransaction, transaction);

      await this.ledgerService.createEntry(manager, {
        walletId: lockedSenderWallet.id,
        transactionId: savedTransaction.id,
        amount: -dto.amount,
        type: LedgerEntryType.DEBIT,
      });

      await this.ledgerService.createEntry(manager, {
        walletId: receiverWallet.id,
        transactionId: savedTransaction.id,
        amount: dto.amount,
        type: LedgerEntryType.CREDIT,
      });

      const senderBalanceAfter = await this.ledgerService.getWalletBalance(
        lockedSenderWallet.id,
        manager,
      );

      return {
        transaction: savedTransaction,
        senderUser: senderWallet.user,
        receiverUser: receiverWallet.user,
        senderBalanceAfter,
      };
    });

    this.dispatchNotification(
      result.senderUser,
      'Wallet transfer sent',
      `You sent ${dto.amount} ${dto.currency} with reference ${result.transaction.reference}.`,
    );
    this.dispatchNotification(
      result.receiverUser,
      'Wallet transfer received',
      `You received ${dto.amount} ${dto.currency} with reference ${result.transaction.reference}.`,
    );

    return result;
  }

  private async assertReferenceAvailable(
    reference: string,
    amount: number,
    currency: string,
    manager: EntityManager,
  ) {
    const existing = await manager.findOne(WalletTransaction, {
      where: { reference },
    });

    if (!existing) {
      return;
    }

    if (existing.amount === amount && existing.currency === currency) {
      throw new ConflictException('Transaction reference already exists');
    }

    throw new ConflictException('Reference already used for a different transaction');
  }

  private dispatchNotification(user: User, subject: string, text: string) {
    this.notificationService
      .sendNotification({
        notifications: [
          {
            channel: 'email',
            to: user.email,
            subject,
            text,
          },
        ],
      })
      .catch((error) => {
        this.logger.error(error);
      });
  }
}