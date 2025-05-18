<?php

namespace Tests\Mcp\Service;

use Mcp\Service\ServiceActuator;
use PHPUnit\Framework\TestCase;
use Mockery;

class ServiceActuatorTest extends TestCase
{
    private ServiceActuator $actuator;
    private $mockService;

    protected function setUp(): void
    {
        parent::setUp();
        $this->actuator = new ServiceActuator();
        $this->mockService = new class {
            public function testMethod($a, $b) { return $a + $b; }
            public function throws() { throw new \RuntimeException('fail'); }
        };
    }

    public function testInvokeSuccess()
    {
        $result = $this->actuator->invoke($this->mockService, 'testMethod', [2, 3]);
        $this->assertEquals(5, $result);
    }

    public function testInvokeMethodNotFound()
    {
        $this->expectException(\BadMethodCallException::class);
        $this->actuator->invoke($this->mockService, 'nonExistentMethod', []);
    }

    public function testInvokeWithInvalidParams()
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->actuator->invoke($this->mockService, 'testMethod', [1]); // missing one param
    }

    public function testInvokeThrowsException()
    {
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('fail');
        $this->actuator->invoke($this->mockService, 'throws', []);
    }

    public function testValidateParamsSuccess()
    {
        $result = $this->actuator->validateParams($this->mockService, 'testMethod', [1, 2]);
        $this->assertTrue($result);
    }

    public function testValidateParamsFailure()
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->actuator->validateParams($this->mockService, 'testMethod', [1]); // missing one param
    }
} 