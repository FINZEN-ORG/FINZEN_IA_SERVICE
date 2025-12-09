import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Pool } from 'pg';

@Injectable()
export class PostgresSemanticService {
  private pool: Pool;

  constructor(private config: ConfigService) {
    const connectionString = this.config.get('SEMANTIC_DB_URL');
    if (connectionString) {
      this.pool = new Pool({ connectionString });
    } else {
      this.pool = new Pool({
        host: this.config.get('SEMANTIC_DB_HOST', 'localhost'),
        port: parseInt(this.config.get('SEMANTIC_DB_PORT', '5432')),
        database: this.config.get('SEMANTIC_DB_NAME', 'postgres'),
        user: this.config.get('SEMANTIC_DB_USER', 'postgres'),
        password: this.config.get('SEMANTIC_DB_PASSWORD', ''),
      });
    }
  }

  async getSemantic(userId: string): Promise<any> {
    const res = await this.pool.query(
      'SELECT financial_summary, spending_patterns, motivation_profile FROM semantic_profiles WHERE user_id = $1 LIMIT 1',
      [userId],
    );
    if (!res.rows || res.rows.length === 0) return null;
    const row = res.rows[0];
    const parseIfJson = (v: any) => {
      if (v === null || v === undefined) return null;
      try {
        return typeof v === 'string' ? JSON.parse(v) : v;
      } catch (e) {
        return v;
      }
    };

    return {
      financial_summary: parseIfJson(row.financial_summary),
      spending_patterns: parseIfJson(row.spending_patterns),
      motivation_profile: parseIfJson(row.motivation_profile),
    };
  }
}
