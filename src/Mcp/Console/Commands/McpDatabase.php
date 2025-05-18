<?php

namespace Mcp\Console\Commands;

use Illuminate\Console\Command;
use Mcp\Database\DatabaseManager;
use Symfony\Component\Console\Helper\Table;

class McpDatabase extends Command
{
    protected $signature = 'mcp:db
                          {action : The action to perform (tables|columns|indexes|fk|size|stats|optimize|analyze|slow|connections|locks)}
                          {table? : The table name for table-specific actions}
                          {--connection= : The database connection to use}
                          {--limit=10 : Limit for slow queries}';

    protected $description = 'Database management and monitoring commands';

    protected DatabaseManager $manager;

    public function __construct(DatabaseManager $manager)
    {
        parent::__construct();
        $this->manager = $manager;
    }

    public function handle(): int
    {
        $action = $this->argument('action');
        $table = $this->argument('table');
        $connection = $this->option('connection');
        $limit = $this->option('limit');

        if ($connection) {
            $this->manager = new DatabaseManager($connection);
        }

        try {
            switch ($action) {
                case 'tables':
                    $this->showTables();
                    break;

                case 'columns':
                    if (!$table) {
                        $this->error('Table name is required for columns action');
                        return 1;
                    }
                    $this->showColumns($table);
                    break;

                case 'indexes':
                    if (!$table) {
                        $this->error('Table name is required for indexes action');
                        return 1;
                    }
                    $this->showIndexes($table);
                    break;

                case 'fk':
                    if (!$table) {
                        $this->error('Table name is required for foreign keys action');
                        return 1;
                    }
                    $this->showForeignKeys($table);
                    break;

                case 'size':
                    if (!$table) {
                        $this->error('Table name is required for size action');
                        return 1;
                    }
                    $this->showTableSize($table);
                    break;

                case 'stats':
                    if (!$table) {
                        $this->error('Table name is required for stats action');
                        return 1;
                    }
                    $this->showTableStats($table);
                    break;

                case 'optimize':
                    if (!$table) {
                        $this->error('Table name is required for optimize action');
                        return 1;
                    }
                    $this->optimizeTable($table);
                    break;

                case 'analyze':
                    if (!$table) {
                        $this->error('Table name is required for analyze action');
                        return 1;
                    }
                    $this->analyzeTable($table);
                    break;

                case 'slow':
                    $this->showSlowQueries($limit);
                    break;

                case 'connections':
                    $this->showConnections();
                    break;

                case 'locks':
                    $this->showLocks();
                    break;

                default:
                    $this->error("Unknown action: {$action}");
                    return 1;
            }

            return 0;
        } catch (\Exception $e) {
            $this->error($e->getMessage());
            return 1;
        }
    }

    protected function showTables(): void
    {
        $tables = $this->manager->getTables();
        
        $this->info("\nDatabase Tables:");
        $this->table(['Table Name'], $tables->map(fn($table) => [$table]));
    }

    protected function showColumns(string $table): void
    {
        $columns = $this->manager->getTableColumns($table);
        
        $this->info("\nColumns for table {$table}:");
        $this->table(
            ['Column Name', 'Type'],
            $columns->map(fn($column) => [$column['name'], $column['type']])
        );
    }

    protected function showIndexes(string $table): void
    {
        $indexes = $this->manager->getTableIndexes($table);
        
        $this->info("\nIndexes for table {$table}:");
        $this->table(
            ['Index Name', 'Columns', 'Unique'],
            collect($indexes)->map(function ($index, $name) {
                return [
                    $name,
                    implode(', ', $index->getColumns()),
                    $index->isUnique() ? 'Yes' : 'No'
                ];
            })
        );
    }

    protected function showForeignKeys(string $table): void
    {
        $foreignKeys = $this->manager->getTableForeignKeys($table);
        
        $this->info("\nForeign Keys for table {$table}:");
        $this->table(
            ['Name', 'Local Columns', 'Foreign Table', 'Foreign Columns'],
            collect($foreignKeys)->map(function ($fk, $name) {
                return [
                    $name,
                    implode(', ', $fk->getLocalColumns()),
                    $fk->getForeignTableName(),
                    implode(', ', $fk->getForeignColumns())
                ];
            })
        );
    }

