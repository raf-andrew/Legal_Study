<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Initializers\DatabaseInitialization;
use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Initializers\QueueInitialization;
use LegalStudy\ModularInitialization\Initializers\ExternalApiInitialization;
use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use LegalStudy\ModularInitialization\Initializers\NetworkInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Services\InitializationPerformanceMonitor;
use PHPUnit\Framework\TestCase;

class InitializationFrameworkVerificationTest extends TestCase
{
    private array $initializationClasses = [
        DatabaseInitialization::class,
        CacheInitialization::class,
        QueueInitialization::class,
        ExternalApiInitialization::class,
        FileSystemInitialization::class,
        NetworkInitialization::class
    ];

    public function testAllInitializationClassesExtendAbstract(): void
    {
        foreach ($this->initializationClasses as $class) {
            $this->assertTrue(is_subclass_of($class, AbstractInitialization::class),
                "$class does not extend AbstractInitialization");
        }
    }

    public function testAllInitializationClassesHaveRequiredMethods(): void
    {
        $requiredMethods = [
            'performInitialization',
            'validateConfiguration',
            'testConnection'
        ];

        foreach ($this->initializationClasses as $class) {
            $reflection = new \ReflectionClass($class);
            foreach ($requiredMethods as $method) {
                $this->assertTrue($reflection->hasMethod($method),
                    "$class does not have required method $method");
                $this->assertTrue($reflection->getMethod($method)->isPublic(),
                    "$method in $class is not public");
            }
        }
    }

    public function testInitializationStatusFunctionality(): void
    {
        $status = new InitializationStatus();
        
        // Test initial state
        $this->assertEquals(InitializationStatus::PENDING, $status->getStatus());
        $this->assertTrue($status->isPending());
        $this->assertEmpty($status->getData());
        $this->assertEmpty($status->getErrors());
        $this->assertEmpty($status->getWarnings());
        
        // Test status transitions
        $status->setStatus(InitializationStatus::INITIALIZING);
        $this->assertTrue($status->isInitializing());
        
        $status->setStatus(InitializationStatus::INITIALIZED);
        $this->assertTrue($status->isInitialized());
        $this->assertTrue($status->isSuccess());
        
        // Test error handling
        $status->addError('Test error');
        $this->assertTrue($status->isFailed());
        $this->assertEquals(['Test error'], $status->getErrors());
        
        // Test data management
        $status->addData('key', 'value');
        $this->assertEquals(['key' => 'value'], $status->getData());
        
        // Create a new status for completion test
        $status = new InitializationStatus();
        $status->startTiming();
        $status->markComplete();
        $this->assertTrue($status->isComplete());
        $this->assertGreaterThan(0, $status->getDuration());
    }

    public function testInitializationPerformanceMonitoring(): void
    {
        $monitor = new InitializationPerformanceMonitor();
        $component = 'TestComponent';
        $operation = 'test_operation';
        
        // Test single measurement
        $monitor->startMeasurement($component, $operation);
        usleep(1000); // Sleep for 1ms
        $monitor->endMeasurement($component, $operation);
        
        $metrics = $monitor->getComponentMetrics($component);
        $this->assertGreaterThan(0, $metrics[$operation]['total_duration']);
        $this->assertEquals(1, $metrics[$operation]['count']);
        
        // Test multiple measurements
        $component2 = 'TestComponent2';
        $operation2 = 'test_operation2';
        
        $monitor->startMeasurement($component2, $operation2);
        usleep(1000);
        $monitor->endMeasurement($component2, $operation2);
        
        $monitor->startMeasurement($component2, $operation2);
        usleep(1000);
        $monitor->endMeasurement($component2, $operation2);
        
        $metrics = $monitor->getComponentMetrics($component2);
        $this->assertEquals(2, $metrics[$operation2]['count']);
        $this->assertGreaterThan(0, $metrics[$operation2]['total_duration']);
    }

    public function testInitializationErrorHandling(): void
    {
        $status = new InitializationStatus();
        
        // Test error collection
        $status->addError('Error 1');
        $status->addError('Error 2');
        $this->assertEquals(['Error 1', 'Error 2'], $status->getErrors());
        
        // Test error state
        $this->assertTrue($status->isFailed());
        $this->assertFalse($status->isSuccess());
        
        // Test warning handling
        $status->addWarning('Warning 1');
        $this->assertEquals(['Warning 1'], $status->getWarnings());
    }

    public function testInitializationDataManagement(): void
    {
        $status = new InitializationStatus();
        
        // Test data addition
        $status->addData('key1', 'value1');
        $status->addData('key2', 'value2');
        $this->assertEquals(['key1' => 'value1', 'key2' => 'value2'], $status->getData());
        
        // Test data setting
        $newData = ['key3' => 'value3'];
        $status->setData($newData);
        $this->assertEquals($newData, $status->getData());
    }

    public function testInitializationStateTransitions(): void
    {
        $status = new InitializationStatus();
        
        // Test all possible state transitions
        $states = [
            InitializationStatus::PENDING,
            InitializationStatus::INITIALIZING,
            InitializationStatus::INITIALIZED,
            InitializationStatus::FAILED,
            InitializationStatus::ERROR,
            InitializationStatus::COMPLETE,
            InitializationStatus::INCOMPLETE,
            InitializationStatus::UNKNOWN
        ];
        
        foreach ($states as $state) {
            $status->setStatus($state);
            $this->assertEquals($state, $status->getStatus());
        }
    }
} 