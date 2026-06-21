/**
 * One-time seeder: assigns NUBAN account numbers to users that don't have one yet.
 *
 * Run from the backend/ directory:
 *   npm run seed:account-numbers
 */

import 'dotenv/config';
import { DataSource } from 'typeorm';
import { getDataSourceConfig } from '../config/config';
import { User } from '../../modules/user/user.entity';
import { generateAccountNumber } from '../../common/utils/account-number.util';

async function run() {
  const dataSource = new DataSource(getDataSourceConfig());
  await dataSource.initialize();
  console.log('Connected to database.');

  const userRepo = dataSource.getRepository(User);

  // How many users already have an account number — used as the offset for new sequences.
  const existingCount = await userRepo.count({ where: { accountNumber: undefined } });
  // Actually count those WITH account numbers to find the highest sequence used.
  const withAccount = await userRepo
    .createQueryBuilder('u')
    .where('u.account_number IS NOT NULL')
    .getCount();

  // Users without an account number, ordered by creation date (oldest first).
  const usersWithout = await userRepo
    .createQueryBuilder('u')
    .where('u.account_number IS NULL')
    .orderBy('u.created_at', 'ASC')
    .getMany();

  if (usersWithout.length === 0) {
    console.log('All users already have account numbers. Nothing to do.');
    await dataSource.destroy();
    return;
  }

  console.log(
    `Found ${usersWithout.length} user(s) without account numbers. Starting from sequence ${withAccount + 1}.`,
  );

  let sequence = withAccount + 1;
  for (const user of usersWithout) {
    const accountNumber = generateAccountNumber(sequence);
    await userRepo.update(user.id, { accountNumber });
    console.log(`  ✓ ${user.email} → ${accountNumber}`);
    sequence++;
  }

  console.log(`Done. Assigned ${usersWithout.length} account number(s).`);
  await dataSource.destroy();
}

run().catch((err) => {
  console.error('Seeder failed:', err);
  process.exit(1);
});
