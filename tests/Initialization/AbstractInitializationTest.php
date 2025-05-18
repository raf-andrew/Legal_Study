<?php

namespace Tests\Initialization;

use LegalStudy\Initialization\AbstractInitialization;
use LegalStudy\Initialization\InitializationStatus;
use LegalStudy\Initialization\InitializationPerformanceMonitor;
use PHPUnit\Framework\TestCase;

/**
 * @covers \LegalStudy\Initialization\AbstractInitialization
 * @covers \LegalStudy\Initialization\InitializationStatus
 * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor
 */
class AbstractInitializationTest extends TestCase
{
    private AbstractInitialization $initialization;

    protected function setUp(): void
    {
        $this->initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        $this->initialization->method('doValidateConfiguration')->willReturn(true);
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::__construct
     * @covers \LegalStudy\Initialization\AbstractInitialization::getStatus
     * @covers \LegalStudy\Initialization\InitializationStatus::__construct
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     * @covers \LegalStudy\Initialization\InitializationStatus::getWarnings
     * @covers \LegalStudy\Initialization\InitializationStatus::getData
     */
    public function testInitialState(): void
    {
        $this->assertInstanceOf(InitializationStatus::class, $this->initialization->getStatus());
        $this->assertTrue($this->initialization->getStatus()->isPending());
        $this->assertEquals(InitializationStatus::PENDING, $this->initialization->getStatus()->getStatus());
        $this->assertEmpty($this->initialization->getStatus()->getErrors());
        $this->assertEmpty($this->initialization->getStatus()->getWarnings());
        $this->assertEmpty($this->initialization->getStatus()->getData());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::setStatus
     * @covers \LegalStudy\Initialization\InitializationStatus::setStatus
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testSetStatus(): void
    {
        $status = new InitializationStatus();
        $status->setStatus(InitializationStatus::INITIALIZING);
        
        $this->initialization->setStatus($status);
        $this->assertEquals($status, $this->initialization->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::addError
     * @covers \LegalStudy\Initialization\AbstractInitialization::testAddError
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::hasErrors
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testAddError(): void
    {
        $this->initialization->testAddError('Test error');
        $this->assertTrue($this->initialization->getStatus()->hasErrors());
        $this->assertContains('Test error', $this->initialization->getStatus()->getErrors());
        $this->assertEquals(InitializationStatus::FAILED, $this->initialization->getStatus()->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::addWarning
     * @covers \LegalStudy\Initialization\AbstractInitialization::testAddWarning
     * @covers \LegalStudy\Initialization\InitializationStatus::addWarning
     * @covers \LegalStudy\Initialization\InitializationStatus::hasWarnings
     * @covers \LegalStudy\Initialization\InitializationStatus::getWarnings
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testAddWarning(): void
    {
        $this->initialization->testAddWarning('Test warning');
        $this->assertTrue($this->initialization->getStatus()->hasWarnings());
        $this->assertContains('Test warning', $this->initialization->getStatus()->getWarnings());
        $this->assertEquals(InitializationStatus::PENDING, $this->initialization->getStatus()->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::markComplete
     * @covers \LegalStudy\Initialization\AbstractInitialization::testMarkComplete
     * @covers \LegalStudy\Initialization\InitializationStatus::markComplete
     * @covers \LegalStudy\Initialization\InitializationStatus::isComplete
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testMarkComplete(): void
    {
        $this->initialization->testMarkComplete();
        $this->assertTrue($this->initialization->getStatus()->isComplete());
        $this->assertEquals(InitializationStatus::COMPLETE, $this->initialization->getStatus()->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::validateConfiguration
     * @covers \LegalStudy\Initialization\AbstractInitialization::getConfig
     * @covers \LegalStudy\Initialization\AbstractInitialization::doValidateConfiguration
     * @covers \LegalStudy\Initialization\InitializationStatus::startTiming
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     */
    public function testValidateConfiguration(): void
    {
        $config = ['key' => 'value'];
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doValidateConfiguration')
            ->willReturn(true);
            
        $initialization->validateConfiguration($config);
        $this->assertEquals($config, $initialization->getConfig());
        $this->assertEmpty($initialization->getStatus()->getErrors());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::validateConfiguration
     * @covers \LegalStudy\Initialization\AbstractInitialization::doValidateConfiguration
     * @covers \LegalStudy\Initialization\InitializationStatus::startTiming
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     */
    public function testValidateConfigurationFailure(): void
    {
        $config = ['key' => 'value'];
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doValidateConfiguration')
            ->willReturn(false);
            
        $this->expectException(\RuntimeException::class);
        $initialization->validateConfiguration($config);
        
        $this->assertNotEmpty($initialization->getStatus()->getErrors());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::testConnection
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testTestConnection(): void
    {
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doTestConnection')
            ->willReturn(true);
            
        $this->assertTrue($initialization->testConnection());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::testConnection
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     * @covers \LegalStudy\Initialization\InitializationStatus::getStatus
     */
    public function testTestConnectionFailure(): void
    {
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doTestConnection')
            ->willReturn(false);
            
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Connection test failed');
        
        $initialization->testConnection();
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::performInitialization
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     * @covers \LegalStudy\Initialization\InitializationStatus::markInitialized
     */
    public function testPerformInitialization(): void
    {
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doPerformInitialization');
            
        $initialization->performInitialization();
        $this->assertEquals(InitializationStatus::INITIALIZED, $initialization->getStatus()->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\AbstractInitialization::performInitialization
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::startMeasurement
     * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor::endMeasurement
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     * @covers \LegalStudy\Initialization\InitializationStatus::markFailed
     */
    public function testPerformInitializationFailure(): void
    {
        $initialization = $this->getMockForAbstractClass(AbstractInitialization::class);
        
        $initialization->expects($this->once())
            ->method('doPerformInitialization')
            ->willThrowException(new \RuntimeException('Initialization failed'));
            
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Initialization failed');
        
        $initialization->performInitialization();
        $this->assertEquals(InitializationStatus::FAILED, $initialization->getStatus()->getStatus());
    }

    public function testGetConfig(): void
    {
        $config = ['key' => 'value'];
        $this->initialization->validateConfiguration($config);
        $this->assertEquals($config, $this->initialization->getConfig());
    }
} 