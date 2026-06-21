import { Transform } from 'class-transformer';
import { IsInt, IsString, Length, Matches, Min } from 'class-validator';

export class TransferDto {
  @IsString()
  @Length(10, 10, { message: 'Account number must be exactly 10 digits' })
  @Matches(/^\d{10}$/, { message: 'Account number must contain only digits' })
  toAccountNumber: string;

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
