Write-Host "Starting full stack..." -ForegroundColor Green

Write-Host "Starting Dev API..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"`$env:AWS_PROFILE='AdministratorAccess-520477993393'; cd apps/api; uv run uvicorn app.main:app --reload --reload-dir . --reload-dir ../../packages --port 8000`""

Write-Host "Starting Dev Web..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd apps/web; pnpm run dev`""
