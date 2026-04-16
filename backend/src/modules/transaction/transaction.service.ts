import {
  Injectable,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { buildPaginatedResult } from '../../common/utils/pagination.util';
import { LedgerEntry, LedgerEntryType } from '../ledger/ledger-entry.entity';
import { WalletService } from '../wallet/wallet.service';
import { HistoryQueryDto } from './dto/history-query.dto';

@Injectable()
export class TransactionService {
  constructor(
    private readonly walletService: WalletService,
    @InjectRepository(LedgerEntry)
    private readonly ledgerRepository: Repository<LedgerEntry>,
  ) {}

  async getHistory(userId: string, query: HistoryQueryDto) {
    const wallet = await this.walletService.findUserWalletOrThrow(userId, query.currency);
    const skip = (query.page - 1) * query.limit;

    const [entries, total] = await this.ledgerRepository
      .createQueryBuilder('entry')
      .leftJoinAndSelect('entry.transaction', 'transaction')
      .where('entry.walletId = :walletId', { walletId: wallet.id })
      .orderBy('entry.createdAt', 'DESC')
      .skip(skip)
      .take(query.limit)
      .getManyAndCount();

    return buildPaginatedResult(
      entries.map((entry) => ({
        id: entry.id,
        walletId: entry.walletId,
        transactionId: entry.transactionId,
        reference: entry.transaction.reference,
        amount: Math.abs(entry.amount),
        signedAmount: entry.amount,
        currency: entry.transaction.currency,
        direction: entry.type === LedgerEntryType.CREDIT ? 'incoming' : 'outgoing',
        type: entry.transaction.type,
        status: entry.transaction.status,
        counterpartyUserId:
          entry.type === LedgerEntryType.CREDIT
            ? entry.transaction.fromUserId
            : entry.transaction.toUserId,
        createdAt: entry.createdAt,
      })),
      total,
      {
        page: query.page,
        limit: query.limit,
      },
    );
  }
}