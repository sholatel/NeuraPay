import {
  Column,
  CreateDateColumn,
  Entity,
  JoinColumn,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { LedgerEntry } from '../ledger/ledger-entry.entity';
import { User } from '../user/user.entity';

export enum TransactionType {
  DEPOSIT = 'deposit',
  TRANSFER = 'transfer',
}

export enum TransactionStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  FAILED = 'failed',
}

@Entity({ name: 'transactions' })
export class WalletTransaction {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({
    type: 'enum',
    enum: TransactionType,
  })
  type: TransactionType;

  @Column({
    type: 'enum',
    enum: TransactionStatus,
    default: TransactionStatus.PENDING,
  })
  status: TransactionStatus;

  @Column({ type: 'varchar', length: 100, unique: true })
  reference: string;

  @Column({ name: 'from_user_id', type: 'uuid', nullable: true })
  fromUserId: string | null;

  @Column({ name: 'to_user_id', type: 'uuid', nullable: true })
  toUserId: string | null;

  @Column({ type: 'integer' })
  amount: number;

  @Column({ type: 'varchar', length: 3 })
  currency: string;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @ManyToOne(() => User, (user) => user.outgoingTransactions, {
    nullable: true,
    onDelete: 'SET NULL',
  })
  @JoinColumn({ name: 'from_user_id' })
  fromUser: User | null;

  @ManyToOne(() => User, (user) => user.incomingTransactions, {
    nullable: true,
    onDelete: 'SET NULL',
  })
  @JoinColumn({ name: 'to_user_id' })
  toUser: User | null;

  @OneToMany(() => LedgerEntry, (entry) => entry.transaction)
  ledgerEntries: LedgerEntry[];
}