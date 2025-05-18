<?php

namespace Tests\MCP\Agent;

use Psr\SimpleCache\CacheInterface;

class TestCache implements CacheInterface
{
    protected array $store = [];

    public function get($key, $default = null)
    {
        if (!isset($this->store[$key])) {
            return $default;
        }

        $item = $this->store[$key];
        if ($item['ttl'] !== null && $item['ttl'] < time()) {
            unset($this->store[$key]);
            return $default;
        }

        return $item['value'];
    }

    public function set($key, $value, $ttl = null)
    {
        $this->store[$key] = [
            'value' => $value,
            'ttl' => $ttl === null ? null : time() + $ttl
        ];
        return true;
    }

    public function delete($key)
    {
        if (isset($this->store[$key])) {
            unset($this->store[$key]);
            return true;
        }
        return false;
    }

    public function clear()
    {
        $this->store = [];
        return true;
    }

    public function getMultiple($keys, $default = null)
    {
        $result = [];
        foreach ($keys as $key) {
            $result[$key] = $this->get($key, $default);
        }
        return $result;
    }

    public function setMultiple($values, $ttl = null)
    {
        foreach ($values as $key => $value) {
            $this->set($key, $value, $ttl);
        }
        return true;
    }

    public function deleteMultiple($keys)
    {
        foreach ($keys as $key) {
            $this->delete($key);
        }
        return true;
    }

    public function has($key)
    {
        return $this->get($key) !== null;
    }
}
