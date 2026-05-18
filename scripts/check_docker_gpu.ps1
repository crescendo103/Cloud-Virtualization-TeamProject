$ErrorActionPreference = "Stop"

Write-Host "Docker version"
docker --version

Write-Host ""
Write-Host "Docker engine"
docker info --format "{{.ServerVersion}}"

Write-Host ""
Write-Host "Host GPU"
nvidia-smi

Write-Host ""
Write-Host "Container GPU"
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi

