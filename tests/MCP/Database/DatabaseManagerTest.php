<?php

namespace Tests\Mcp\Database;

use Mcp\Database\DatabaseManager;
use Tests\TestCase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\Log;
use Mockery;

class DatabaseManagerTest extends TestCase
{
    private DatabaseManager $manager;
    private string $connection = 'testing';

    protected function setUp(): void
    {
        parent::setUp();
        $this->manager = new DatabaseManager($this->connection);
    }

    public function testGetTables(): void
    {
        $tables = ['users', 'posts', 'comments'];
        
        $schemaManager = Mockery::mock('Doctrine\DBAL\Schema\AbstractSchemaManager');
        $schemaManager->shouldReceive('listTableNames')
            ->once()
            ->andReturn($tables);

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'getDoctrineSchemaManager' => $schemaManager
            ]));

        $result = $this->manager->getTables();
        
        $this->assertEquals($tables, $result->all());
    }

    public function testGetTableColumns(): void
    {
        $table = 'users';
        $columns = ['id', 'name', 'email'];
        $types = ['integer', 'string', 'string'];

        Schema::shouldReceive('connection')
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'getColumnListing' => $columns,
                'getColumnType' => function ($tableName, $column) use ($table, $columns, $types) {
                    $this->assertEquals($table, $tableName);
                    return $types[array_search($column, $columns)];
                }
            ]));

        $result = $this->manager->getTableColumns($table);
        
        $this->assertEquals(3, $result->count());
        $this->assertEquals('integer', $result[0]['type']);
        $this->assertEquals('string', $result[1]['type']);
        $this->assertEquals('string', $result[2]['type']);
    }

    public function testGetTableIndexes(): void
    {
        $table = 'users';
        $indexes = [
            'users_pkey' => Mockery::mock(),
            'users_email_unique' => Mockery::mock()
        ];

        $schemaManager = Mockery::mock('Doctrine\DBAL\Schema\AbstractSchemaManager');
        $schemaManager->shouldReceive('listTableIndexes')
            ->once()
            ->with($table)
            ->andReturn($indexes);

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'getDoctrineSchemaManager' => $schemaManager
            ]));

        $result = $this->manager->getTableIndexes($table);
        
        $this->assertEquals($indexes, $result->all());
    }

    public function testGetTableForeignKeys(): void
    {
        $table = 'comments';
        $foreignKeys = [
            'comments_user_id_foreign' => Mockery::mock(),
            'comments_post_id_foreign' => Mockery::mock()
        ];

        $schemaManager = Mockery::mock('Doctrine\DBAL\Schema\AbstractSchemaManager');
        $schemaManager->shouldReceive('listTableForeignKeys')
            ->once()
            ->with($table)
            ->andReturn($foreignKeys);

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'getDoctrineSchemaManager' => $schemaManager
            ]));

        $result = $this->manager->getTableForeignKeys($table);
        
        $this->assertEquals($foreignKeys, $result->all());
    }

    public function testTruncateTable(): void
    {
        $table = 'users';
        
        $query = Mockery::mock();
        $query->shouldReceive('truncate')
            ->once();

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'table' => $query
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with("Truncated table: {$table}");

        $this->manager->truncateTable($table);
    }

    public function testDropTable(): void
    {
        $table = 'users';

        Schema::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'dropIfExists' => true
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with("Dropped table: {$table}");

        $this->manager->dropTable($table);
    }

    public function testGetTableSize(): void
    {
        $table = 'users';
        $result = (object)[
            'total_size' => '1 MB',
            'table_size' => '800 KB',
            'index_size' => '200 KB',
            'row_count' => 1000
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [$result],
                'raw' => 'raw query'
            ]));

        $size = $this->manager->getTableSize($table);
        
        $this->assertEquals($result->total_size, $size['total_size']);
        $this->assertEquals($result->table_size, $size['table_size']);
        $this->assertEquals($result->index_size, $size['index_size']);
        $this->assertEquals($result->row_count, $size['row_count']);
    }

    public function testGetTableStats(): void
    {
        $table = 'users';
        $result = (object)[
            'live_rows' => 1000,
            'dead_rows' => 10,
            'last_vacuum' => '2024-01-01',
            'last_autovacuum' => '2024-01-02',
            'last_analyze' => '2024-01-03',
            'last_autoanalyze' => '2024-01-04'
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [$result],
                'raw' => 'raw query'
            ]));

        $stats = $this->manager->getTableStats($table);
        
        $this->assertEquals($result->live_rows, $stats['live_rows']);
        $this->assertEquals($result->dead_rows, $stats['dead_rows']);
        $this->assertEquals($result->last_vacuum, $stats['last_vacuum']);
        $this->assertEquals($result->last_autovacuum, $stats['last_autovacuum']);
        $this->assertEquals($result->last_analyze, $stats['last_analyze']);
        $this->assertEquals($result->last_autoanalyze, $stats['last_autoanalyze']);
    }

    public function testOptimizeTable(): void
    {
        $table = 'users';

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [],
                'raw' => 'raw query'
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with("Optimized table: {$table}");

        $this->manager->optimizeTable($table);
    }

    public function testAnalyzeTable(): void
    {
        $table = 'users';

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [],
                'raw' => 'raw query'
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with("Analyzed table: {$table}");

        $this->manager->analyzeTable($table);
    }

    public function testGetSlowQueries(): void
    {
        $queries = [
            (object)[
                'query' => 'SELECT * FROM users',
                'calls' => 100,
                'total_seconds' => 10.5,
                'avg_seconds' => 0.105,
                'rows' => 1000
            ]
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => $queries,
                'raw' => 'raw query'
            ]));

        $result = $this->manager->getSlowQueries();
        
        $this->assertEquals($queries, $result->all());
    }

    public function testGetQueryStats(): void
    {
        $result = (object)[
            'total_calls' => 1000,
            'total_seconds' => 100,
            'total_rows' => 10000
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [$result],
                'raw' => 'raw query'
            ]));

        $stats = $this->manager->getQueryStats();
        
        $this->assertEquals($result->total_calls, $stats['total_calls']);
        $this->assertEquals($result->total_seconds, $stats['total_seconds']);
        $this->assertEquals($result->total_rows, $stats['total_rows']);
        $this->assertEquals(0.1, $stats['avg_seconds_per_call']);
        $this->assertEquals(10, $stats['avg_rows_per_call']);
    }

    public function testResetQueryStats(): void
    {
        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [],
                'raw' => 'raw query'
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with('Reset query statistics');

        $this->manager->resetQueryStats();
    }

    public function testGetConnectionStats(): void
    {
        $result = (object)[
            'active_connections' => 10,
            'commits' => 1000,
            'rollbacks' => 10,
            'blks_read' => 100,
            'blks_hit' => 900,
            'rows_returned' => 10000,
            'rows_fetched' => 5000,
            'rows_inserted' => 1000,
            'rows_updated' => 500,
            'rows_deleted' => 100
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [$result],
                'raw' => 'raw query'
            ]));

        $stats = $this->manager->getConnectionStats();
        
        $this->assertEquals($result->active_connections, $stats['active_connections']);
        $this->assertEquals($result->commits, $stats['commits']);
        $this->assertEquals($result->rollbacks, $stats['rollbacks']);
        $this->assertEquals($result->blks_read, $stats['blocks_read']);
        $this->assertEquals($result->blks_hit, $stats['blocks_hit']);
        $this->assertEquals(0.9, $stats['cache_hit_ratio']);
        $this->assertEquals($result->rows_returned, $stats['rows_returned']);
        $this->assertEquals($result->rows_fetched, $stats['rows_fetched']);
        $this->assertEquals($result->rows_inserted, $stats['rows_inserted']);
        $this->assertEquals($result->rows_updated, $stats['rows_updated']);
        $this->assertEquals($result->rows_deleted, $stats['rows_deleted']);
    }

    public function testKillConnection(): void
    {
        $pid = 12345;

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => [],
                'raw' => 'raw query'
            ]));

        Log::shouldReceive('info')
            ->once()
            ->with("Killed connection: {$pid}");

        $this->manager->killConnection($pid);
    }

    public function testGetActiveConnections(): void
    {
        $connections = [
            (object)[
                'pid' => 12345,
                'username' => 'user',
                'application_name' => 'app',
                'client_address' => '127.0.0.1',
                'backend_start' => '2024-01-01',
                'transaction_start' => '2024-01-01',
                'query_start' => '2024-01-01',
                'state' => 'active',
                'wait_event' => null,
                'query' => 'SELECT * FROM users'
            ]
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => $connections,
                'raw' => 'raw query'
            ]));

        $result = $this->manager->getActiveConnections();
        
        $this->assertEquals($connections, $result->all());
    }

    public function testGetLocks(): void
    {
        $locks = [
            (object)[
                'pid' => 12345,
                'table_name' => 'users',
                'mode' => 'AccessShareLock',
                'granted' => true
            ]
        ];

        DB::shouldReceive('connection')
            ->once()
            ->with($this->connection)
            ->andReturn(Mockery::mock([
                'select' => $locks,
                'raw' => 'raw query'
            ]));

        $result = $this->manager->getLocks();
        
        $this->assertEquals($locks, $result->all());
    }
} 