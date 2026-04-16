import { Transform } from 'class-transformer';
import { IsInt, IsString, IsUUID, Length, Min } from 'class-validator';

export class TransferDto {
  @IsUUID()
  toUserId: string;

  @IsInt()
  @Min(1)
  amount: number;

  @Transform(({ value }) => String(value).toUpperCase())
  @IsString()
  @Length(3, 3)
  currency: string;

  @IsString()
  @Length(8, 100)
  reference: string;
}