import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Pool } from 'pg';

@Injectable()
export class TransactionsDbService {
  private pool: Pool;

  constructor(private config: ConfigService) {
    const connectionString = this.config.get('TRANSACTIONS_DB_URL');
    if (connectionString) {
      this.pool = new Pool({ connectionString });
    } else {
      this.pool = new Pool({
        host: this.config.get('TRANSACTIONS_DB_HOST', 'localhost'),
        port: parseInt(this.config.get('TRANSACTIONS_DB_PORT', '5432')),
        database: this.config.get('TRANSACTIONS_DB_NAME', 'postgres'),
        user: this.config.get('TRANSACTIONS_DB_USER', 'postgres'),
        password: this.config.get('TRANSACTIONS_DB_PASSWORD', ''),
      });
    }
  }

  async getRecentTransactions(userId: string, limit = 20): Promise<any[]> {
    const query = `
      SELECT id, amount, date, description, 'expense' as type, category_id, created_at, updated_at
      FROM expense WHERE user_id = $1
      UNION ALL
      SELECT id, amount, date, description, 'income' as type, category_id, created_at, updated_at
      FROM income WHERE user_id = $1
      ORDER BY date DESC
      LIMIT $2
    `;
    const res = await this.pool.query(query, [userId, limit]);
    return res.rows;
  }

  async getCategories(userId: string): Promise<any[]> {
    const res = await this.pool.query(
      'SELECT * FROM categories WHERE user_id = $1',
      [userId],
    );
    return res.rows;
  }
}
