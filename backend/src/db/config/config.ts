import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { DataSourceOptions } from 'typeorm';
import * as dotenv from 'dotenv';

dotenv.config();

type EnvReader = (key: string, fallback: string) => string;

const buildTypeOrmOptions = (readEnv: EnvReader): DataSourceOptions => ({
  type: 'postgres',
  host: readEnv('DB_HOST', 'localhost'),
  port: parseInt(readEnv('DB_PORT', '5432'), 10),
  username: readEnv('DB_USERNAME', 'postgres'),
  password: readEnv('DB_PASSWORD', 'postgres'),
  database: readEnv('DB_NAME', 'wallet-ledger-db'),
  entities: [readEnv('TYPEORM_ENTITIES_PATH', 'src/**/*.entity.ts')],
  migrations: [readEnv('TYPEORM_MIGRATIONS_PATH', 'src/db/migrations/*.ts')],
  synchronize: false,
  logging: false,
});

export const getTypeOrmConfig = (
  configService: ConfigService,
): TypeOrmModuleOptions =>
  buildTypeOrmOptions((key: string, fallback: string) =>
    configService.get<string>(key, fallback),
  ) as TypeOrmModuleOptions;

export const getDataSourceConfig = (): DataSourceOptions =>
  buildTypeOrmOptions(
    (key: string, fallback: string) => process.env[key] || fallback,
  );