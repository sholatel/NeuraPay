import {
  Body,
  Controller,
  ForbiddenException,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
  Query,
  UseGuards,
} from '@nestjs/common';
import { CurrentUser, type AuthenticatedUser } from '../../common/decorators/current-user.decorator';
import { AccountStatusGuard } from '../../common/guards/account-status.guard';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { HistoryQueryDto } from '../transaction/dto/history-query.dto';
import { TransactionService } from '../transaction/transaction.service';
import { DepositDto } from './dto/deposit.dto';
import { TransferDto } from './dto/transfer.dto';
import { WalletService } from './wallet.service';

@UseGuards(JwtAuthGuard)
@Controller('wallet')
export class WalletController {
  constructor(
    private readonly walletService: WalletService,
    private readonly transactionService: TransactionService,
  ) {}

  @Post('deposit')
  @UseGuards(AccountStatusGuard)
  deposit(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: DepositDto,
  ) {
    return this.walletService.deposit(user.sub, dto);
  }

  @Post('transfer')
  @UseGuards(AccountStatusGuard)
  transfer(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: TransferDto,
  ) {
    return this.walletService.transfer(user.sub, dto);
  }

  @Get()
  getWallets(@CurrentUser() user: AuthenticatedUser) {
    return this.walletService.getWalletsForUser(user.sub);
  }

  @Get(':userId/balance')
  getBalance(
    @CurrentUser() user: AuthenticatedUser,
    @Param('userId', new ParseUUIDPipe()) userId: string,
    @Query('currency') currency?: string,
  ) {
    this.assertCurrentUser(user, userId);
    const resolvedCurrency = currency?.trim() ? currency.trim().toUpperCase() : 'NGN';

    return this.walletService.getWalletBalanceForUser(
      userId,
      resolvedCurrency,
    );
  }

  @Get(':userId/transactions')
  getTransactions(
    @CurrentUser() user: AuthenticatedUser,
    @Param('userId', new ParseUUIDPipe()) userId: string,
    @Query() query: HistoryQueryDto,
  ) {
    this.assertCurrentUser(user, userId);
    return this.transactionService.getHistory(userId, query);
  }

  private assertCurrentUser(user: AuthenticatedUser, userId: string) {
    if (user.sub !== userId) {
      throw new ForbiddenException('You can only access your own wallet data');
    }
  }
}