import { ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { hash } from 'bcrypt';
import { DataSource, Repository } from 'typeorm';
import { generateAccountNumber } from '../../common/utils/account-number.util';
import { Wallet } from '../wallet/wallet.entity';
import { CreateUserDto } from './dto/create-user.dto';
import { User, UserStatus } from './user.entity';

const DEFAULT_CURRENCY = 'NGN';

@Injectable()
export class UserService {
  constructor(
    private readonly dataSource: DataSource,
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async createUser(dto: CreateUserDto) {
    try {
      return await this.dataSource.transaction(async (manager) => {
        const passwordHash = await hash(dto.password, 10);

        const user = manager.create(User, {
          name: dto.name,
          email: dto.email.toLowerCase(),
          passwordHash,
          status: UserStatus.ONBOARDING,
        });

        const savedUser = await manager.save(User, user);

        // Count all users (including the one just saved) to derive a unique sequence.
        // Safe inside the transaction — concurrent creates each see their own count.
        const row = await manager
          .createQueryBuilder(User, 'u')
          .select('COUNT(*)', 'count')
          .getRawOne<{ count: string }>();

        savedUser.accountNumber = generateAccountNumber(Number(row?.count ?? 1));
        await manager.save(User, savedUser);

        const wallet = manager.create(Wallet, {
          userId: savedUser.id,
          currency: DEFAULT_CURRENCY,
        });
        const savedWallet = await manager.save(Wallet, wallet);

        savedUser.status = UserStatus.OPENED;
        const openedUser = await manager.save(User, savedUser);

        return {
          user: this.toPublicUser(openedUser),
          defaultWallet: savedWallet,
        };
      });
    } catch (error) {
      if ((error as { code?: string }).code === '23505') {
        throw new ConflictException('User email already exists');
      }
      throw error;
    }
  }

  async findByIdOrThrow(id: string) {
    const user = await this.userRepository.findOne({ where: { id } });
    if (!user) throw new NotFoundException('User not found');
    return user;
  }

  async findByAccountNumberOrThrow(accountNumber: string) {
    const user = await this.userRepository.findOne({ where: { accountNumber } });
    if (!user) throw new NotFoundException(`No user found with account number ${accountNumber}`);
    return user;
  }

  async lookupByAccountNumber(accountNumber: string) {
    const user = await this.findByAccountNumberOrThrow(accountNumber);
    return {
      name: user.name,
      accountNumber: user.accountNumber,
      bank: 'NeuraPay',
      email: user.email,
    };
  }

  async findByEmailWithPassword(email: string) {
    return this.userRepository
      .createQueryBuilder('user')
      .addSelect('user.passwordHash')
      .where('LOWER(user.email) = LOWER(:email)', { email })
      .getOne();
  }

  toPublicUser(user: User) {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      accountNumber: user.accountNumber,
      status: user.status,
      createdAt: user.createdAt,
    };
  }
}
