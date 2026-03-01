import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { data, spec } = body;

    if (!data || !spec) {
      return NextResponse.json(
        { error: 'Missing data or spec' },
        { status: 400 }
      );
    }

    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'redpill-'));
    const scriptPath = path.join(tempDir, 'script.py');

    const pythonScript = `
import sys
import json
import os
from redpill.spec.schema import ChartSpec
from redpill.executor.polars_executor import PolarsExecutor

executor = PolarsExecutor()

try:
    data_json = json.loads('''${JSON.stringify(data).replace(/'/g, "\\'")}''')
    
    chart_spec = ChartSpec(**json.loads('''${JSON.stringify(spec).replace(/'/g, "\\'")}'''))
    
    result = executor.execute(spec=chart_spec, data=data_json)
    
    response = {
        "chartData": result.data,
        "metadata": result.metadata
    }
    
    print(json.dumps(response))
    
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
`;

    fs.writeFileSync(scriptPath, pythonScript);

    const rootDir = process.env.REDPILL_ROOT || 'C:\\Users\\shant\\Videos\\redpill';
    const redpillSrcPath = path.join(rootDir, 'packages/python/redpill/src');
    const venvPython = path.join(rootDir, 'packages/python/redpill/venv/Scripts/python.exe');

    return new Promise((resolve) => {
      const python = spawn(venvPython, [scriptPath], {
        env: {
          ...process.env,
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
            { error: error || 'Python script failed', stderr: error },
            { status: 500 }
          ));
        } else {
          try {
            const result = JSON.parse(output);
            if (result.error) {
              resolve(NextResponse.json(
                { error: result.error },
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
