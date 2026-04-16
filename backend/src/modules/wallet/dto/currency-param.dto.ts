import { Transform } from 'class-transformer';
import { IsString, Length } from 'class-validator';

export class CurrencyParamDto {
  @Transform(({ value }) => String(value).toUpperCase())
  @IsString()
  @Length(3, 3)
  currency: string;
}