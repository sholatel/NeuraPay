import { MigrationInterface, QueryRunner } from "typeorm";

export class AddedAccountNumberColumn1781732700986 implements MigrationInterface {
    name = 'AddedAccountNumberColumn1781732700986'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`ALTER TABLE "users" ADD "account_number" character varying(10)`);
        await queryRunner.query(`ALTER TABLE "users" ADD CONSTRAINT "UQ_6ef2c9d08bf32f14242c36d0af2" UNIQUE ("account_number")`);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`ALTER TABLE "users" DROP CONSTRAINT "UQ_6ef2c9d08bf32f14242c36d0af2"`);
        await queryRunner.query(`ALTER TABLE "users" DROP COLUMN "account_number"`);
    }

}
