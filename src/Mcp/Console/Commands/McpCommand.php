<?php

namespace App\Mcp\Console\Commands;

use App\Mcp\Server;
use Illuminate\Console\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

abstract class McpCommand extends Command
{
    protected $server;

    public function __construct(Server $server)
    {
        parent::__construct();
        $this->server = $server;
    }

    protected function initialize(InputInterface $input, OutputInterface $output)
    {
        parent::initialize($input, $output);

        if (!$this->server->isEnabled()) {
            $this->error('MCP server is not enabled. Please check your configuration.');
            exit(1);
        }
    }

    protected function formatOutput($data, $format = 'json')
    {
        switch ($format) {
            case 'json':
                return json_encode($data, JSON_PRETTY_PRINT);
            case 'table':
                if (!is_array($data)) {
                    return (string) $data;
                }
                return $this->formatTable($data);
            default:
                return (string) $data;
        }
    }

    protected function formatTable(array $data)
    {
        if (empty($data)) {
            return '';
        }

        if (!is_array(reset($data))) {
            return implode("\n", array_map(function ($key, $value) {
                return sprintf("%-30s %s", $key . ':', $value);
            }, array_keys($data), $data));
        }

        $headers = array_keys(reset($data));
        $rows = array_map(function ($row) use ($headers) {
            return array_map(function ($header) use ($row) {
                return $row[$header] ?? '';
            }, $headers);
        }, $data);

        return $this->table($headers, $rows);
    }

    protected function validateInput(array $rules)
    {
        $validator = validator($this->arguments() + $this->options(), $rules);

        if ($validator->fails()) {
            foreach ($validator->errors()->all() as $error) {
                $this->error($error);
            }
            exit(1);
        }

        return $validator->validated();
    }

    protected function confirmAction($message = 'Do you want to proceed?')
    {
        if (!$this->option('force') && !$this->confirm($message)) {
            $this->info('Operation cancelled.');
            exit(0);
        }
    }

    protected function handleException(\Exception $e)
    {
        $this->error('Error: ' . $e->getMessage());
        
        if ($this->option('verbose')) {
            $this->line($e->getTraceAsString());
        }
        
        exit(1);
    }
} 