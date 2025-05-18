<?php

namespace LegalStudy\ModularInitialization\Tests\Unit;

use LegalStudy\ModularInitialization\Contracts\InitializationInterface;
use LegalStudy\ModularInitialization\Services\InitializationStateManager;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use Orchestra\Testbench\TestCase;

/**
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 */
class InitializationStateManagerTest extends TestCase
{
    private InitializationStateManager $manager;
    private InitializationInterface $initialization;
    private InitializationStatus $status;

    protected function setUp(): void
    {
        parent::setUp();
        $this->status = new InitializationStatus();
        $this->manager = new InitializationStateManager($this->status);
        $this->initialization = $this->createMock(InitializationInterface::class);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     */
    public function testRegisterInitialization(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $state = $this->manager->getState(get_class($this->initialization));
        
        $this->assertInstanceOf(InitializationStatus::class, $state['status']);
        $this->assertInstanceOf(InitializationInterface::class, $state['instance']);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addError
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addWarning
     */
    public function testRegisterInitializationWithDependencies(): void
    {
        $dependency = $this->createMock(InitializationInterface::class);
        $this->manager->registerInitialization($dependency);
        $this->manager->registerInitialization($this->initialization, [get_class($dependency)]);

        $dependencies = $this->manager->getDependencies(get_class($this->initialization));
        $this->assertEquals([get_class($dependency)], $dependencies);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::updateState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::setStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     */
    public function testUpdateState(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $status = new InitializationStatus();
        $status->setStatus(InitializationStatus::COMPLETE);

        $this->manager->updateState(get_class($this->initialization), $status);
        $state = $this->manager->getState(get_class($this->initialization));
        
        $this->assertEquals(InitializationStatus::COMPLETE, $state['status']->getStatus());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::updateState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     */
    public function testUpdateStateForUnregisteredInitialization(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->manager->updateState('NonExistentClass', new InitializationStatus());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getState
     */
    public function testGetStateForUnregisteredInitialization(): void
    {
        $this->expectException(\RuntimeException::class);
        $this->manager->getState('NonExistentClass');
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::isInitializationComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::updateState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::markComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::setStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addError
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addWarning
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::reset
     */
    public function testIsInitializationComplete(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $status = new InitializationStatus();
        $status->markComplete();

        $this->manager->updateState(get_class($this->initialization), $status);
        $this->assertTrue($this->manager->isInitializationComplete(get_class($this->initialization)));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::isAllComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::updateState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::markComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     */
    public function testIsAllComplete(): void
    {
        $init1 = $this->createMock(InitializationInterface::class);
        $init2 = $this->createMock(InitializationInterface::class);

        $this->manager->registerInitialization($init1);
        $this->manager->registerInitialization($init2);

        $status = new InitializationStatus();
        $status->markComplete();

        $this->manager->updateState(get_class($init1), $status);
        $this->manager->updateState(get_class($init2), $status);

        $this->assertTrue($this->manager->isAllComplete());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitializationOrder
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     */
    public function testGetInitializationOrder(): void
    {
        $init1 = $this->createMock(InitializationInterface::class);
        $init2 = $this->createMock(InitializationInterface::class);

        // Register init1 with no dependencies
        $this->manager->registerInitialization($init1);
        
        // Register init2 with init1 as dependency
        $this->manager->registerInitialization($init2, [get_class($init1)]);

        $order = $this->manager->getInitializationOrder();
        
        // The order should be init1 -> init2 since init2 depends on init1
        $this->assertEquals(
            [get_class($init1), get_class($init2)],
            $order,
            'Initialization order should reflect dependency chain'
        );
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitializationOrder
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     */
    public function testCircularDependencyDetection(): void
    {
        $init1 = $this->createMock(InitializationInterface::class);
        $init2 = $this->createMock(InitializationInterface::class);

        $this->manager->registerInitialization($init1, [get_class($init2)]);
        $this->manager->registerInitialization($init2, [get_class($init1)]);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Circular dependency detected');
        $this->manager->getInitializationOrder();
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     */
    public function testGetDependenciesForInitializationWithoutDependencies(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $dependencies = $this->manager->getDependencies(get_class($this->initialization));
        $this->assertEmpty($dependencies);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::hasDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     */
    public function testHasDependencies(): void
    {
        $init1 = $this->createMock(InitializationInterface::class);
        $init2 = $this->createMock(InitializationInterface::class);

        // Register init1 with no dependencies
        $this->manager->registerInitialization($init1);
        
        // Register init2 with init1 as dependency
        $this->manager->registerInitialization($init2, [get_class($init1)]);

        // init1 should have no dependencies
        $this->assertFalse($this->manager->hasDependencies(get_class($init1)), 'init1 should have no dependencies');
        
        // init2 should have dependencies
        $this->assertTrue($this->manager->hasDependencies(get_class($init2)), 'init2 should have dependencies');

        // Test non-existent class
        $this->expectException(\RuntimeException::class);
        $this->manager->hasDependencies('NonExistentClass');
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::hasWarnings
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     */
    public function testGetInitialization(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $instance = $this->manager->getInitialization(get_class($this->initialization));
        $this->assertSame($this->initialization, $instance);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitializationStatus
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::__construct
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isPending
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getStatus
     */
    public function testGetInitializationStatus(): void
    {
        $this->manager->registerInitialization($this->initialization);
        $status = $this->manager->getInitializationStatus(get_class($this->initialization));
        $this->assertInstanceOf(InitializationStatus::class, $status);
    }
} 