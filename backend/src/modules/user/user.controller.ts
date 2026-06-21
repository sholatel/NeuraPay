import { Body, Controller, Get, Param, ParseUUIDPipe, Post, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { CreateUserDto } from './dto/create-user.dto';
import { UserService } from './user.service';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  createUser(@Body() dto: CreateUserDto) {
    return this.userService.createUser(dto);
  }

  // Must be declared before /:id to avoid NestJS treating "account" as a UUID
  @Get('account/:accountNumber')
  @UseGuards(AuthGuard('jwt'))
  lookupByAccountNumber(@Param('accountNumber') accountNumber: string) {
    return this.userService.lookupByAccountNumber(accountNumber);
  }

  @Get(':id')
  getUser(@Param('id', new ParseUUIDPipe()) id: string) {
    return this.userService.findByIdOrThrow(id);
  }
}