<?php

namespace Mcp\Service;

class ServiceActuator
{
    public function invoke($service, $method, array $params = [])
    {
        $this->validateParams($service, $method, $params);
        if (!is_object($service)) {
            throw new \InvalidArgumentException('Service must be an object');
        }
        if (!method_exists($service, $method) || !is_callable([$service, $method])) {
            throw new \BadMethodCallException("Method {$method} does not exist or is not callable on service");
        }
        return call_user_func_array([$service, $method], $params);
    }

    public function validateParams($service, $method, array $params = [])
    {
        if (!is_object($service)) {
            throw new \InvalidArgumentException('Service must be an object');
        }
        if (!method_exists($service, $method)) {
            throw new \BadMethodCallException("Method {$method} does not exist on service");
        }
        $ref = new \ReflectionMethod($service, $method);
        $required = 0;
        foreach ($ref->getParameters() as $param) {
            if (!$param->isOptional() && !$param->isVariadic()) {
                $required++;
            }
        }
        if (count($params) < $required) {
            throw new \InvalidArgumentException("Not enough parameters for {$method}: required {$required}, given " . count($params));
        }
        return true;
    }

    protected function handleError($service, $method, $params, \Throwable $e)
    {
        // TODO: Implement error handling and reporting
    }
} 