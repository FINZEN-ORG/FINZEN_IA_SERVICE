import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Pool } from 'pg';

@Injectable()
export class PostgresEpisodicService {
  private pool: Pool;

  constructor(private config: ConfigService) {
    const connectionString = this.config.get('EPISODIC_DB_URL');
    if (connectionString) {
      this.pool = new Pool({ connectionString });
    } else {
      this.pool = new Pool({
        host: this.config.get('EPISODIC_DB_HOST', 'localhost'),
        port: parseInt(this.config.get('EPISODIC_DB_PORT', '5432')),
        database: this.config.get('EPISODIC_DB_NAME', 'postgres'),
        user: this.config.get('EPISODIC_DB_USER', 'postgres'),
        password: this.config.get('EPISODIC_DB_PASSWORD', ''),
      });
    }
  }

  async getEpisodic(userId: string): Promise<any[]> {
    const res = await this.pool.query(
      'SELECT * FROM episodic_memory_orchestrator WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100',
      [userId],
    );
    return res.rows;
  }

  async storeEpisodic(userId: string, record: any): Promise<any> {
    const query = `INSERT INTO episodic_memory_orchestrator (user_id, event_type, description, payload_out, payload_in, agent, status) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`;
    const values = [
      userId,
      record.event_type || null,
      record.description || null,
      record.payload_out || null,
      record.payload_in || null,
      record.agent || null,
      record.status || 'success',
    ];
    const res = await this.pool.query(query, values);
    return res.rows[0];
  }
}
