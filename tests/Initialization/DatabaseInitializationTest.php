<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\DatabaseInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Services\InitializationPerformanceMonitor;
use PHPUnit\Framework\TestCase;
use PDO;
use PDOStatement;

/**
 * @covers \LegalStudy\ModularInitialization\Initializers\DatabaseInitialization
 * @covers \LegalStudy\ModularInitialization\AbstractInitialization
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 * @covers \LegalStudy\ModularInitialization\Services\InitializationPerformanceMonitor
 */
class DatabaseInitializationTest extends TestCase
{
    private DatabaseInitialization $initialization;
    private PDO $pdoMock;
    private PDOStatement $statementMock;

    protected function setUp(): void
    {
        $this->pdoMock = $this->createMock(PDO::class);
        $this->statementMock = $this->createMock(PDOStatement::class);
        
        $this->initialization = $this->getMockBuilder(DatabaseInitialization::class)
            ->onlyMethods(['createPDOConnection'])
            ->getMock();
            
        $this->initialization->method('createPDOConnection')
            ->willReturn($this->pdoMock);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doValidateConfiguration
     * @covers \LegalStudy\Initialization\AbstractInitialization::validateConfiguration
     * @covers \LegalStudy\Initialization\InitializationStatus::startTiming
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     */
    public function testValidateConfiguration(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->getStatus()->isPending());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createDsn
     * @covers \LegalStudy\Initialization\DatabaseInitialization::getConnectionOptions
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createPDOConnection
     * @covers \LegalStudy\Initialization\AbstractInitialization::testConnection
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     */
    public function testTestConnection(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('query')
            ->with('SELECT 1')
            ->willReturn($this->statementMock);

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->testConnection());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doPerformInitialization
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createDsn
     * @covers \LegalStudy\Initialization\DatabaseInitialization::getConnectionOptions
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createPDOConnection
     * @covers \LegalStudy\Initialization\AbstractInitialization::performInitialization
     * @covers \LegalStudy\Initialization\InitializationStatus::markInitialized
     * @covers \LegalStudy\Initialization\InitializationStatus::isInitialized
     * @covers \LegalStudy\Initialization\InitializationStatus::getData
     * @covers \LegalStudy\Initialization\InitializationStatus::addData
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     */
    public function testPerformInitialization(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('getAttribute')
            ->with(PDO::ATTR_SERVER_VERSION)
            ->willReturn('8.0.0');

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->assertTrue($this->initialization->getStatus()->isInitialized());
        $this->assertEquals(['connected' => true, 'version' => '8.0.0'], $this->initialization->getStatus()->getData());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createDsn
     * @covers \LegalStudy\Initialization\DatabaseInitialization::getConnectionOptions
     * @covers \LegalStudy\Initialization\DatabaseInitialization::createPDOConnection
     * @covers \LegalStudy\Initialization\AbstractInitialization::testConnection
     * @covers \LegalStudy\Initialization\InitializationStatus::isFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     */
    public function testErrorHandling(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('query')
            ->with('SELECT 1')
            ->willThrowException(new \PDOException('Connection failed'));

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        
        try {
            $this->initialization->testConnection();
            $this->fail('Expected RuntimeException was not thrown');
        } catch (\RuntimeException $e) {
            $this->assertEquals('Connection test failed', $e->getMessage());
            $this->assertTrue($this->initialization->getStatus()->isFailed());
            $this->assertNotEmpty($this->initialization->getStatus()->getErrors());
        }
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doValidateConfiguration
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doPerformInitialization
     */
    public function testTimeoutConfiguration(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'timeout' => 5
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->getStatus()->isPending());

        $this->pdoMock->expects($this->once())
            ->method('setAttribute')
            ->with(PDO::ATTR_TIMEOUT, 5);

        $this->pdoMock->expects($this->once())
            ->method('query')
            ->with('SELECT 1')
            ->willReturn($this->statementMock);

        $this->assertTrue($this->initialization->testConnection());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doValidateConfiguration
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doPerformInitialization
     */
    public function testRetryConfiguration(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'retry_attempts' => 2,
            'retry_delay' => 0.1
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->getStatus()->isPending());

        $this->pdoMock->expects($this->exactly(3))
            ->method('query')
            ->with('SELECT 1')
            ->willThrowException(new \PDOException('Connection failed'));

        $this->assertFalse($this->initialization->testConnection());
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertCount(3, $this->initialization->getStatus()->getErrors());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doValidateConfiguration
     */
    public function testInvalidTimeoutConfiguration(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'timeout' => -1
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid timeout value', $this->initialization->getStatus()->getErrors()[0]);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doValidateConfiguration
     */
    public function testInvalidRetryConfiguration(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'retry_attempts' => -1,
            'retry_delay' => -0.1
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid retry attempts value', $this->initialization->getStatus()->getErrors()[0]);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::beginTransaction
     * @covers \LegalStudy\Initialization\DatabaseInitialization::isInTransaction
     */
    public function testBeginTransaction(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('beginTransaction')
            ->willReturn(true);

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->assertTrue($this->initialization->beginTransaction());
        $this->assertTrue($this->initialization->isInTransaction());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::beginTransaction
     */
    public function testBeginTransactionWithoutConnection(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('No database connection available');
        $this->initialization->beginTransaction();
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::beginTransaction
     */
    public function testBeginTransactionAlreadyInProgress(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('beginTransaction')
            ->willReturn(true);

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();
        $this->initialization->beginTransaction();

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Transaction already in progress');
        $this->initialization->beginTransaction();
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::commit
     * @covers \LegalStudy\Initialization\DatabaseInitialization::isInTransaction
     */
    public function testCommitTransaction(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('beginTransaction')
            ->willReturn(true);

        $this->pdoMock->expects($this->once())
            ->method('commit')
            ->willReturn(true);

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();
        $this->initialization->beginTransaction();

        $this->assertTrue($this->initialization->commit());
        $this->assertFalse($this->initialization->isInTransaction());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::commit
     */
    public function testCommitWithoutTransaction(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('No transaction in progress');
        $this->initialization->commit();
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::rollback
     * @covers \LegalStudy\Initialization\DatabaseInitialization::isInTransaction
     */
    public function testRollbackTransaction(): void
    {
        $this->pdoMock->expects($this->once())
            ->method('beginTransaction')
            ->willReturn(true);

        $this->pdoMock->expects($this->once())
            ->method('rollBack')
            ->willReturn(true);

        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();
        $this->initialization->beginTransaction();

        $this->assertTrue($this->initialization->rollback());
        $this->assertFalse($this->initialization->isInTransaction());
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::rollback
     */
    public function testRollbackWithoutTransaction(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('No transaction in progress');
        $this->initialization->rollback();
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithMaxRetries(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'retry_attempts' => 1,
            'retry_delay' => 0.1
        ];

        $this->pdoMock->expects($this->exactly(2))
            ->method('query')
            ->with('SELECT 1')
            ->willThrowException(new \PDOException('Connection failed'));

        $this->initialization->validateConfiguration($config);
        $this->assertFalse($this->initialization->testConnection());
        $this->assertEquals(2, count($this->initialization->getStatus()->getErrors()));
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithZeroRetries(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'retry_attempts' => 0
        ];

        $this->pdoMock->expects($this->once())
            ->method('query')
            ->with('SELECT 1')
            ->willThrowException(new \PDOException('Connection failed'));

        $this->initialization->validateConfiguration($config);
        $this->assertFalse($this->initialization->testConnection());
        $this->assertEquals(1, count($this->initialization->getStatus()->getErrors()));
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithZeroTimeout(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass',
            'timeout' => 0
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid timeout value', $this->initialization->getStatus()->getErrors()[0]);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithInvalidPort(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => -1,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Invalid port value', $this->initialization->getStatus()->getErrors()[0]);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithEmptyHost(): void
    {
        $config = [
            'host' => '',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Host cannot be empty', $this->initialization->getStatus()->getErrors()[0]);
    }

    /**
     * @covers \LegalStudy\Initialization\DatabaseInitialization::doTestConnection
     */
    public function testConnectionWithEmptyDatabase(): void
    {
        $config = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => '',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        $this->assertFalse($this->initialization->validateConfiguration($config));
        $this->assertTrue($this->initialization->getStatus()->isFailed());
        $this->assertStringContainsString('Database name cannot be empty', $this->initialization->getStatus()->getErrors()[0]);
    }
} 