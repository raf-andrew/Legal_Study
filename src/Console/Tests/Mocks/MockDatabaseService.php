<?php

namespace LegalStudy\Console\Tests\Mocks;

class MockDatabaseService extends AbstractMockService
{
    private array $tables = [];
    private array $queries = [];
    private int $queryCount = 0;
    private float $queryTime = 0.0;

    public function __construct(array $config = [])
    {
        parent::__construct('database', $config);
        $this->reset();
    }

    public function reset(): void
    {
        parent::reset();
        $this->tables = [];
        $this->queries = [];
        $this->queryCount = 0;
        $this->queryTime = 0.0;
        $this->updateStatus();
    }

    public function getStatus(): array
    {
        return array_merge(parent::getStatus(), [
            'tables' => count($this->tables),
            'queries' => $this->queryCount,
            'query_time' => $this->queryTime,
            'last_query' => end($this->queries) ?: null
        ]);
    }

    public function createTable(string $name, array $columns): void
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (isset($this->tables[$name])) {
            throw new \RuntimeException("Table '{$name}' already exists");
        }

        $this->tables[$name] = [
            'columns' => $columns,
            'data' => []
        ];

        $this->updateStatus();
    }

    public function dropTable(string $name): void
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (!isset($this->tables[$name])) {
            throw new \RuntimeException("Table '{$name}' does not exist");
        }

        unset($this->tables[$name]);
        $this->updateStatus();
    }

    public function insert(string $table, array $data): int
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (!isset($this->tables[$table])) {
            throw new \RuntimeException("Table '{$table}' does not exist");
        }

        $id = count($this->tables[$table]['data']) + 1;
        $this->tables[$table]['data'][$id] = $data;
        $this->logQuery("INSERT INTO {$table}", $data);

        return $id;
    }

    public function select(string $table, array $conditions = []): array
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (!isset($this->tables[$table])) {
            throw new \RuntimeException("Table '{$table}' does not exist");
        }

        $this->logQuery("SELECT FROM {$table}", $conditions);
        return $this->filterData($this->tables[$table]['data'], $conditions);
    }

    public function update(string $table, array $data, array $conditions = []): int
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (!isset($this->tables[$table])) {
            throw new \RuntimeException("Table '{$table}' does not exist");
        }

        $this->logQuery("UPDATE {$table}", array_merge($data, $conditions));
        $affected = 0;

        foreach ($this->tables[$table]['data'] as $id => $row) {
            if ($this->matchesConditions($row, $conditions)) {
                $this->tables[$table]['data'][$id] = array_merge($row, $data);
                $affected++;
            }
        }

        return $affected;
    }

    public function delete(string $table, array $conditions = []): int
    {
        $this->throwIfDisabled();
        $this->throwIfShouldFail();

        if (!isset($this->tables[$table])) {
            throw new \RuntimeException("Table '{$table}' does not exist");
        }

        $this->logQuery("DELETE FROM {$table}", $conditions);
        $affected = 0;

        foreach ($this->tables[$table]['data'] as $id => $row) {
            if ($this->matchesConditions($row, $conditions)) {
                unset($this->tables[$table]['data'][$id]);
                $affected++;
            }
        }

        return $affected;
    }

    private function logQuery(string $type, array $data): void
    {
        $this->queries[] = [
            'type' => $type,
            'data' => $data,
            'timestamp' => microtime(true)
        ];
        $this->queryCount++;
        $this->queryTime += 0.001; // Simulate query time
        $this->updateStatus();
    }

    private function filterData(array $data, array $conditions): array
    {
        return array_filter($data, function ($row) use ($conditions) {
            return $this->matchesConditions($row, $conditions);
        });
    }

    private function matchesConditions(array $row, array $conditions): bool
    {
        foreach ($conditions as $key => $value) {
            if (!isset($row[$key]) || $row[$key] !== $value) {
                return false;
            }
        }
        return true;
    }
} 