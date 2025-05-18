<?php

namespace Tests\Mcp\Console\Commands;

use Mcp\Console\Commands\McpDatabase;
use Mcp\Database\DatabaseManager;
use Tests\TestCase;
use Illuminate\Support\Collection;
use Mockery;

class McpDatabaseTest extends TestCase
{
    private McpDatabase $command;
    private DatabaseManager $manager;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->manager = Mockery::mock(DatabaseManager::class);
        $this->command = new McpDatabase($this->manager);
    }

    public function testShowTables(): void
    {
        $tables = collect(['users', 'posts', 'comments']);
        
        $this->manager->shouldReceive('getTables')
            ->once()
            ->andReturn($tables);

        $this->artisan('mcp:db', ['action' => 'tables'])
            ->expectsOutput("\nDatabase Tables:")
            ->assertExitCode(0);
    }

    public function testShowColumnsWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'columns'])
            ->expectsOutput('Table name is required for columns action')
            ->assertExitCode(1);
    }

    public function testShowColumns(): void
    {
        $columns = collect([
            ['name' => 'id', 'type' => 'integer'],
            ['name' => 'name', 'type' => 'string'],
            ['name' => 'email', 'type' => 'string']
        ]);

        $this->manager->shouldReceive('getTableColumns')
            ->once()
            ->with('users')
            ->andReturn($columns);

        $this->artisan('mcp:db', ['action' => 'columns', 'table' => 'users'])
            ->expectsOutput("\nColumns for table users:")
            ->assertExitCode(0);
    }

    public function testShowIndexesWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'indexes'])
            ->expectsOutput('Table name is required for indexes action')
            ->assertExitCode(1);
    }

    public function testShowIndexes(): void
    {
        $indexes = collect([
            'users_pkey' => Mockery::mock([
                'getColumns' => ['id'],
                'isUnique' => true
            ]),
            'users_email_unique' => Mockery::mock([
                'getColumns' => ['email'],
                'isUnique' => true
            ])
        ]);

        $this->manager->shouldReceive('getTableIndexes')
            ->once()
            ->with('users')
            ->andReturn($indexes);

        $this->artisan('mcp:db', ['action' => 'indexes', 'table' => 'users'])
            ->expectsOutput("\nIndexes for table users:")
            ->assertExitCode(0);
    }

    public function testShowForeignKeysWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'fk'])
            ->expectsOutput('Table name is required for foreign keys action')
            ->assertExitCode(1);
    }

    public function testShowForeignKeys(): void
    {
        $foreignKeys = collect([
            'comments_user_id_foreign' => Mockery::mock([
                'getLocalColumns' => ['user_id'],
                'getForeignTableName' => 'users',
                'getForeignColumns' => ['id']
            ])
        ]);

        $this->manager->shouldReceive('getTableForeignKeys')
            ->once()
            ->with('comments')
            ->andReturn($foreignKeys);

        $this->artisan('mcp:db', ['action' => 'fk', 'table' => 'comments'])
            ->expectsOutput("\nForeign Keys for table comments:")
            ->assertExitCode(0);
    }

    public function testShowTableSizeWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'size'])
            ->expectsOutput('Table name is required for size action')
            ->assertExitCode(1);
    }

    public function testShowTableSize(): void
    {
        $size = [
            'total_size' => '1 MB',
            'table_size' => '800 KB',
            'index_size' => '200 KB',
            'row_count' => 1000
        ];

        $this->manager->shouldReceive('getTableSize')
            ->once()
            ->with('users')
            ->andReturn($size);

        $this->artisan('mcp:db', ['action' => 'size', 'table' => 'users'])
            ->expectsOutput("\nSize information for table users:")
            ->assertExitCode(0);
    }

    public function testShowTableStatsWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'stats'])
            ->expectsOutput('Table name is required for stats action')
            ->assertExitCode(1);
    }

    public function testShowTableStats(): void
    {
        $stats = [
            'live_rows' => 1000,
            'dead_rows' => 10,
            'last_vacuum' => '2024-01-01',
            'last_autovacuum' => '2024-01-02',
            'last_analyze' => '2024-01-03',
            'last_autoanalyze' => '2024-01-04'
        ];

        $this->manager->shouldReceive('getTableStats')
            ->once()
            ->with('users')
            ->andReturn($stats);

        $this->artisan('mcp:db', ['action' => 'stats', 'table' => 'users'])
            ->expectsOutput("\nStatistics for table users:")
            ->assertExitCode(0);
    }

    public function testOptimizeTableWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'optimize'])
            ->expectsOutput('Table name is required for optimize action')
            ->assertExitCode(1);
    }

    public function testOptimizeTable(): void
    {
        $this->manager->shouldReceive('optimizeTable')
            ->once()
            ->with('users');

        $this->artisan('mcp:db', ['action' => 'optimize', 'table' => 'users'])
            ->expectsOutput('Optimizing table users...')
            ->expectsOutput('Optimization complete')
            ->assertExitCode(0);
    }

    public function testAnalyzeTableWithoutTable(): void
    {
        $this->artisan('mcp:db', ['action' => 'analyze'])
            ->expectsOutput('Table name is required for analyze action')
            ->assertExitCode(1);
    }

    public function testAnalyzeTable(): void
    {
        $this->manager->shouldReceive('analyzeTable')
            ->once()
            ->with('users');

        $this->artisan('mcp:db', ['action' => 'analyze', 'table' => 'users'])
            ->expectsOutput('Analyzing table users...')
            ->expectsOutput('Analysis complete')
            ->assertExitCode(0);
    }

    public function testShowSlowQueries(): void
    {
        $queries = collect([
            (object)[
                'query' => 'SELECT * FROM users',
                'calls' => 100,
                'total_seconds' => 10.5,
                'avg_seconds' => 0.105,
                'rows' => 1000
            ]
        ]);

        $stats = [
            'total_calls' => 1000,
            'total_seconds' => 100,
            'total_rows' => 10000,
            'avg_seconds_per_call' => 0.1,
            'avg_rows_per_call' => 10
        ];

        $this->manager->shouldReceive('getSlowQueries')
            ->once()
            ->with(10)
            ->andReturn($queries);

        $this->manager->shouldReceive('getQueryStats')
            ->once()
            ->andReturn($stats);

        $this->artisan('mcp:db', ['action' => 'slow'])
            ->expectsOutput("\nSlow Queries:")
            ->expectsOutput("\nQuery Statistics:")
            ->assertExitCode(0);
    }

    public function testShowConnections(): void
    {
        $connections = collect([
            (object)[
                'pid' => 12345,
                'username' => 'user',
                'application_name' => 'app',
                'client_address' => '127.0.0.1',
                'state' => 'active',
                'query' => 'SELECT * FROM users'
            ]
        ]);

        $stats = [
            'active_connections' => 10,
            'commits' => 1000,
            'rollbacks' => 10,
            'blocks_read' => 100,
            'blocks_hit' => 900,
            'cache_hit_ratio' => 0.9,
            'rows_returned' => 10000,
            'rows_fetched' => 5000,
            'rows_inserted' => 1000,
            'rows_updated' => 500,
            'rows_deleted' => 100
        ];

        $this->manager->shouldReceive('getActiveConnections')
            ->once()
            ->andReturn($connections);

        $this->manager->shouldReceive('getConnectionStats')
            ->once()
            ->andReturn($stats);

        $this->artisan('mcp:db', ['action' => 'connections'])
            ->expectsOutput("\nActive Connections:")
            ->expectsOutput("\nConnection Statistics:")
            ->assertExitCode(0);
    }

    public function testShowLocks(): void
    {
        $locks = collect([
            (object)[
                'pid' => 12345,
                'table_name' => 'users',
                'mode' => 'AccessShareLock',
                'granted' => true
            ]
        ]);

        $this->manager->shouldReceive('getLocks')
            ->once()
            ->andReturn($locks);

        $this->artisan('mcp:db', ['action' => 'locks'])
            ->expectsOutput("\nActive Locks:")
            ->assertExitCode(0);
    }

    public function testUnknownAction(): void
    {
        $this->artisan('mcp:db', ['action' => 'unknown'])
            ->expectsOutput('Unknown action: unknown')
            ->assertExitCode(1);
    }

    public function testHandleException(): void
    {
        $this->manager->shouldReceive('getTables')
            ->once()
            ->andThrow(new \Exception('Database error'));

        $this->artisan('mcp:db', ['action' => 'tables'])
            ->expectsOutput('Database error')
            ->assertExitCode(1);
    }
} 