import {
  Column,
  CreateDateColumn,
  Entity,
  OneToMany,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { WalletTransaction } from '../transaction/transaction.entity';
import { Wallet } from '../wallet/wallet.entity';

export enum UserStatus {
  OPENED = 'opened',
  BLOCKED = 'blocked',
  ONBOARDING = 'onboarding',
}

@Entity({ name: 'users' })
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 120 })
  name: string;

  @Column({ type: 'varchar', length: 160, unique: true, nullable:false })
  email: string;

  @Column({ name: 'password_hash', type: 'varchar', length: 255, select: false })
  passwordHash: string;

  @Column({
    name: 'account_number',
    type: 'varchar',
    length: 10,
    unique: true,
    nullable: true,
  })
  accountNumber: string | null;

  @Column({
    type: 'enum',
    enum: UserStatus,
    default: UserStatus.ONBOARDING,
  })
  status: UserStatus;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @OneToMany(() => Wallet, (wallet) => wallet.user)
  wallets: Wallet[];

  @OneToMany(() => WalletTransaction, (transaction) => transaction.fromUser)
  outgoingTransactions: WalletTransaction[];

  @OneToMany(() => WalletTransaction, (transaction) => transaction.toUser)
  incomingTransactions: WalletTransaction[];
}