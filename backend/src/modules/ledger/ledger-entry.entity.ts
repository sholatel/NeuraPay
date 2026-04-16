import {
  Check,
  Column,
  CreateDateColumn,
  Entity,
  Index,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { WalletTransaction } from '../transaction/transaction.entity';
import { Wallet } from '../wallet/wallet.entity';

export enum LedgerEntryType {
  CREDIT = 'credit',
  DEBIT = 'debit',
}

@Entity({ name: 'ledger_entries' })
@Index('IDX_ledger_entries_wallet_id', ['walletId'])
@Check(`("type" = 'credit' AND "amount" > 0) OR ("type" = 'debit' AND "amount" < 0)`)
export class LedgerEntry {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'wallet_id', type: 'uuid' })
  walletId: string;

  @Column({ name: 'transaction_id', type: 'uuid' })
  transactionId: string;

  @Column({ type: 'integer' })
  amount: number;

  @Column({
    type: 'enum',
    enum: LedgerEntryType,
  })
  type: LedgerEntryType;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @ManyToOne(() => Wallet, (wallet) => wallet.ledgerEntries, {
    onDelete: 'RESTRICT',
  })
  @JoinColumn({ name: 'wallet_id' })
  wallet: Wallet;

  @ManyToOne(() => WalletTransaction, (transaction) => transaction.ledgerEntries, {
    onDelete: 'RESTRICT',
  })
  @JoinColumn({ name: 'transaction_id' })
  transaction: WalletTransaction;
}