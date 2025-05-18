<?php

namespace Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\DatabaseInitialization;
use PHPUnit\Framework\TestCase;

class DatabaseInitializationIntegrationTest extends TestCase
{
    private DatabaseInitialization $initialization;
    private array $config;

    protected function setUp(): void
    {
        $this->config = [
            'host' => getenv('DB_HOST') ?: 'localhost',
            'port' => (int)(getenv('DB_PORT') ?: 3306),
            'database' => getenv('DB_NAME') ?: 'test_db',
            'username' => getenv('DB_USER') ?: 'test_user',
            'password' => getenv('DB_PASS') ?: 'test_pass',
            'timeout' => (int)(getenv('DB_TIMEOUT') ?: 5),
            'retry_attempts' => (int)(getenv('DB_RETRY_ATTEMPTS') ?: 3),
            'retry_delay' => (float)(getenv('DB_RETRY_DELAY') ?: 1.0)
        ];

        $this->initialization = new DatabaseInitialization();
    }

    public function testDatabaseConnection(): void
    {
        $this->assertTrue($this->initialization->validateConfiguration($this->config));
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testDatabaseInitialization(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isInitialized());
        $this->assertEmpty($status->getErrors());
    }

    public function testDatabaseOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $connection = $this->initialization->getConnection();
        
        // Test table creation
        $connection->exec('CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, name VARCHAR(255))');
        
        // Test insert
        $stmt = $connection->prepare('INSERT INTO test_table (id, name) VALUES (?, ?)');
        $stmt->execute([1, 'test']);
        
        // Test select
        $stmt = $connection->prepare('SELECT name FROM test_table WHERE id = ?');
        $stmt->execute([1]);
        $result = $stmt->fetch(\PDO::FETCH_ASSOC);
        
        $this->assertEquals('test', $result['name']);
        
        // Cleanup
        $connection->exec('DROP TABLE IF EXISTS test_table');
    }

    public function testErrorHandling(): void
    {
        $invalidConfig = array_merge($this->config, [
            'password' => 'wrong_password'
        ]);

        $this->initialization->validateConfiguration($invalidConfig);
        $this->initialization->performInitialization();

        $status = $this->initialization->getStatus();
        $this->assertTrue($status->isFailed());
        $this->assertNotEmpty($status->getErrors());
    }

    public function testTimeoutHandling(): void
    {
        $timeoutConfig = array_merge($this->config, [
            'timeout' => 1 // Very short timeout
        ]);

        $this->initialization->validateConfiguration($timeoutConfig);
        
        try {
            $this->initialization->testConnection();
            $this->fail('Expected timeout exception was not thrown');
        } catch (\RuntimeException $e) {
            $this->assertStringContainsString('timeout', strtolower($e->getMessage()));
        }
    }

    public function testRetryHandling(): void
    {
        $retryConfig = array_merge($this->config, [
            'retry_attempts' => 2,
            'retry_delay' => 0.1
        ]);

        $this->initialization->validateConfiguration($retryConfig);
        
        // Simulate temporary connection failure
        $this->initialization->testConnection();
        
        $status = $this->initialization->getStatus();
        if ($status->isFailed()) {
            $errors = $status->getErrors();
            $this->assertGreaterThan(1, count($errors), 'Should have multiple retry attempts');
            $this->assertStringContainsString('retrying', strtolower($errors[0]));
        }
    }

    public function testInvalidTimeoutConfiguration(): void
    {
        $invalidConfig = array_merge($this->config, [
            'timeout' => -1
        ]);

        $this->assertFalse($this->initialization->validateConfiguration($invalidConfig));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid timeout value', $this->initialization->getStatus()->getErrors()[0]);
    }

    public function testInvalidRetryConfiguration(): void
    {
        $invalidConfig = array_merge($this->config, [
            'retry_attempts' => -1,
            'retry_delay' => -0.1
        ]);

        $this->assertFalse($this->initialization->validateConfiguration($invalidConfig));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid retry attempts value', $this->initialization->getStatus()->getErrors()[0]);
    }

    public function testTransactionOperations(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $connection = $this->initialization->getConnection();
        
        // Create test table
        $connection->exec('CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, name VARCHAR(255))');
        
        // Start transaction
        $this->assertTrue($this->initialization->beginTransaction());
        $this->assertTrue($this->initialization->isInTransaction());
        
        // Insert data
        $stmt = $connection->prepare('INSERT INTO test_table (id, name) VALUES (?, ?)');
        $stmt->execute([1, 'test']);
        
        // Verify data is not visible to other connections
        $otherConnection = new \PDO(
            $this->initialization->createDsn(true),
            $this->config['username'],
            $this->config['password']
        );
        $stmt = $otherConnection->prepare('SELECT name FROM test_table WHERE id = ?');
        $stmt->execute([1]);
        $this->assertFalse($stmt->fetch());
        
        // Commit transaction
        $this->assertTrue($this->initialization->commit());
        $this->assertFalse($this->initialization->isInTransaction());
        
        // Verify data is now visible
        $stmt = $otherConnection->prepare('SELECT name FROM test_table WHERE id = ?');
        $stmt->execute([1]);
        $result = $stmt->fetch(\PDO::FETCH_ASSOC);
        $this->assertEquals('test', $result['name']);
    }

    public function testTransactionRollback(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        $connection = $this->initialization->getConnection();
        
        // Create test table
        $connection->exec('CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, name VARCHAR(255))');
        
        // Start transaction
        $this->assertTrue($this->initialization->beginTransaction());
        
        // Insert data
        $stmt = $connection->prepare('INSERT INTO test_table (id, name) VALUES (?, ?)');
        $stmt->execute([1, 'test']);
        
        // Rollback transaction
        $this->assertTrue($this->initialization->rollback());
        $this->assertFalse($this->initialization->isInTransaction());
        
        // Verify data was not committed
        $stmt = $connection->prepare('SELECT name FROM test_table WHERE id = ?');
        $stmt->execute([1]);
        $this->assertFalse($stmt->fetch());
    }

    public function testTransactionErrorHandling(): void
    {
        $this->initialization->validateConfiguration($this->config);
        $this->initialization->performInitialization();

        // Try to commit without starting a transaction
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('No transaction in progress');
        $this->initialization->commit();
    }

    protected function tearDown(): void
    {
        if ($this->initialization->getStatus()->isInitialized()) {
            $connection = $this->initialization->getConnection();
            $connection->exec('DROP TABLE IF EXISTS test_table');
        }
    }
} 