<?php

namespace Mcp\Database;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Collection;

class DatabaseManager
{
    protected string $connection;

    public function __construct(string $connection = null)
    {
        $this->connection = $connection ?? config('database.default');
    }

    public function getTables(): Collection
    {
        return collect(DB::connection($this->connection)
            ->getDoctrineSchemaManager()
            ->listTableNames());
    }

    public function getTableColumns(string $table): Collection
    {
        return collect(Schema::connection($this->connection)
            ->getColumnListing($table))
            ->map(function ($column) use ($table) {
                return [
                    'name' => $column,
                    'type' => Schema::connection($this->connection)
                        ->getColumnType($table, $column)
                ];
            });
    }

    public function getTableIndexes(string $table): Collection
    {
        return collect(DB::connection($this->connection)
            ->getDoctrineSchemaManager()
            ->listTableIndexes($table));
    }

    public function getTableForeignKeys(string $table): Collection
    {
        return collect(DB::connection($this->connection)
            ->getDoctrineSchemaManager()
            ->listTableForeignKeys($table));
    }

    public function truncateTable(string $table): void
    {
        DB::connection($this->connection)
            ->table($table)
            ->truncate();

        Log::info("Truncated table: {$table}");
    }

    public function dropTable(string $table): void
    {
        Schema::connection($this->connection)
            ->dropIfExists($table);

        Log::info("Dropped table: {$table}");
    }

    public function getTableSize(string $table): array
    {
        $result = DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    pg_size_pretty(pg_total_relation_size('$table')) as total_size,
                    pg_size_pretty(pg_table_size('$table')) as table_size,
                    pg_size_pretty(pg_indexes_size('$table')) as index_size,
                    (SELECT reltuples::bigint FROM pg_class WHERE relname = '$table') as row_count
            "));

        return [
            'total_size' => $result[0]->total_size,
            'table_size' => $result[0]->table_size,
            'index_size' => $result[0]->index_size,
            'row_count' => $result[0]->row_count
        ];
    }

    public function getTableStats(string $table): array
    {
        $result = DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables 
                WHERE relname = '$table'
            "));

        return [
            'live_rows' => $result[0]->live_rows,
            'dead_rows' => $result[0]->dead_rows,
            'last_vacuum' => $result[0]->last_vacuum,
            'last_autovacuum' => $result[0]->last_autovacuum,
            'last_analyze' => $result[0]->last_analyze,
            'last_autoanalyze' => $result[0]->last_autoanalyze
        ];
    }

    public function optimizeTable(string $table): void
    {
        DB::connection($this->connection)
            ->select(DB::raw("VACUUM ANALYZE $table"));

        Log::info("Optimized table: {$table}");
    }

    public function analyzeTable(string $table): void
    {
        DB::connection($this->connection)
            ->select(DB::raw("ANALYZE $table"));

        Log::info("Analyzed table: {$table}");
    }

    public function getSlowQueries(int $limit = 10): Collection
    {
        return collect(DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    query,
                    calls,
                    total_time / 1000 as total_seconds,
                    (total_time / calls) / 1000 as avg_seconds,
                    rows
                FROM pg_stat_statements
                ORDER BY total_time DESC
                LIMIT $limit
            ")));
    }

    public function getQueryStats(): array
    {
        $result = DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    sum(calls) as total_calls,
                    sum(total_time) / 1000 as total_seconds,
                    sum(rows) as total_rows
                FROM pg_stat_statements
            "));

        return [
            'total_calls' => $result[0]->total_calls,
            'total_seconds' => $result[0]->total_seconds,
            'total_rows' => $result[0]->total_rows,
            'avg_seconds_per_call' => $result[0]->total_seconds / $result[0]->total_calls,
            'avg_rows_per_call' => $result[0]->total_rows / $result[0]->total_calls
        ];
    }

    public function resetQueryStats(): void
    {
        DB::connection($this->connection)
            ->select(DB::raw('SELECT pg_stat_statements_reset()'));

        Log::info('Reset query statistics');
    }

    public function getConnectionStats(): array
    {
        $result = DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    numbackends as active_connections,
                    xact_commit as commits,
                    xact_rollback as rollbacks,
                    blks_read,
                    blks_hit,
                    tup_returned as rows_returned,
                    tup_fetched as rows_fetched,
                    tup_inserted as rows_inserted,
                    tup_updated as rows_updated,
                    tup_deleted as rows_deleted
                FROM pg_stat_database 
                WHERE datname = current_database()
            "));

        return [
            'active_connections' => $result[0]->active_connections,
            'commits' => $result[0]->commits,
            'rollbacks' => $result[0]->rollbacks,
            'blocks_read' => $result[0]->blks_read,
            'blocks_hit' => $result[0]->blks_hit,
            'cache_hit_ratio' => $result[0]->blks_hit / ($result[0]->blks_read + $result[0]->blks_hit),
            'rows_returned' => $result[0]->rows_returned,
            'rows_fetched' => $result[0]->rows_fetched,
            'rows_inserted' => $result[0]->rows_inserted,
            'rows_updated' => $result[0]->rows_updated,
            'rows_deleted' => $result[0]->rows_deleted
        ];
    }

    public function killConnection(int $pid): void
    {
        DB::connection($this->connection)
            ->select(DB::raw("SELECT pg_terminate_backend($pid)"));

        Log::info("Killed connection: {$pid}");
    }

    public function getActiveConnections(): Collection
    {
        return collect(DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    pid,
                    usename as username,
                    application_name,
                    client_addr as client_address,
                    backend_start,
                    xact_start as transaction_start,
                    query_start,
                    state,
                    wait_event,
                    query
                FROM pg_stat_activity
                WHERE pid <> pg_backend_pid()
                AND state <> 'idle'
                ORDER BY query_start DESC
            ")));
    }

    public function getLocks(): Collection
    {
        return collect(DB::connection($this->connection)
            ->select(DB::raw("
                SELECT 
                    pid,
                    relname as table_name,
                    mode,
                    granted
                FROM pg_locks l
                JOIN pg_class c ON l.relation = c.oid
                WHERE relname NOT LIKE 'pg_%'
            ")));
    }
} 