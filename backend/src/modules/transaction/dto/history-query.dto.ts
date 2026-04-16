import { Transform } from 'class-transformer';
import { IsInt, IsOptional, IsString, Length, Max, Min } from 'class-validator';

export class HistoryQueryDto {
  @Transform(({ value }) => {
    const normalized = String(value ?? '').trim();
    return normalized ? normalized.toUpperCase() : 'NGN';
  })
  @IsString()
  @Length(3, 3)
  currency = 'NGN';

  @Transform(({ value }) => (value === undefined ? 1 : Number(value)))
  @IsOptional()
  @IsInt()
  @Min(1)
  page = 1;

  @Transform(({ value }) => (value === undefined ? 20 : Number(value)))
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit = 20;
}