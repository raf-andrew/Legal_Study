<?php

namespace LegalStudy\Initialization;

class DatabaseInitialization extends AbstractInitialization
{
    private ?\PDO $connection = null;
    private int $timeout = 30; // Default timeout in seconds
    private int $maxRetries = 3; // Default max retries
    private float $retryDelay = 1.0; // Default delay between retries in seconds
    private bool $inTransaction = false;

    protected function doValidateConfiguration(): bool
    {
        $required = ['host', 'port', 'database', 'username', 'password'];
        
        foreach ($required as $field) {
            if (!isset($this->config[$field])) {
                $this->addError("Database {$field} is required");
                return false;
            }
        }

        // Validate timeout if provided
        if (isset($this->config['timeout'])) {
            if (!is_int($this->config['timeout']) || $this->config['timeout'] <= 0) {
                $this->addError("Invalid timeout value");
                return false;
            }
            $this->timeout = $this->config['timeout'];
        }

        // Validate retry settings if provided
        if (isset($this->config['retry_attempts'])) {
            if (!is_int($this->config['retry_attempts']) || $this->config['retry_attempts'] < 0) {
                $this->addError("Invalid retry attempts value");
                return false;
            }
            $this->maxRetries = $this->config['retry_attempts'];
        }

        if (isset($this->config['retry_delay'])) {
            if (!is_float($this->config['retry_delay']) || $this->config['retry_delay'] < 0) {
                $this->addError("Invalid retry delay value");
                return false;
            }
            $this->retryDelay = $this->config['retry_delay'];
        }

        return true;
    }

    protected function doTestConnection(): bool
    {
        $attempt = 0;
        $lastException = null;

        while ($attempt <= $this->maxRetries) {
            try {
                $dsn = $this->createDsn(false);
                $options = $this->getConnectionOptions();

                $connection = $this->createPDOConnection(
                    $dsn,
                    $this->config['username'],
                    $this->config['password'],
                    $options
                );

                $connection->setAttribute(\PDO::ATTR_TIMEOUT, $this->timeout);
                $result = $connection->query('SELECT 1');
                
                if ($result === false) {
                    $this->addError('Failed to execute test query');
                    return false;
                }

                $connection = null;
                return true;
            } catch (\PDOException $e) {
                $lastException = $e;
                $attempt++;
                
                if ($attempt <= $this->maxRetries) {
                    $this->addError(sprintf(
                        'Connection attempt %d failed: %s. Retrying in %.1f seconds...',
                        $attempt,
                        $e->getMessage(),
                        $this->retryDelay
                    ));
                    usleep((int)($this->retryDelay * 1000000));
                }
            }
        }

        $this->addError('Database connection test failed: ' . $lastException->getMessage());
        return false;
    }

    protected function doPerformInitialization(): void
    {
        $attempt = 0;
        $lastException = null;

        while ($attempt <= $this->maxRetries) {
            try {
                $dsn = $this->createDsn(true);
                $options = $this->getConnectionOptions();

                $this->connection = $this->createPDOConnection(
                    $dsn,
                    $this->config['username'],
                    $this->config['password'],
                    $options
                );

                $this->connection->setAttribute(\PDO::ATTR_TIMEOUT, $this->timeout);
                $this->addData('connected', true);
                $this->addData('version', $this->connection->getAttribute(\PDO::ATTR_SERVER_VERSION));
                return;
            } catch (\PDOException $e) {
                $lastException = $e;
                $attempt++;
                
                if ($attempt <= $this->maxRetries) {
                    $this->addError(sprintf(
                        'Initialization attempt %d failed: %s. Retrying in %.1f seconds...',
                        $attempt,
                        $e->getMessage(),
                        $this->retryDelay
                    ));
                    usleep((int)($this->retryDelay * 1000000));
                }
            }
        }

        $this->connection = null;
        throw new \RuntimeException('Database initialization failed: ' . $lastException->getMessage());
    }

    protected function createDsn(bool $includeDatabase): string
    {
        $dsn = sprintf(
            'mysql:host=%s;port=%d;charset=utf8mb4',
            $this->config['host'],
            $this->config['port']
        );

        if ($includeDatabase) {
            $dsn .= ';dbname=' . $this->config['database'];
        }

        return $dsn;
    }

    protected function getConnectionOptions(): array
    {
        return [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            \PDO::ATTR_EMULATE_PREPARES => false,
        ];
    }

    protected function createPDOConnection(string $dsn, string $username, string $password, array $options): \PDO
    {
        return new \PDO($dsn, $username, $password, $options);
    }

    public function getConnection(): ?\PDO
    {
        return $this->connection;
    }

    public function beginTransaction(): bool
    {
        if ($this->connection === null) {
            throw new \RuntimeException('No database connection available');
        }

        if ($this->inTransaction) {
            throw new \RuntimeException('Transaction already in progress');
        }

        try {
            $this->inTransaction = $this->connection->beginTransaction();
            return $this->inTransaction;
        } catch (\PDOException $e) {
            throw new \RuntimeException('Failed to begin transaction: ' . $e->getMessage());
        }
    }

    public function commit(): bool
    {
        if ($this->connection === null) {
            throw new \RuntimeException('No database connection available');
        }

        if (!$this->inTransaction) {
            throw new \RuntimeException('No transaction in progress');
        }

        try {
            $result = $this->connection->commit();
            $this->inTransaction = false;
            return $result;
        } catch (\PDOException $e) {
            throw new \RuntimeException('Failed to commit transaction: ' . $e->getMessage());
        }
    }

    public function rollback(): bool
    {
        if ($this->connection === null) {
            throw new \RuntimeException('No database connection available');
        }

        if (!$this->inTransaction) {
            throw new \RuntimeException('No transaction in progress');
        }

        try {
            $result = $this->connection->rollBack();
            $this->inTransaction = false;
            return $result;
        } catch (\PDOException $e) {
            throw new \RuntimeException('Failed to rollback transaction: ' . $e->getMessage());
        }
    }

    public function isInTransaction(): bool
    {
        return $this->inTransaction;
    }

    public function __destruct()
    {
        if ($this->inTransaction) {
            $this->rollback();
        }
        $this->connection = null;
    }
} 