<?php

namespace LegalStudy\ModularInitialization\Initializers;

use LegalStudy\ModularInitialization\AbstractInitialization;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class NetworkInitialization extends AbstractInitialization
{
    private int $maxRetries = 3;
    private int $timeout = 30;

    protected function doValidateConfiguration(): void
    {
        $requiredKeys = ['host', 'port', 'protocol'];
        foreach ($requiredKeys as $key) {
            if (!isset($this->config[$key])) {
                $this->addError("Missing required configuration key: {$key}");
            }
        }

        if (isset($this->config['port']) && (!is_numeric($this->config['port']) || $this->config['port'] <= 0)) {
            $this->addError("Invalid port value");
        }

        if (isset($this->config['timeout']) && (!is_numeric($this->config['timeout']) || $this->config['timeout'] <= 0)) {
            $this->addError("Invalid timeout value");
        }

        if (isset($this->config['max_retries']) && (!is_numeric($this->config['max_retries']) || $this->config['max_retries'] < 0)) {
            $this->addError("Invalid max_retries value");
        }

        if (isset($this->config['protocol']) && !in_array($this->config['protocol'], ['tcp', 'udp'])) {
            $this->addError("Invalid protocol. Must be 'tcp' or 'udp'");
        }
    }

    protected function doTestConnection(): bool
    {
        try {
            $host = $this->config['host'];
            $port = $this->config['port'];
            $protocol = $this->config['protocol'];
            
            $socket = @fsockopen(
                $protocol . '://' . $host,
                $port,
                $errno,
                $errstr,
                $this->timeout
            );
            
            if ($socket === false) {
                throw new \RuntimeException("Connection failed: {$errstr} ({$errno})");
            }
            
            fclose($socket);
            return true;
        } catch (\Exception $e) {
            $this->addError("Connection test failed: " . $e->getMessage());
            return false;
        }
    }

    protected function doPerformInitialization(): void
    {
        try {
            // Test network connectivity
            if (!$this->doTestConnection()) {
                throw new \RuntimeException("Network initialization failed: Connection test failed");
            }
            
            // Test DNS resolution
            $host = $this->config['host'];
            if (!gethostbyname($host)) {
                throw new \RuntimeException("DNS resolution failed for host: {$host}");
            }
            
            // Test protocol-specific functionality
            $protocol = $this->config['protocol'];
            if ($protocol === 'tcp') {
                $this->testTcpFunctionality();
            } else {
                $this->testUdpFunctionality();
            }
        } catch (\Exception $e) {
            $this->addError("Initialization failed: " . $e->getMessage());
            throw $e;
        }
    }

    private function testTcpFunctionality(): void
    {
        $host = $this->config['host'];
        $port = $this->config['port'];
        
        $socket = @fsockopen('tcp://' . $host, $port, $errno, $errstr, $this->timeout);
        if ($socket === false) {
            throw new \RuntimeException("TCP connection failed: {$errstr} ({$errno})");
        }
        
        // Test write
        $testData = "TEST\n";
        if (fwrite($socket, $testData) === false) {
            fclose($socket);
            throw new \RuntimeException("TCP write failed");
        }
        
        // Test read
        $response = fread($socket, 1024);
        if ($response === false) {
            fclose($socket);
            throw new \RuntimeException("TCP read failed");
        }
        
        fclose($socket);
    }

    private function testUdpFunctionality(): void
    {
        $host = $this->config['host'];
        $port = $this->config['port'];
        
        $socket = @fsockopen('udp://' . $host, $port, $errno, $errstr, $this->timeout);
        if ($socket === false) {
            throw new \RuntimeException("UDP connection failed: {$errstr} ({$errno})");
        }
        
        // Test write
        $testData = "TEST\n";
        if (fwrite($socket, $testData) === false) {
            fclose($socket);
            throw new \RuntimeException("UDP write failed");
        }
        
        fclose($socket);
    }

    public function getHost(): string
    {
        return $this->config['host'];
    }

    public function getPort(): int
    {
        return $this->config['port'];
    }

    public function getProtocol(): string
    {
        return $this->config['protocol'];
    }
} 