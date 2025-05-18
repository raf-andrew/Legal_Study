<?php

namespace LegalStudy\Tests\Initialization;

use LegalStudy\Initialization\InitializationErrorDetector;
use PHPUnit\Framework\TestCase;
use RuntimeException;

class InitializationErrorDetectorTest extends TestCase
{
    private InitializationErrorDetector $detector;

    protected function setUp(): void
    {
        $this->detector = new InitializationErrorDetector();
    }

    public function testRegisterErrorPattern(): void
    {
        $pattern = '/test error/i';
        $handler = function($error) { return 'TEST_ERROR'; };
        
        $this->detector->registerErrorPattern($pattern, $handler);
        
        $error = new RuntimeException('This is a test error');
        $this->detector->detectError('test', $error);
        
        $lastError = $this->detector->getLastError();
        $this->assertEquals('TEST_ERROR', $lastError['type']);
    }

    public function testRegisterErrorHandler(): void
    {
        $errorType = 'TEST_ERROR';
        $handlerCalled = false;
        $handler = function($error) use (&$handlerCalled) {
            $handlerCalled = true;
        };
        
        $this->detector->registerErrorHandler($errorType, $handler);
        
        // Create a custom exception class that can hold the error type
        $error = new class('Test error') extends RuntimeException {
            private string $errorType = 'TEST_ERROR';
            public function getErrorType(): string {
                return $this->errorType;
            }
        };
        
        $this->detector->detectError('test', $error);
        
        $this->assertTrue($handlerCalled);
    }

    public function testDetectError(): void
    {
        $error = new RuntimeException('Test error');
        $this->detector->detectError('test', $error);
        
        $lastError = $this->detector->getLastError();
        $this->assertEquals('test', $lastError['component']);
        $this->assertEquals(RuntimeException::class, $lastError['type']);
        $this->assertEquals('Test error', $lastError['message']);
    }

    public function testGetErrorHistory(): void
    {
        $error1 = new RuntimeException('Error 1');
        $error2 = new RuntimeException('Error 2');
        
        $this->detector->detectError('test1', $error1);
        $this->detector->detectError('test2', $error2);
        
        $history = $this->detector->getErrorHistory();
        $this->assertCount(2, $history);
        $this->assertEquals('Error 1', $history[0]['message']);
        $this->assertEquals('Error 2', $history[1]['message']);
    }

    public function testGetErrorHistoryForComponent(): void
    {
        $error1 = new RuntimeException('Error 1');
        $error2 = new RuntimeException('Error 2');
        
        $this->detector->detectError('test1', $error1);
        $this->detector->detectError('test1', $error2);
        $this->detector->detectError('test2', new RuntimeException('Error 3'));
        
        $history = $this->detector->getErrorHistoryForComponent('test1');
        $this->assertCount(2, $history);
        $this->assertEquals('Error 1', $history[0]['message']);
        $this->assertEquals('Error 2', $history[1]['message']);
    }

    public function testGetErrorCount(): void
    {
        $this->assertEquals(0, $this->detector->getErrorCount());
        
        $this->detector->detectError('test', new RuntimeException('Error 1'));
        $this->assertEquals(1, $this->detector->getErrorCount());
        
        $this->detector->detectError('test', new RuntimeException('Error 2'));
        $this->assertEquals(2, $this->detector->getErrorCount());
    }

    public function testGetErrorCountForComponent(): void
    {
        $this->assertEquals(0, $this->detector->getErrorCountForComponent('test'));
        
        $this->detector->detectError('test', new RuntimeException('Error 1'));
        $this->assertEquals(1, $this->detector->getErrorCountForComponent('test'));
        
        $this->detector->detectError('other', new RuntimeException('Error 2'));
        $this->assertEquals(1, $this->detector->getErrorCountForComponent('test'));
    }

    public function testClearErrorHistory(): void
    {
        $this->detector->detectError('test', new RuntimeException('Error 1'));
        $this->detector->detectError('test', new RuntimeException('Error 2'));
        
        $this->detector->clearErrorHistory();
        
        $this->assertEquals(0, $this->detector->getErrorCount());
        $this->assertEmpty($this->detector->getErrorHistory());
    }

    public function testHasErrors(): void
    {
        $this->assertFalse($this->detector->hasErrors());
        
        $this->detector->detectError('test', new RuntimeException('Error'));
        $this->assertTrue($this->detector->hasErrors());
        
        $this->detector->clearErrorHistory();
        $this->assertFalse($this->detector->hasErrors());
    }

    public function testHasErrorsForComponent(): void
    {
        $this->assertFalse($this->detector->hasErrorsForComponent('test'));
        
        $this->detector->detectError('test', new RuntimeException('Error'));
        $this->assertTrue($this->detector->hasErrorsForComponent('test'));
        
        $this->detector->clearErrorHistory();
        $this->assertFalse($this->detector->hasErrorsForComponent('test'));
    }

    public function testGetLastError(): void
    {
        $this->assertNull($this->detector->getLastError());
        
        $error1 = new RuntimeException('Error 1');
        $error2 = new RuntimeException('Error 2');
        
        $this->detector->detectError('test', $error1);
        $this->detector->detectError('test', $error2);
        
        $lastError = $this->detector->getLastError();
        $this->assertEquals('Error 2', $lastError['message']);
    }

    public function testGetLastErrorForComponent(): void
    {
        $this->assertNull($this->detector->getLastErrorForComponent('test'));
        
        $error1 = new RuntimeException('Error 1');
        $error2 = new RuntimeException('Error 2');
        
        $this->detector->detectError('test', $error1);
        $this->detector->detectError('other', new RuntimeException('Other Error'));
        $this->detector->detectError('test', $error2);
        
        $lastError = $this->detector->getLastErrorForComponent('test');
        $this->assertEquals('Error 2', $lastError['message']);
    }
} 