    protected function showTableSize(string $table): void
    {
        $size = $this->manager->getTableSize($table);
        
        $this->info("\nSize information for table {$table}:");
        $this->table(
            ['Metric', 'Value'],
            [
                ['Total Size', $size['total_size']],
                ['Table Size', $size['table_size']],
                ['Index Size', $size['index_size']],
                ['Row Count', number_format($size['row_count'])]
            ]
        );
    }

    protected function showTableStats(string $table): void
    {
        $stats = $this->manager->getTableStats($table);
        
        $this->info("\nStatistics for table {$table}:");
        $this->table(
            ['Metric', 'Value'],
            [
                ['Live Rows', number_format($stats['live_rows'])],
                ['Dead Rows', number_format($stats['dead_rows'])],
                ['Last Vacuum', $stats['last_vacuum'] ?? 'Never'],
                ['Last Auto-vacuum', $stats['last_autovacuum'] ?? 'Never'],
                ['Last Analyze', $stats['last_analyze'] ?? 'Never'],
                ['Last Auto-analyze', $stats['last_autoanalyze'] ?? 'Never']
            ]
        );
    }

    protected function optimizeTable(string $table): void
    {
        $this->info("Optimizing table {$table}...");
        $this->manager->optimizeTable($table);
        $this->info('Optimization complete');
    }

    protected function analyzeTable(string $table): void
    {
        $this->info("Analyzing table {$table}...");
        $this->manager->analyzeTable($table);
        $this->info('Analysis complete');
    }

    protected function showSlowQueries(int $limit): void
    {
        $queries = $this->manager->getSlowQueries($limit);
        
        $this->info("\nSlow Queries:");
        $this->table(
            ['Query', 'Calls', 'Total Time (s)', 'Avg Time (s)', 'Rows'],
            $queries->map(function ($query) {
                return [
                    substr($query->query, 0, 100) . '...',
                    number_format($query->calls),
                    number_format($query->total_seconds, 2),
                    number_format($query->avg_seconds, 4),
                    number_format($query->rows)
                ];
            })
        );

        $stats = $this->manager->getQueryStats();
        
        $this->info("\nQuery Statistics:");
        $this->table(
            ['Metric', 'Value'],
            [
                ['Total Calls', number_format($stats['total_calls'])],
                ['Total Time (s)', number_format($stats['total_seconds'], 2)],
                ['Total Rows', number_format($stats['total_rows'])],
                ['Avg Time/Call (s)', number_format($stats['avg_seconds_per_call'], 4)],
                ['Avg Rows/Call', number_format($stats['avg_rows_per_call'], 1)]
            ]
        );
    }

    protected function showConnections(): void
    {
        $connections = $this->manager->getActiveConnections();
        
        $this->info("\nActive Connections:");
        $this->table(
            ['PID', 'User', 'Application', 'Client', 'State', 'Query'],
            $connections->map(function ($conn) {
                return [
                    $conn->pid,
                    $conn->username,
                    $conn->application_name,
                    $conn->client_address,
                    $conn->state,
                    substr($conn->query, 0, 100) . '...'
                ];
            })
        );

        $stats = $this->manager->getConnectionStats();
        
        $this->info("\nConnection Statistics:");
        $this->table(
            ['Metric', 'Value'],
            [
                ['Active Connections', number_format($stats['active_connections'])],
                ['Commits', number_format($stats['commits'])],
                ['Rollbacks', number_format($stats['rollbacks'])],
                ['Cache Hit Ratio', number_format($stats['cache_hit_ratio'] * 100, 2) . '%'],
                ['Rows Returned', number_format($stats['rows_returned'])],
                ['Rows Fetched', number_format($stats['rows_fetched'])],
                ['Rows Inserted', number_format($stats['rows_inserted'])],
                ['Rows Updated', number_format($stats['rows_updated'])],
                ['Rows Deleted', number_format($stats['rows_deleted'])]
            ]
        );
    }

    protected function showLocks(): void
    {
        $locks = $this->manager->getLocks();
        
        $this->info("\nActive Locks:");
        $this->table(
            ['PID', 'Table', 'Mode', 'Granted'],
            $locks->map(function ($lock) {
                return [
                    $lock->pid,
                    $lock->table_name,
                    $lock->mode,
                    $lock->granted ? 'Yes' : 'No'
                ];
            })
        );
    }
} 