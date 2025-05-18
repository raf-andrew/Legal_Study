<?php

namespace LegalStudy\ModularInitialization\Initializers;

use PDO;
use PDOException;
use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Services\DatabasePerformanceMonitor;
use LegalStudy\ModularInitialization\Services\InitializationPerformanceMonitor;
use InvalidArgumentException;
use RuntimeException;

class DatabaseInitialization extends AbstractInitialization
{
    private ?PDO $connection = null;
    private bool $inTransaction = false;
    private int $maxRetries = 3;
    private int $timeout = 30;
    protected InitializationPerformanceMonitor $performanceMonitor;
    private DatabasePerformanceMonitor $databasePerformanceMonitor;

    public function __construct()
    {
        parent::__construct();
        $this->databasePerformanceMonitor = new DatabasePerformanceMonitor();
        $this->performanceMonitor = new InitializationPerformanceMonitor();
    }

    protected function doValidateConfiguration(): void
    {
        $this->performanceMonitor->startMeasurement('DatabaseInitialization', 'validateConfiguration');
        try {
            if (empty($this->config['host'])) {
                throw new InvalidArgumentException('Database host is required');
            }
            if (empty($this->config['database'])) {
                throw new InvalidArgumentException('Database name is required');
            }
            if (empty($this->config['username'])) {
                throw new InvalidArgumentException('Database username is required');
            }
            if (!isset($this->config['port'])) {
                throw new InvalidArgumentException('Database port is required');
            }
        } finally {
            $this->performanceMonitor->endMeasurement('DatabaseInitialization', 'validateConfiguration');
        }
    }

    protected function doTestConnection(): bool
    {
        $this->performanceMonitor->startMeasurement('DatabaseInitialization', 'testConnection');
        $this->databasePerformanceMonitor->startConnectionMeasurement();
        try {
            $dsn = sprintf(
                'mysql:host=%s;port=%d;dbname=%s',
                $this->config['host'],
                $this->config['port'],
                $this->config['database']
            );
            $this->connection = new PDO(
                $dsn,
                $this->config['username'],
                $this->config['password'] ?? '',
                [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
            );
            return true;
        } catch (PDOException $e) {
            $this->addError('Failed to connect to database: ' . $e->getMessage());
            return false;
        } finally {
            $this->databasePerformanceMonitor->endConnectionMeasurement();
            $this->performanceMonitor->endMeasurement('DatabaseInitialization', 'testConnection');
        }
    }

    protected function doPerformInitialization(): void
    {
        $this->performanceMonitor->startMeasurement('DatabaseInitialization', 'performInitialization');
        try {
            if (!$this->connection) {
                throw new RuntimeException('No database connection available');
            }
            $this->beginTransaction();
            $this->createTables();
            $this->createIndexes();
            $this->insertInitialData();
            $this->commitTransaction();
        } catch (Exception $e) {
            $this->rollbackTransaction();
            throw new RuntimeException('Database initialization failed: ' . $e->getMessage());
        } finally {
            $this->performanceMonitor->endMeasurement('DatabaseInitialization', 'performInitialization');
        }
    }

    private function createPDOConnection(): void
    {
        if ($this->connection === null) {
            $dsn = sprintf(
                'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
                $this->config['host'],
                $this->config['port'],
                $this->config['dbname']
            );

            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_TIMEOUT => $this->timeout,
                PDO::ATTR_PERSISTENT => true
            ];

            $this->connection = new PDO(
                $dsn,
                $this->config['user'],
                $this->config['password'],
                $options
            );
        }
    }

    private function startTransaction(): void
    {
        if (!$this->inTransaction) {
            $this->performanceMonitor->startTransactionMeasurement();
            $this->connection->beginTransaction();
            $this->inTransaction = true;
        }
    }

    private function commitTransaction(): void
    {
        if ($this->inTransaction) {
            $this->connection->commit();
            $this->performanceMonitor->endTransactionMeasurement();
            $this->inTransaction = false;
        }
    }

    private function rollbackTransaction(): void
    {
        if ($this->inTransaction) {
            $this->connection->rollBack();
            $this->performanceMonitor->incrementRollbackCount();
            $this->inTransaction = false;
        }
    }

    private function createTables(): void
    {
        // Implementation specific to your database schema
        // This is a placeholder for actual table creation logic
    }

    private function createIndexes(): void
    {
        // Implementation specific to your database schema
        // This is a placeholder for actual index creation logic
    }

    private function insertInitialData(): void
    {
        // Implementation specific to your database schema
        // This is a placeholder for actual data insertion logic
    }

    public function getConnection(): PDO
    {
        if ($this->connection === null) {
            $this->createPDOConnection();
        }
        return $this->connection;
    }

    public function getDatabasePerformanceMonitor(): DatabasePerformanceMonitor
    {
        return $this->databasePerformanceMonitor;
    }
} 