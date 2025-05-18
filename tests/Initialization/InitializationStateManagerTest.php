<?php

namespace Tests\Initialization;

use Tests\TestCase;
use LegalStudy\ModularInitialization\Services\InitializationStateManager;
use LegalStudy\ModularInitialization\Services\InitializationStatus;
use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Exceptions\CircularDependencyException;
use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\ModularInitializationServiceProvider;
use PHPUnit\Framework\MockObject\MockObject;
use LegalStudy\ModularInitialization\Tests\Initialization\TestInitialization;

/**
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager
 * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus
 * @covers \LegalStudy\ModularInitialization\AbstractInitialization
 * @covers \LegalStudy\ModularInitialization\ModularInitializationServiceProvider
 * @covers \LegalStudy\ModularInitialization\Exceptions\CircularDependencyException
 */
class InitializationStateManagerTest extends TestCase
{
    protected InitializationStateManager $manager;
    protected InitializationStatus $status;
    protected FileSystemInitialization $filesystem;
    protected CacheInitialization $cache;
    protected $cacheMock;
    protected TestInitialization $first;
    protected TestInitialization $second;

    protected function setUp(): void
    {
        parent::setUp();
        
        $this->status = new InitializationStatus();
        $this->manager = new InitializationStateManager($this->status);
        $this->filesystem = new FileSystemInitialization($this->status);
        
        // Mock the cache functionality
        $this->cacheMock = $this->getMockBuilder(CacheInitialization::class)
            ->setConstructorArgs([$this->status])
            ->onlyMethods(['doTestConnection', 'doValidateConfiguration', 'doPerformInitialization'])
            ->getMock();
        
        $this->cacheMock->method('doTestConnection')
            ->willReturn(true);
            
        $this->cacheMock->method('doValidateConfiguration')
            ->willReturn(true);
            
        $this->cacheMock->method('doPerformInitialization')
            ->will($this->returnCallback(function() {
                $this->status->setInitialized(true);
            }));
            
        $this->cache = $this->cacheMock;

        $this->first = new TestInitialization($this->status);
        $this->second = new TestInitialization($this->status);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::registerInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::hasInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::__construct
     */
    public function test_register_initialization_with_dependencies()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);
        $this->manager->registerInitialization('cache', $this->cache, ['filesystem']);

