import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { EntityManager, Repository } from 'typeorm';
import { LedgerEntry, LedgerEntryType } from './ledger-entry.entity';

@Injectable()
export class LedgerService {
  constructor(
    @InjectRepository(LedgerEntry)
    private readonly ledgerRepository: Repository<LedgerEntry>,
  ) {}

  async createEntry(
    manager: EntityManager,
    payload: {
      walletId: string;
      transactionId: string;
      amount: number;
      type: LedgerEntryType;
    },
  ) {
    const entry = manager.create(LedgerEntry, payload);
    return manager.save(LedgerEntry, entry);
  }

  async getWalletBalance(walletId: string, manager?: EntityManager) {
    const repository = manager?.getRepository(LedgerEntry) ?? this.ledgerRepository;
    const result = await repository
      .createQueryBuilder('entry')
      .select('COALESCE(SUM(entry.amount), 0)', 'balance')
      .where('entry.walletId = :walletId', { walletId })
      .getRawOne<{ balance: string }>();

    return Number(result?.balance ?? 0);
  }
}