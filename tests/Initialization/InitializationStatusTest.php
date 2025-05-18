<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Services\InitializationStatus;
use PHPUnit\Framework\TestCase;

class InitializationStatusTest extends TestCase
{
    private InitializationStatus $status;

    protected function setUp(): void
    {
        $this->status = new InitializationStatus();
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::__construct
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     * @covers \LegalStudy\Initialization\InitializationStatus::getData
     * @covers \LegalStudy\Initialization\InitializationStatus::getErrors
     * @covers \LegalStudy\Initialization\InitializationStatus::getWarnings
     */
    public function testInitialState(): void
    {
        $status = new InitializationStatus();
        $this->assertTrue($status->isPending());
        $this->assertEmpty($status->getData());
        $this->assertEmpty($status->getErrors());
        $this->assertEmpty($status->getWarnings());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::setStatus
     */
    public function testSetStatus(): void
    {
        $this->status->setStatus(InitializationStatus::INITIALIZING);
        $this->assertEquals(InitializationStatus::INITIALIZING, $this->status->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::addData
     */
    public function testAddData(): void
    {
        $this->status->addData('key', 'value');
        $this->assertEquals(['key' => 'value'], $this->status->getData());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::setData
     */
    public function testSetData(): void
    {
        $data = ['key' => 'value'];
        $this->status->setData($data);
        $this->assertEquals($data, $this->status->getData());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::addError
     */
    public function testAddError(): void
    {
        $this->status->addError('Test error');
        $this->assertEquals(['Test error'], $this->status->getErrors());
        $this->assertEquals(InitializationStatus::ERROR, $this->status->getStatus());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::setErrors
     */
    public function testSetErrors(): void
    {
        $errors = ['Error 1', 'Error 2'];
        $this->status->setErrors($errors);
        $this->assertEquals($errors, $this->status->getErrors());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::addWarning
     */
    public function testAddWarning(): void
    {
        $this->status->addWarning('Test warning');
        $this->assertEquals(['Test warning'], $this->status->getWarnings());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::isSuccess
     */
    public function testSuccessStates(): void
    {
        $this->status->setStatus(InitializationStatus::COMPLETE);
        $this->assertTrue($this->status->isSuccess());

        $this->status->setStatus(InitializationStatus::INITIALIZED);
        $this->assertTrue($this->status->isSuccess());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::isError
     * @covers \LegalStudy\Initialization\InitializationStatus::isFailed
     */
    public function testFailureStates(): void
    {
        $this->status->setStatus(InitializationStatus::ERROR);
        $this->assertTrue($this->status->isError());

        $this->status->setStatus(InitializationStatus::FAILED);
        $this->assertTrue($this->status->isFailed());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::isPending
     * @covers \LegalStudy\Initialization\InitializationStatus::isInitializing
     * @covers \LegalStudy\Initialization\InitializationStatus::isIncomplete
     * @covers \LegalStudy\Initialization\InitializationStatus::isUnknown
     */
    public function testOtherStates(): void
    {
        $this->status->setStatus(InitializationStatus::PENDING);
        $this->assertTrue($this->status->isPending());

        $this->status->setStatus(InitializationStatus::INITIALIZING);
        $this->assertTrue($this->status->isInitializing());

        $this->status->setStatus(InitializationStatus::INCOMPLETE);
        $this->assertTrue($this->status->isIncomplete());

        $this->status->setStatus(InitializationStatus::UNKNOWN);
        $this->assertTrue($this->status->isUnknown());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::getDuration
     */
    public function testDuration(): void
    {
        $this->status->startTiming();
        usleep(1000); // Sleep for 1ms
        $this->status->endTiming();
        $this->assertGreaterThan(0, $this->status->getDuration());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::markComplete
     */
    public function testMarkComplete(): void
    {
        $this->status->startTiming();
        $this->status->markComplete();
        $this->assertEquals(InitializationStatus::COMPLETE, $this->status->getStatus());
        $this->assertGreaterThan(0, $this->status->getDuration());
    }

    /**
     * @covers \LegalStudy\Initialization\InitializationStatus::toArray
     */
    public function testToArray(): void
    {
        $this->status->addData('key', 'value');
        $this->status->addError('error');
        $this->status->addWarning('warning');
        $this->status->startTiming();
        $this->status->endTiming();

        $expected = [
            'status' => InitializationStatus::PENDING,
            'data' => ['key' => 'value'],
            'errors' => ['error'],
            'warnings' => ['warning'],
            'duration' => $this->status->getDuration(),
            'hasErrors' => true,
            'hasWarnings' => true
        ];

        $this->assertEquals($expected, $this->status->toArray());
    }
} 