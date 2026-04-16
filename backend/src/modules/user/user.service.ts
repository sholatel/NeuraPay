import { ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { hash } from 'bcrypt';
import { DataSource, Repository } from 'typeorm';
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
    const user = await this.userRepository.findOne({
      where: { id },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    return user;
  }

  async findByEmailWithPassword(email: string) {
    return this.userRepository
      .createQueryBuilder('user')
      .addSelect('user.passwordHash')
      .where('LOWER(user.email) = LOWER(:email)', { email })
      .getOne();
  }

  private toPublicUser(user: User) {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      status: user.status,
      createdAt: user.createdAt,
    };
  }
}