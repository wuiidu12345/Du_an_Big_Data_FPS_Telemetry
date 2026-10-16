@echo off
chcp 65001 >nul
title Tien ich chay Pipeline Apache Spark - Du an Big Data FPS
cls
@echo off

echo ==================================================================================================================
echo THUC THI DUONG ONG XU LY DU LIEU LON APACHE SPARK (SPARK SQL ^& SPARK MLLIB)
echo ==================================================================================================================
echo.
echo [-] Dang kiem tra trang thai Container 'bigdata-fps-engine'...
docker ps -q --filter "name=bigdata-fps-engine" --filter "status=running" | findstr /r "." >nul 2>&1
if errorlevel 1 (
    echo [INFO] Container chua bat, dang tu dong khoi dong container...
    docker compose up -d
    echo.
)

echo [OK] Container dang hoat dong.
echo.
echo [-] Dang giao viec thuc thi Pipeline xu ly du lieu lon cho Apache Spark...
echo.

docker exec -it bigdata-fps-engine python scripts/spark_batch_pipeline.py

echo.
echo ==================================================================================================================
echo [OK] DA HOAN TAT TOAN BO TIEN TRINH PHAN TICH PHAN TAN TREN APACHE SPARK!
echo ==================================================================================================================
pause
