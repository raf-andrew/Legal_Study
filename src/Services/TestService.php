<?php

namespace App\Services;

use Illuminate\Contracts\Http\Kernel;

class TestService implements Kernel
{
    public function handle($request)
    {
        return response()->json(['status' => 'ok']);
    }

    public function bootstrap()
    {
        // Bootstrap logic
    }

    public function terminate($request, $response)
    {
        // Termination logic
    }
} 