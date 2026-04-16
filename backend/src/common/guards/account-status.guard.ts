import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { UserStatus } from '../../modules/user/user.entity';
import { UserService } from '../../modules/user/user.service';

@Injectable()
export class AccountStatusGuard implements CanActivate {
  constructor(private readonly userService: UserService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<{ user?: { sub?: string } }>();
    const userId = request.user?.sub;

    if (!userId) {
      throw new UnauthorizedException('Authenticated user context is required');
    }

    const user = await this.userService.findByIdOrThrow(userId);
    if (user.status !== UserStatus.OPENED) {
      throw new ForbiddenException('Only opened accounts can perform wallet transactions');
    }

    return true;
  }
}