<?php

namespace Tests\Initialization;

use LegalStudy\ModularInitialization\Initializers\ExternalApiInitialization;
use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Psr7\Response;
use GuzzleHttp\Exception\RequestException;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;

/**
 * @covers \LegalStudy\Initialization\ExternalApiInitialization
 * @covers \LegalStudy\Initialization\AbstractInitialization
 * @covers \LegalStudy\Initialization\InitializationStatus
 * @covers \LegalStudy\Initialization\InitializationPerformanceMonitor
 */
class ExternalApiInitializationTest extends TestCase
{
    private ExternalApiInitialization $initialization;
    private MockHandler $mockHandler;
    private HandlerStack $handlerStack;

    protected function setUp(): void
    {
        $this->mockHandler = new MockHandler();
        $this->handlerStack = HandlerStack::create($this->mockHandler);
        
        $this->initialization = $this->getMockBuilder(ExternalApiInitialization::class)
            ->onlyMethods(['createClient'])
            ->getMock();
    }

    public function testValidateConfiguration(): void
    {
        $config = [
            'base_url' => 'https://api.example.com',
            'timeout' => 30,
            'headers' => ['Authorization' => 'Bearer test_token']
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->getStatus()->isPending());
    }

    public function testTestConnection(): void
    {
        $this->mockHandler->append(new Response(200));
        
        $client = new Client(['handler' => $this->handlerStack]);
        
        $this->initialization->expects($this->once())
            ->method('createClient')
            ->willReturn($client);

        $config = [
            'base_url' => 'https://api.example.com',
            'timeout' => 30,
            'headers' => ['Authorization' => 'Bearer test_token']
        ];

        $this->initialization->validateConfiguration($config);
        $this->assertTrue($this->initialization->testConnection());
    }

    public function testPerformInitialization(): void
    {
        $this->mockHandler->append(new Response(200));
        
        $client = new Client(['handler' => $this->handlerStack]);
        
        $this->initialization->expects($this->once())
            ->method('createClient')
            ->willReturn($client);

        $config = [
            'base_url' => 'https://api.example.com',
            'timeout' => 30,
            'headers' => ['Authorization' => 'Bearer test_token']
        ];

        $this->initialization->validateConfiguration($config);
        $this->initialization->performInitialization();

        $this->assertTrue($this->initialization->getStatus()->isInitialized());
        $this->assertEquals(['connected' => true, 'status_code' => 200], $this->initialization->getStatus()->getData());
    }

    public function testErrorHandling(): void
    {
        $request = new Request('GET', 'https://api.example.com/');
        $this->mockHandler->append(new RequestException('Connection failed', $request));
        
        $client = new Client(['handler' => $this->handlerStack]);
        
        $this->initialization->expects($this->once())
            ->method('createClient')
            ->willReturn($client);

        $config = [
            'base_url' => 'https://api.example.com',
            'timeout' => 30,
            'headers' => ['Authorization' => 'Bearer test_token']
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
} 