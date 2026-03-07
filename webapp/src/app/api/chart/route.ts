import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { data, prompt, sdk = 'python' } = body;

    if (!data || !prompt) {
      return NextResponse.json(
        { error: 'Missing data or prompt' },
        { status: 400 }
      );
    }

    const apiKey = process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY || '';

    if (!apiKey) {
      return NextResponse.json(
        { error: 'OPENROUTER_API_KEY not configured' },
        { status: 500 }
      );
    }

    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'redpill-'));
    const scriptPath = path.join(tempDir, 'script.py');

    const pythonScript = `
import sys
import json
import os
import traceback

try:
    from redpillx import Redpill
    from openai import OpenAI

    client = OpenAI(
        api_key="${apiKey}",
        base_url="https://openrouter.ai/api/v1"
    )

    def llm(messages, options=None):
        response = client.chat.completions.create(
            model="z-ai/glm-4.5-air:free",
            messages=messages,
            temperature=options.get("temperature", 0.7) if options else 0.7,
            max_tokens=options.get("max_tokens", 4000) if options else 4000,
        )
        return {"content": response.choices[0].message.content}

    rp = Redpill().llm(llm).build()

    data_json = json.loads('''${JSON.stringify(data).replace(/'/g, "\\'")}''')
    
    result = rp.generate_spec(data=data_json, prompt="${prompt.replace(/"/g, '\\"')}")
    
    chart_data = rp.execute(spec=result.spec, data=data_json)
    
    response = {
        "spec": result.spec.model_dump(),
        "chartData": chart_data.data,
        "metadata": chart_data.metadata
    }
    
    print(json.dumps(response))
    
except Exception as e:
    print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))
    sys.exit(1)
`;

    fs.writeFileSync(scriptPath, pythonScript);

    const rootDir = process.env.REDPILL_ROOT || 'C:\\Users\\shant\\Videos\\redpill';
    const redpillSrcPath = path.join(rootDir, 'packages/python/redpillx/src');
    const venvPython = path.join(rootDir, 'packages/python/redpillx/venv/Scripts/python.exe');
    let pythonPath = venvPython;

    if (!fs.existsSync(venvPython)) {
      const pyPython = 'py';
      if (fs.existsSync(path.join(rootDir, 'packages/python/redpillx'))) {
        pythonPath = pyPython;
      } else {
        pythonPath = pyPython;
      }
    }

    return new Promise((resolve) => {
      const python = spawn(pythonPath, ['-3.12', scriptPath], {
        env: {
          ...process.env,
          OPENAI_API_KEY: apiKey,
          PYTHONPATH: redpillSrcPath
        }
      });

      let output = '';
      let error = '';

      python.stdout.on('data', (chunk) => {
        output += chunk.toString();
      });

      python.stderr.on('data', (chunk) => {
        error += chunk.toString();
      });

      python.on('close', (code) => {
        try {
          fs.unlinkSync(scriptPath);
          fs.rmdirSync(tempDir);
        } catch (cleanupError) {
          console.error('Cleanup error:', cleanupError);
        }

        if (code !== 0) {
          resolve(NextResponse.json(
            { error: error || 'Python script failed', stderr: error, output: output },
            { status: 500 }
          ));
        } else {
          try {
            const result = JSON.parse(output);
            if (result.error) {
              resolve(NextResponse.json(
                { error: result.error, traceback: result.traceback },
                { status: 500 }
              ));
            } else {
              resolve(NextResponse.json(result));
            }
          } catch (parseError) {
            resolve(NextResponse.json(
              {
                error: 'Failed to parse output',
                details: output,
                stderr: error
              },
              { status: 500 }
            ));
          }
        }
      });
    });
  } catch (error) {
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    );
  }
}