        $this->assertTrue($this->manager->hasInitialization('filesystem'));
        $this->assertTrue($this->manager->hasInitialization('cache'));
        $this->assertEquals(['filesystem'], $this->manager->getDependencies('cache'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::isInitializationComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::setInitialized
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isInitialized
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::markComplete
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isComplete
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_is_initialization_complete()
    {
        $this->manager->registerInitialization('first', $this->first);
        $this->manager->registerInitialization('second', $this->second, ['first']);

        $this->assertFalse($this->manager->isInitializationComplete('second'));
        $this->assertFalse($this->manager->isInitializationComplete('first'));

        // Initialize first
        $this->manager->initialize('first');
        $this->assertTrue($this->manager->isInitializationComplete('first'));
        $this->assertFalse($this->manager->isInitializationComplete('second'));

        // Initialize second
        $this->manager->initialize('second');
        $this->assertTrue($this->manager->isInitializationComplete('second'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_circular_dependency_detection()
    {
        $filesystem = new FileSystemInitialization($this->status, [
            'base_path' => storage_path('app'),
            'permissions' => 0755,
            'required_dirs' => ['cache', 'logs', 'uploads'],
        ]);

        $cache = new CacheInitialization($this->status, [
            'driver' => 'file',
        ]);

        $this->manager->registerInitialization('filesystem', $filesystem);
        $this->manager->registerInitialization('cache', $cache);

        // Create a circular dependency
        $this->manager->addDependency('filesystem', 'cache');
        
        try {
            $this->manager->addDependency('cache', 'filesystem');
            $this->fail('Expected CircularDependencyException was not thrown');
        } catch (CircularDependencyException $e) {
            $this->assertInstanceOf(CircularDependencyException::class, $e);
            $this->assertContains('cache', $e->getDependencyChain());
            $this->assertContains('filesystem', $e->getDependencyChain());
        }
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getDependencies
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_get_dependencies_for_initialization_without_dependencies()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);

        $this->assertEquals([], $this->manager->getDependencies('filesystem'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::hasDependencies
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_has_dependencies()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);
        $this->manager->registerInitialization('cache', $this->cache, ['filesystem']);

        $this->assertFalse($this->manager->hasDependencies('filesystem'));
        $this->assertTrue($this->manager->hasDependencies('cache'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitialization
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addDependency
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_get_initialization()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);

        $this->assertSame($this->filesystem, $this->manager->getInitialization('filesystem'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getStatus
     * @covers \LegalStudy\ModularInitialization\ModularInitializationServiceProvider::register
     */
    public function test_get_initialization_status()
    {
        $this->assertSame($this->status, $this->manager->getStatus());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addError
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isFailed
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getErrors
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_initialization_status_error_handling()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);

        $this->status->addError('Test error');
        $this->assertTrue($this->status->isFailed());
        $this->assertEquals(['Test error'], $this->status->getErrors());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::addData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getData
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getAllData
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_initialization_status_data_handling()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);

        $this->status->addData('test_key', 'test_value');
        $this->assertEquals('test_value', $this->status->getData('test_key'));
        $this->assertEquals(['test_key' => 'test_value'], $this->status->getAllData());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::reset
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isInitialized
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::isFailed
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getErrors
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStatus::getAllData
     * @covers \LegalStudy\ModularInitialization\AbstractInitialization::getStatus
     */
    public function test_initialization_status_reset()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);

        $this->status->setInitialized(true);
        $this->status->addError('Test error');
        $this->status->addData('test_key', 'test_value');

        $this->status->reset();

        $this->assertFalse($this->status->isInitialized());
        $this->assertFalse($this->status->isFailed());
        $this->assertEmpty($this->status->getErrors());
        $this->assertEmpty($this->status->getAllData());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::updateState
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getState
     */
    public function test_update_and_get_state()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);
        $newStatus = new InitializationStatus();
        $newStatus->setInitialized(true);
        
        $this->manager->updateState('filesystem', $newStatus);
        $state = $this->manager->getState('filesystem');
        
        $this->assertSame($this->filesystem, $state['instance']);
        $this->assertTrue($state['status']->isInitialized());
        
        $this->expectException(\RuntimeException::class);
        $this->manager->updateState('nonexistent', $newStatus);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::isAllComplete
     */
    public function test_is_all_complete()
    {
        $this->manager->registerInitialization('first', $this->first);
        $this->manager->registerInitialization('second', $this->second);
        
        $this->assertFalse($this->manager->isAllComplete());
        
        $firstStatus = $this->first->getStatus();
        $firstStatus->markComplete();
        $this->manager->updateState('first', $firstStatus);
        $this->assertFalse($this->manager->isAllComplete());
        
        $secondStatus = $this->second->getStatus();
        $secondStatus->markComplete();
        $this->manager->updateState('second', $secondStatus);
        $this->assertTrue($this->manager->isAllComplete());
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::getInitializationOrder
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::topologicalSort
     */
    public function test_get_initialization_order()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);
        $this->manager->registerInitialization('cache', $this->cache, ['filesystem']);
        $this->manager->registerInitialization('second', $this->second, ['cache']);
        
        $order = $this->manager->getInitializationOrder();
        
        $this->assertIsArray($order);
        $this->assertCount(3, $order);
        
        // Check that the order respects dependencies
        $filesystemIndex = array_search('filesystem', $order);
        $cacheIndex = array_search('cache', $order);
        $secondIndex = array_search('second', $order);
        
        $this->assertNotFalse($filesystemIndex);
        $this->assertNotFalse($cacheIndex);
        $this->assertNotFalse($secondIndex);
        
        // The order should be: filesystem -> cache -> second
        $this->assertLessThan($cacheIndex, $filesystemIndex);
        $this->assertLessThan($secondIndex, $cacheIndex);
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::reset
     */
    public function test_reset()
    {
        $this->manager->registerInitialization('first', $this->first);
        $this->manager->registerInitialization('second', $this->second, ['first']);
        
        $this->manager->initialize('first');
        $this->assertTrue($this->manager->isInitializationComplete('first'));
        
        $this->manager->reset();
        $this->assertFalse($this->manager->isInitializationComplete('first'));
    }

    /**
     * @covers \LegalStudy\ModularInitialization\Services\InitializationStateManager::resolveDependencies
     */
    public function test_resolve_dependencies()
    {
        $this->manager->registerInitialization('filesystem', $this->filesystem);
        $this->manager->registerInitialization('cache', $this->cache, ['filesystem']);
        $this->manager->registerInitialization('second', $this->second, ['cache']);
        
        $deps = $this->manager->getDependencies('second');
        $this->assertContains('cache', $deps);
        $this->assertContains('filesystem', $deps);
        
        $this->expectException(\InvalidArgumentException::class);
        $this->manager->getDependencies('nonexistent');
    }
} 