$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
docker compose up -d minio lakekeeper trino
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed' }
python scripts/setup.py
if ($LASTEXITCODE -ne 0) { throw 'Catalog setup failed' }
python scripts/run.py
if ($LASTEXITCODE -ne 0) { throw 'Pipeline or checks failed' }
if (-not (Test-Path 'scripts/trino-jdbc-476.jar')) {
    Invoke-WebRequest 'https://repo.maven.apache.org/maven2/io/trino/trino-jdbc/476/trino-jdbc-476.jar' -OutFile 'scripts/trino-jdbc-476.jar'
}
docker compose --profile tools run --rm spark 2>&1 | Tee-Object -FilePath results/spark_console.txt
if ($LASTEXITCODE -ne 0) { throw 'Spark demonstration failed' }
docker compose ps | Out-File -Encoding utf8 results/services.txt
docker images --digests | Out-File -Encoding utf8 results/images.txt
python scripts/make_report.py
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed' }
