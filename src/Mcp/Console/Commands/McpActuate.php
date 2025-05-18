<?php

namespace Mcp\Console\Commands;

use Illuminate\Console\Command;
use Mcp\Service\ServiceActuator;

class McpActuate extends Command
{
    protected $signature = 'mcp:actuate
        {service : The fully qualified service class name}
        {method : The method to invoke}
        {params?* : Parameters as JSON or key=value pairs}
        {--json : Output result as JSON}';

    protected $description = 'Actuate (invoke) a service method via MCP';

    protected ServiceActuator $actuator;

    public function __construct(ServiceActuator $actuator)
    {
        parent::__construct();
        $this->actuator = $actuator;
    }

    public function handle(): int
    {
        $serviceClass = $this->argument('service');
        $method = $this->argument('method');
        $paramsInput = $this->argument('params');
        $params = $this->parseParams($paramsInput);

        try {
            if (!class_exists($serviceClass)) {
                $this->error("Service class {$serviceClass} does not exist.");
                return 1;
            }
            $service = app($serviceClass);
            $result = $this->actuator->invoke($service, $method, $params);
            if ($this->option('json')) {
                $this->line(json_encode(['result' => $result], JSON_PRETTY_PRINT));
            } else {
                $this->info('Invocation result:');
                $this->line(var_export($result, true));
            }
            return 0;
        } catch (\Throwable $e) {
            $this->error('Invocation failed: ' . $e->getMessage());
            return 1;
        }
    }

    protected function parseParams(array $paramsInput): array
    {
        if (count($paramsInput) === 1 && $this->isJson($paramsInput[0])) {
            return json_decode($paramsInput[0], true) ?? [];
        }
        $params = [];
        foreach ($paramsInput as $item) {
            if (strpos($item, '=') !== false) {
                [$key, $value] = explode('=', $item, 2);
                $params[] = $this->castValue($value);
            } else {
                $params[] = $this->castValue($item);
            }
        }
        return $params;
    }

    protected function isJson($string): bool
    {
        json_decode($string);
        return json_last_error() === JSON_ERROR_NONE;
    }

    protected function castValue($value)
    {
        if (is_numeric($value)) {
            return $value + 0;
        }
        if (strtolower($value) === 'true') return true;
        if (strtolower($value) === 'false') return false;
        if (strtolower($value) === 'null') return null;
        return $value;
    }
} 