import 'dotenv/config';
import { DataSource } from 'typeorm';
import { getDataSourceConfig } from './config';

export default new DataSource(getDataSourceConfig());