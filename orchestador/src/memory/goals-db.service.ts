import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Pool } from 'pg';

@Injectable()
export class GoalsDbService {
  private pool: Pool;

  constructor(private config: ConfigService) {
    const connectionString = this.config.get('GOALS_DB_URL');
    if (connectionString) {
      this.pool = new Pool({ connectionString });
    } else {
      this.pool = new Pool({
        host: this.config.get('GOALS_DB_HOST', 'localhost'),
        port: parseInt(this.config.get('GOALS_DB_PORT', '5432')),
        database: this.config.get('GOALS_DB_NAME', 'postgres'),
        user: this.config.get('GOALS_DB_USER', 'postgres'),
        password: this.config.get('GOALS_DB_PASSWORD', ''),
      });
    }
  }

  async getGoalsByUser(userId: string): Promise<any[]> {
    const res = await this.pool.query(
      'SELECT * FROM goals WHERE user_id = $1 ORDER BY created_at DESC',
      [userId],
    );
    return res.rows;
  }

  async getBudgetsByUser(userId: string): Promise<any[]> {
    const res = await this.pool.query(
      'SELECT * FROM budgets WHERE user_id = $1 ORDER BY created_at DESC',
      [userId],
    );
    return res.rows;
  }
}
