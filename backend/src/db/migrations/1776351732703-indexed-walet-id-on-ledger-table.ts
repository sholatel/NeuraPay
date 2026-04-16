import { MigrationInterface, QueryRunner } from "typeorm";

export class IndexedWaletIdOnLedgerTable1776351732703 implements MigrationInterface {
    name = 'IndexedWaletIdOnLedgerTable1776351732703'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`CREATE INDEX "IDX_ledger_entries_wallet_id" ON "ledger_entries" ("wallet_id") `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`DROP INDEX "public"."IDX_ledger_entries_wallet_id"`);
    }

}
